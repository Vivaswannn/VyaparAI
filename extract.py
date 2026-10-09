import fitz  # PyMuPDF
import json
from groq import AsyncGroq

async def process_document(file_bytes: bytes, filename: str) -> dict:
    """
    Extracts raw text from the PDF using PyMuPDF and uses Groq to convert it to structured JSON.
    This completely bypasses the flaky Gemini Vision API!
    """
    client = AsyncGroq()
    
    # 1. Extract raw text locally
    raw_text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_document:
                raw_text += page.get_text() + "\n"
        else:
            return {"error": "For this robust MVP, please upload text-based PDFs only (not raw images)."}
            
    except Exception as e:
        return {"error": f"Failed to read PDF: {e}"}

    # 2. Use Groq to parse the raw text into structured JSON
    prompt = f"""
    Extract the following details from this raw invoice text:
    - vendor_name
    - amount (number only, float)
    - due_date (if mentioned, otherwise null)
    - tax_details (any GST or tax info, otherwise null)
    - payment_status (e.g., Paid, Due, Overdue, Unpaid, PENDING, otherwise null)
    
    RAW TEXT:
    {raw_text}
    
    Return ONLY valid JSON matching this schema exactly:
    {{
      "vendor_name": "string",
      "amount": 0.0,
      "due_date": "string or null",
      "tax_details": "string or null",
      "payment_status": "string or null"
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a precise data extraction bot. You only output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        result_json = response.choices[0].message.content
        extracted_data = json.loads(result_json)
        extracted_data['document_name'] = filename
        return extracted_data
    except Exception as e:
        print(f"Groq Extraction error: {e}")
        return {"error": str(e)}
