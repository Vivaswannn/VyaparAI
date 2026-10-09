import fitz  # PyMuPDF
from google import genai
from google.genai import types
import json

client = genai.Client() # Uses GEMINI_API_KEY from .env

async def process_document(file_bytes: bytes, filename: str) -> dict:
    """
    Converts a document to an image and extracts structured data using Gemini 3.8 Flash Vision.
    """
    img_bytes = file_bytes
    mime_type = "image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "image/png"
    
    if filename.lower().endswith('.pdf'):
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        page = pdf_document.load_page(0)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        mime_type = "image/png"
        
    prompt = """
    Extract the following details from this invoice/bill:
    - vendor_name
    - amount (number only, float)
    - due_date (if mentioned, otherwise null)
    - tax_details (any GST or tax info, otherwise null)
    - payment_status (e.g., Paid, Due, Overdue, Unpaid, otherwise null)
    """
    
    try:
        response = await client.aio.models.generate_content(
            model='gemini-3.8-flash',
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "vendor_name": {"type": "STRING"},
                        "amount": {"type": "NUMBER"},
                        "due_date": {"type": "STRING", "nullable": True},
                        "tax_details": {"type": "STRING", "nullable": True},
                        "payment_status": {"type": "STRING", "nullable": True}
                    },
                    "required": ["vendor_name", "amount"]
                }
            )
        )
        
        result_json = response.text
        extracted_data = json.loads(result_json)
        extracted_data['document_name'] = filename
        return extracted_data
    except Exception as e:
        print(f"Extraction error: {e}")
        return {
            "vendor_name": "Unknown",
            "amount": 0.0,
            "due_date": None,
            "tax_details": None,
            "payment_status": "Unknown",
            "document_name": filename,
            "error": str(e)
        }
