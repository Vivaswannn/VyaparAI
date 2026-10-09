import json
from google import genai
from google.genai import types
from datetime import datetime

client = genai.Client()

async def generate_action_plan(query: str, retrieved_docs: list[dict]) -> dict:
    """
    Takes the user query and the retrieved documents, and uses Gemini 
    to synthesize a cited action plan.
    """
    
    # Format context string
    context_blocks = []
    for doc in retrieved_docs:
        filename = doc.get("filename", "Unknown Document")
        data = json.dumps(doc.get("extracted_data", {}), indent=2)
        context_blocks.append(f"--- Document: {filename} ---\n{data}\n")
        
    context_str = "\n".join(context_blocks)
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are VyaparAI, an AI copilot for Indian MSMEs. 
    Today's date is: {today}
    
    A user has asked a question: "{query}"
    
    Here is the ONLY business context you have (extracted from their invoices/bills):
    {context_str}
    
    INSTRUCTIONS:
    1. Answer the user's question using ONLY the provided document context.
    2. If the answer is not contained in the documents, explicitly state "I don't have enough information in the uploaded documents." DO NOT hallucinate.
    3. Generate a summary of your findings.
    4. Generate a list of recommended actions.
    5. List the exact filenames of the documents you relied on to make this plan.
    """
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING"},
                        "actions": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "text": {"type": "STRING"},
                                    "source": {"type": "STRING"}
                                },
                                "required": ["text", "source"]
                            }
                        },
                        "sources_used": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        }
                    },
                    "required": ["summary", "actions", "sources_used"]
                },
                temperature=0.2
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Action plan generation error: {e}")
        return {
            "summary": "Sorry, I encountered an error while analyzing the documents.",
            "actions": [],
            "sources_used": []
        }
