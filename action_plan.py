import json
from groq import AsyncGroq
from datetime import datetime

async def generate_action_plan(query: str, all_docs: list[dict], language: str = "english") -> dict:
    """
    Takes the user query and the entire historical ledger, and uses Groq 
    to synthesize a macro-level action plan and answer aggregate questions.
    """
    client = AsyncGroq()
    
    # Format the entire ledger as a structured list for context, deduplicating by filename to prevent double-counting!
    ledger = []
    seen_filenames = set()
    for doc in all_docs:
        if doc["filename"] not in seen_filenames:
            seen_filenames.add(doc["filename"])
            ledger.append({
                "File": doc["filename"],
                "Vendor": doc["vendor_name"],
                "Amount": doc["amount"],
                "DueDate": doc["due_date"],
                "Status": doc["payment_status"]
            })
        
    context_str = json.dumps(ledger, indent=2)
    today = datetime.now().strftime("%Y-%m-%d")
    
    language_instruction = ""
    if language.lower() == "hindi":
        language_instruction = "\nCRITICAL: You must write the 'summary' and the 'actions' text entirely in HINDI (Devanagari script). The JSON keys must remain in English."
    
    prompt = f"""
    You are VyaparAI, an expert AI financial analyst and copilot for Indian MSMEs. 
    Today's date is: {today}
    
    The user has asked: "{query}"
    
    Here is the complete historical ledger of all their uploaded invoices and bills (duplicates removed):
    {context_str}
    {language_instruction}
    
    INSTRUCTIONS:
    1. Analyze the ledger data to answer the user's question.
    2. IMPORTANT: In your 'summary', explicitly list out the individual bills (by Vendor and Amount) that you are counting BEFORE stating the final total. Explain your math clearly (e.g., "I see two bills: $50 for Vendor A and $100 for Vendor B. The total is $150.").
    3. Do NOT hallucinate data. If the answer cannot be calculated from the ledger, explicitly state that.
    4. Generate a concise summary of your analysis.
    5. Provide recommended actions based on the analysis (e.g., "Pay Vendor X by Friday").
    6. List the exact filenames of any specific invoices you referenced in your answer.
    
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
