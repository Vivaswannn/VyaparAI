import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from database import init_db, insert_document, get_all_documents, get_document_by_id
from extract import process_document
from action_plan import generate_action_plan
from reminder import generate_reminder_letter

# Load environment variables
load_dotenv()

# Initialize the SQLite Database
init_db()

app = FastAPI(title="VyaparAI API")

# Ensure frontend directory exists
os.makedirs("frontend", exist_ok=True)

# Mount the frontend directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

class QueryRequest(BaseModel):
    query: str
    language: str = "english"

class ReminderRequest(BaseModel):
    document_id: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend HTML file."""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Frontend not found</h1><p>Please create frontend/index.html</p>"

import csv
from io import StringIO
from fastapi.responses import StreamingResponse

@app.get("/api/documents")
async def get_documents(x_user_id: str = Header('demo_user')):
    """Returns a list of all documents in the database."""
    docs = get_all_documents(x_user_id)
    # Return just the metadata for the UI list
    return [{"id": d["id"], "filename": d["filename"], "vendor": d["vendor_name"], "amount": d["amount"], "status": d["payment_status"]} for d in docs]

@app.get("/api/export")
async def export_ledger(user_id: str = 'demo_user'):
    """
    Export the entire SQLite database as a CSV file.
    """
    docs = get_all_documents(user_id)
    
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Filename", "Vendor Name", "Amount", "Due Date", "Tax Details", "Payment Status"])
    
    for doc in docs:
        writer.writerow([
            doc.get("filename", ""),
            doc.get("vendor_name", ""),
            doc.get("amount", ""),
            doc.get("due_date", ""),
            doc.get("tax_details", ""),
            doc.get("payment_status", "")
        ])
        
    stream.seek(0)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=vyapar_ledger.csv"
    return response

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), x_user_id: str = Header('demo_user')):
    """
    Handle file upload, trigger Gemini Vision extraction, and persist to SQLite.
    """
    file_bytes = await file.read()
    
    # Extract data using Vision API
    extracted_data = await process_document(file_bytes, file.filename)
    
    if "error" in extracted_data:
        return {
            "status": "error",
            "message": f"AI Extraction Failed: {extracted_data['error']}. Please try uploading again."
        }
    
    # Store in Persistent SQLite Database
    doc_id = insert_document(file.filename, extracted_data, x_user_id)
    
    return {
        "status": "success", 
        "filename": file.filename, 
        "id": doc_id,
        "extracted_data": extracted_data
    }

@app.post("/api/query")
async def query_documents(request: QueryRequest, x_user_id: str = Header('demo_user')):
    """
    Fetch all historical records from SQLite and let Groq do macro-analysis.
    """
    all_docs = get_all_documents(x_user_id)
    
    if not all_docs:
        return {
            "summary": "No documents found in the database. Please upload some bills or invoices first.",
            "actions": [],
            "sources_used": []
        }

    # Pass entire lightweight ledger + query to Groq
    action_plan_result = await generate_action_plan(request.query, all_docs, request.language)
    
    return action_plan_result

@app.post("/api/reminder")
async def generate_reminder(request: ReminderRequest):
    """
    Generate a payment reminder letter for a specific document.
    """
    # Fetch document from DB
    doc_data = get_document_by_id(request.document_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
        
    letter = await generate_reminder_letter(doc_data)
    
    return {"letter": letter}

@app.delete("/api/documents/{doc_id}")
async def delete_doc(doc_id: str, x_user_id: str = Header('demo_user')):
    from database import delete_document
    success = delete_document(doc_id, x_user_id)
    return {"status": "success" if success else "error"}

@app.patch("/api/documents/{doc_id}/complete")
async def complete_doc(doc_id: str, x_user_id: str = Header('demo_user')):
    from database import mark_document_complete
    success = mark_document_complete(doc_id, x_user_id)
    return {"status": "success" if success else "error"}

class ManualEntryRequest(BaseModel):
    vendor: str
    amount: float
    due_date: str

@app.post("/api/manual")
async def manual_upload(request: ManualEntryRequest, x_user_id: str = Header('demo_user')):
    extracted_data = {
        "vendor_name": request.vendor,
        "amount": request.amount,
        "due_date": request.due_date,
        "tax_details": "",
        "payment_status": "Pending"
    }
    doc_id = insert_document("Manual Entry", extracted_data, x_user_id)
    return {"status": "success", "id": doc_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
