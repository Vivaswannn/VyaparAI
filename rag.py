from google import genai
import numpy as np
import json

client = genai.Client()

async def generate_embedding(text: str) -> list[float]:
    """Generates an embedding vector using gemini-embedding-2."""
    try:
        result = await client.aio.models.embed_content(
            model="gemini-embedding-2",
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

def retrieve_relevant_documents(query_embedding: list[float], documents: list[dict], top_k: int = 3) -> list[dict]:
    """
    Performs cosine similarity search between query embedding and document embeddings.
    Returns the top_k most relevant documents.
    """
    if not documents or not query_embedding:
        return []
        
    query_vec = np.array(query_embedding)
    results = []
    
    for doc in documents:
        if not doc.get("embedding"):
            continue
            
        doc_vec = np.array(doc["embedding"])
        
        # Compute cosine similarity
        dot_product = np.dot(query_vec, doc_vec)
        norm_query = np.linalg.norm(query_vec)
        norm_doc = np.linalg.norm(doc_vec)
        
        if norm_query == 0 or norm_doc == 0:
            similarity = 0.0
        else:
            similarity = dot_product / (norm_query * norm_doc)
            
        results.append({
            "doc": doc,
            "similarity": float(similarity)
        })
        
    # Sort by descending similarity
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top_k documents
    return [res["doc"] for res in results[:top_k]]

def format_document_for_embedding(extracted_data: dict) -> str:
    """Converts the structured JSON into a searchable text string."""
    return json.dumps(extracted_data, indent=2)
