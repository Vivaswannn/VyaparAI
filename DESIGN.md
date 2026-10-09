# VyaparAI — Architecture & Implementation Plan
*Hackathon / Demo MVP*

## 1. Problem Statement
Small business owners (MSMEs) in India struggle to track payments across scattered paper/PDF invoices and bills. They need an AI copilot that understands their specific business documents and generates actionable advice, not generic recommendations.

## 2. Core User Journey
1. **Upload:** User uploads invoices/bills (PDFs/images).
2. **Extract:** System converts all documents to images and uses GPT-4o Vision to extract structured JSON (vendor, amount, due date, tax info, status).
3. **Query:** User asks a natural language question (typed or spoken via Web Speech API).
4. **Retrieve & Reason:** System embeds the query, retrieves the top relevant documents via cosine similarity, and uses GPT-4o to synthesize a specific action plan citing those documents.
5. **Display:** UI presents the cited action plan and optionally reads it aloud.
6. **Bonus (Reminder):** One-click generation of a payment reminder letter for overdue invoices.

## 3. Architecture Decisions (The "Vision-Only Fast Path")
- **Frontend:** Plain HTML/JS with Tailwind CSS via CDN (zero build step). Web Speech API for voice.
- **Backend:** FastAPI (Python). In-memory storage for the hackathon (no external DBs).
- **Extraction:** **GPT-4o Vision ONLY**. Convert any PDFs to images server-side. This eliminates `pdfplumber` edge cases and perfectly parses messy or scanned tabular data.
- **RAG:** OpenAI `text-embedding-3-small` for embeddings. In-memory cosine similarity search.
- **LLM Reasoning:** OpenAI GPT-4o with strict instructions to cite sources and output JSON.

## 4. Required Components
| Component | Responsibility |
|---|---|
| `main.py` | FastAPI app, routes, in-memory storage, orchestration |
| `extract.py` | Document to Image conversion + GPT-4o Vision structured JSON extraction |
| `rag.py` | OpenAI embeddings + in-memory similarity search |
| `action_plan.py` | GPT-4o reasoning step, producing the cited action plan |
| `reminder.py` | Generates the reminder letter |
| `frontend/index.html` | Tailwind-styled UI for upload, query (voice/text), and results |

## 5. Design Principles
- **No hallucination:** AI must only reason from retrieved documents and explicitly flag missing info.
- **Traceability:** Every recommendation must cite the source document.
- **Graceful degradation:** Pipeline stages must not crash the whole flow on a bad file.

## 6. Build Order
1. **Scaffold:** Initialize FastAPI app and serve static frontend.
2. **Extraction:** Implement PDF-to-image and GPT-4o Vision extraction prompt.
3. **RAG:** Build the embedding and retrieval logic.
4. **Action Plan:** Connect retrieval to the final GPT-4o reasoning prompt.
5. **Frontend:** Wire up the UI, add Tailwind CSS, and implement Web Speech API.
6. **Bonuses:** Add the reminder letter generation endpoint.
