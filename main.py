import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
import chromadb

app = FastAPI(
    title="Automexa AI RAG Engine",
    description="Render backend powering autonomous job application reasoning with Gemini 2.5 Flash and vector search.",
    version="1.0.0"
)

# In-memory ChromaDB vector collection for candidate resume context
chroma_client = chromadb.Client()
profile_collection = chroma_client.get_or_create_collection(name="candidate_profile")

# Google Gemini Client
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None

class ReasonRequest(BaseModel):
    question: str
    field_type: str  # "text", "number", "dropdown", "radio"
    options: Optional[List[str]] = []
    user_id: Optional[str] = "default"

class ReasonResponse(BaseModel):
    answer: str
    confidence: float
    reasoning: Optional[str] = None

class ProfileSyncRequest(BaseModel):
    user_id: str
    full_name: str
    resume_markdown: str
    primary_skills: List[str]
    current_ctc: str
    expected_ctc: str
    notice_period_days: int

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Automexa AI RAG Engine",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/sync-profile")
def sync_profile(req: ProfileSyncRequest):
    """
    Ingests and vectorizes candidate profile details into ChromaDB for dynamic question retrieval.
    """
    try:
        # Split markdown into sections
        sections = req.resume_markdown.split("\n\n")
        documents = [s.strip() for s in sections if s.strip()]
        
        # Add basic structured metadata facts
        documents.append(f"Full Name: {req.full_name}")
        documents.append(f"Primary Skills: {', '.join(req.primary_skills)}")
        documents.append(f"Current CTC: {req.current_ctc}")
        documents.append(f"Expected CTC: {req.expected_ctc}")
        documents.append(f"Notice Period: {req.notice_period_days} days")

        ids = [f"{req.user_id}_doc_{i}" for i in range(len(documents))]

        profile_collection.upsert(
            documents=documents,
            ids=ids
        )
        return {"status": "synced", "chunks_indexed": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reason-field", response_model=ReasonResponse)
def reason_field(req: ReasonRequest):
    """
    Given a form question and options, queries candidate vector context and uses Gemini to answer.
    """
    try:
        # 1. Vector Search for relevant resume chunks
        results = profile_collection.query(
            query_texts=[req.question],
            n_results=3
        )
        matched_docs = results.get("documents", [[]])[0]
        context_str = "\n".join(matched_docs) if matched_docs else "No specific resume chunk found."

        # 2. Build Gemini prompt
        prompt = f"""
You are an expert autonomous job applicant agent. You must answer a form question based strictly on the candidate context.

Candidate Profile Context:
{context_str}

Form Question Details:
- Question: "{req.question}"
- Field Type: {req.field_type}
- Available Options: {req.options}

Instructions:
1. If field_type is 'number', return ONLY integer or float numbers (e.g. 4 or 30).
2. If field_type is 'dropdown' or 'radio', choose the EXACT string match from Available Options.
3. Be professional and accurate.
4. Return strictly valid JSON in this exact structure:
{{
    "answer": "<your chosen string or number>",
    "confidence": <float from 0.0 to 1.0>,
    "reasoning": "<short 1-sentence rationale>"
}}
"""

        if not gemini_client:
            # Deterministic fallback when Gemini API key is not configured
            fallback_answer = "Yes" if "authorized" in req.question.lower() else "30"
            return ReasonResponse(
                answer=fallback_answer,
                confidence=0.8,
                reasoning="Fallback mode active (GEMINI_API_KEY pending)."
            )

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        data = json.loads(response.text)
        return ReasonResponse(
            answer=str(data.get("answer", "")),
            confidence=float(data.get("confidence", 0.95)),
            reasoning=data.get("reasoning")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning failure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
