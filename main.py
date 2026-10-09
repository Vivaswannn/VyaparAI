import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="VyaparAI API")

# Ensure frontend directory exists
os.makedirs("frontend", exist_ok=True)

# Mount the frontend directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# In-memory database for the hackathon session
# Structure: 
# {
#   "documents": [{"id": str, "filename": str, "extracted_data": dict, "embedding": list}],
#   "raw_texts": {"id": "raw text or summary"}
# }
db = {
    "documents": []
}

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

import uuid
from extract import process_document
from rag import generate_embedding, retrieve_relevant_documents, format_document_for_embedding
from action_plan import generate_action_plan
from reminder import generate_reminder_letter

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Step 1, 2 & 3: Handle file upload, trigger GPT-4o Vision extraction, and generate embeddings.
    """
    file_bytes = await file.read()
    
    # 1. Extract data using Vision API
    extracted_data = await process_document(file_bytes, file.filename)
    
    # 2. Generate Embedding
    doc_text = format_document_for_embedding(extracted_data)
    embedding = await generate_embedding(doc_text)
    
    # 3. Store in DB
    doc_id = str(uuid.uuid4())
    document_record = {
        "id": doc_id,
        "filename": file.filename,
        "extracted_data": extracted_data,
        "embedding": embedding 
    }
    db["documents"].append(document_record)
    
    return {
        "status": "success", 
        "filename": file.filename, 
        "id": doc_id,
        "extracted_data": extracted_data
    }

@app.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Step 4 & 5: Handle user query, retrieve relevant docs, and generate action plan.
    """
    if not db["documents"]:
        return {
            "summary": "No documents uploaded yet. Please upload some invoices or bills first.",
            "actions": [],
            "sources_used": []
        }

    # 1. Embed user query
    query_embedding = await generate_embedding(request.query)
    
    # 2. Perform cosine similarity against db["documents"]
    retrieved_docs = retrieve_relevant_documents(query_embedding, db["documents"], top_k=3)
    
    # 3. Pass retrieved docs + query to GPT-4o for Action Plan
    action_plan_result = await generate_action_plan(request.query, retrieved_docs)
    
    return action_plan_result

@app.post("/api/reminder")
async def generate_reminder(request: ReminderRequest):
    """
    Step 6 (Bonus): Generate a payment reminder letter for a specific document.
    """
    # Fetch document from DB
    doc = next((d for d in db["documents"] if d["id"] == request.document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    letter = await generate_reminder_letter(doc["extracted_data"])
    
    return {"letter": letter}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
