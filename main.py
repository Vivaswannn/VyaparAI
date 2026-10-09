import os
from fastapi import FastAPI, File, UploadFile, HTTPException
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

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Handle file upload, trigger Gemini Vision extraction, and persist to SQLite.
    """
    file_bytes = await file.read()
    
    # Extract data using Vision API
    extracted_data = await process_document(file_bytes, file.filename)
    
    # Store in Persistent SQLite Database
    doc_id = insert_document(file.filename, extracted_data)
    
    return {
        "status": "success", 
        "filename": file.filename, 
        "id": doc_id,
        "extracted_data": extracted_data
    }

@app.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Fetch all historical records from SQLite and let Groq do macro-analysis.
    """
    all_docs = get_all_documents()
    
    if not all_docs:
        return {
            "summary": "No documents found in the database. Please upload some bills or invoices first.",
            "actions": [],
            "sources_used": []
        }

    # Pass entire lightweight ledger + query to Groq
    action_plan_result = await generate_action_plan(request.query, all_docs)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
