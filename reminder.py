from google import genai
import json

client = genai.Client()

async def generate_reminder_letter(extracted_data: dict) -> str:
    """
    Generates a polite payment reminder letter based on the extracted invoice data.
    """
    prompt = f"""
    You are an assistant writing a payment reminder letter on behalf of a small business owner in India.
    
    Here is the invoice/bill data that is currently overdue or pending:
    {json.dumps(extracted_data, indent=2)}
    
    Draft a polite, professional payment reminder letter to the vendor/client. 
    Include the amount due, the vendor name, and the due date if available.
    Do not use placeholders like [Your Name]. Just end it with "Sincerely, VyaparAI Business Team".
    Keep it concise and professional.
    """
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Reminder generation error: {e}")
        return "Sorry, there was an error generating the reminder letter."
