import json
from groq import AsyncGroq

async def generate_reminder_letter(extracted_data: dict) -> str:
    """
    Generates a polite payment reminder letter based on the extracted invoice data.
    """
    client = AsyncGroq()
    
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
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a professional business assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Reminder generation error: {e}")
        return "Sorry, there was an error generating the reminder letter."
