import json
from groq import AsyncGroq
from datetime import datetime

client = AsyncGroq()

async def generate_action_plan(query: str, all_docs: list[dict]) -> dict:
    """
    Takes the user query and the entire historical ledger, and uses Groq 
    to synthesize a macro-level action plan and answer aggregate questions.
    """
    
    # Format the entire ledger as a structured list for context
    ledger = []
    for doc in all_docs:
        ledger.append({
            "File": doc["filename"],
            "Vendor": doc["vendor_name"],
            "Amount": doc["amount"],
            "DueDate": doc["due_date"],
            "Status": doc["payment_status"]
        })
        
    context_str = json.dumps(ledger, indent=2)
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are VyaparAI, an expert AI financial analyst and copilot for Indian MSMEs. 
    Today's date is: {today}
    
    The user has asked: "{query}"
    
    Here is the complete historical ledger of all their uploaded invoices and bills:
    {context_str}
    
    INSTRUCTIONS:
    1. Analyze the ledger data to answer the user's question. Calculate totals, monthly dues, or aggregate data if they ask for it.
    2. Do NOT hallucinate data. If the answer cannot be calculated from the ledger, explicitly state that.
    3. Generate a concise summary of your analysis.
    4. Provide recommended actions based on the analysis (e.g., "Pay Vendor X by Friday").
    5. List the exact filenames of any specific invoices you referenced in your answer.
    
    Return ONLY valid JSON matching this schema exactly:
    {{
      "summary": "string",
      "actions": [
        {{"text": "string (the action)", "source": "string (the filename cited or 'Aggregate Data')"}}
      ],
      "sources_used": ["filename1.pdf", "filename2.jpg"]
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a precise financial assistant that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1024
        )
        
        result_json = response.choices[0].message.content
        return json.loads(result_json)
    except Exception as e:
        print(f"Action plan generation error: {e}")
        return {
            "summary": "Sorry, I encountered an error while analyzing your ledger.",
            "actions": [],
            "sources_used": []
        }
