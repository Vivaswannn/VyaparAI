import sqlite3
import json
import uuid
from datetime import datetime

DB_NAME = "vyapar.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT,
                vendor_name TEXT,
                amount REAL,
                due_date TEXT,
                tax_details TEXT,
                payment_status TEXT,
                raw_json TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

def insert_document(filename: str, extracted_data: dict) -> str:
    doc_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    # Safely extract values in case Gemini returned nulls
    vendor = extracted_data.get("vendor_name") or "Unknown"
    
    amount_raw = extracted_data.get("amount")
    try:
        amount = float(amount_raw) if amount_raw is not None else 0.0
    except ValueError:
        amount = 0.0
        
    due_date = extracted_data.get("due_date") or ""
    tax = extracted_data.get("tax_details") or ""
    status = extracted_data.get("payment_status") or "Unknown"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (id, filename, vendor_name, amount, due_date, tax_details, payment_status, raw_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, filename, vendor, amount, due_date, tax, status, json.dumps(extracted_data), created_at))
        conn.commit()
    return doc_id

def get_all_documents() -> list[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        docs = []
        for row in rows:
            docs.append({
                "id": row["id"],
                "filename": row["filename"],
                "vendor_name": row["vendor_name"],
                "amount": row["amount"],
                "due_date": row["due_date"],
                "tax_details": row["tax_details"],
                "payment_status": row["payment_status"],
                "extracted_data": json.loads(row["raw_json"])
            })
        return docs
        
def get_document_by_id(doc_id: str) -> dict:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row["raw_json"])
    return None
