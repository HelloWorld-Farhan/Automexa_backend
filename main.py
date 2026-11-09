import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import chromadb

app = FastAPI(
    title="⚡ Automexa AI Reasoning Backend",
    description="High-performance cloud intelligence engine powered by Google Gemini 2.5 Flash and ChromaDB vector search for autonomous job applications.",
    version="1.0.0"
)

# Enable CORS for all mobile and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChromaDB Vector Database Collection
chroma_client = chromadb.Client()
profile_collection = chroma_client.get_or_create_collection(name="automexa_candidate_context")

# Google Gemini Client Initialization
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None

class ReasonRequest(BaseModel):
    question: str
    field_type: str = "text"  # "text", "number", "dropdown", "radio"
    options: Optional[List[str]] = []
    user_id: Optional[str] = "farhan"

class ReasonResponse(BaseModel):
    answer: str
    confidence: float
    reasoning: Optional[str] = None

class ProfileSyncRequest(BaseModel):
    user_id: str = "farhan"
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
        "service": "Automexa AI Cloud Intelligence Backend",
        "version": "1.0.0",
        "gemini_active": bool(gemini_client)
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Automexa Backend"}

@app.post("/api/v1/sync-profile")
def sync_profile(req: ProfileSyncRequest):
    """
    Ingests candidate resume markdown and core parameters into ChromaDB for dynamic retrieval.
    """
    try:
        sections = req.resume_markdown.split("\n\n")
        documents = [s.strip() for s in sections if s.strip()]

        documents.append(f"Candidate Name: {req.full_name}")
        documents.append(f"Primary Skills: {', '.join(req.primary_skills)}")
        documents.append(f"Current Compensation (CTC): {req.current_ctc}")
        documents.append(f"Expected Compensation (CTC): {req.expected_ctc}")
        documents.append(f"Official Notice Period: {req.notice_period_days} days")

        ids = [f"{req.user_id}_doc_{i}" for i in range(len(documents))]

        profile_collection.upsert(
            documents=documents,
            ids=ids
        )
        return {
            "status": "success",
            "message": "Candidate profile successfully indexed into vector database.",
            "chunks_indexed": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.get("/api/v1/profile-status")
def profile_status():
    """
    Returns the count of indexed candidate facts and resume chunks.
    """
    count = profile_collection.count()
    return {
        "indexed_chunks": count,
        "ready_for_reasoning": count > 0
    }

@app.post("/api/v1/reason-field", response_model=ReasonResponse)
def reason_field(req: ReasonRequest):
    """
    Retrieves candidate context and queries Gemini 2.5 Flash to accurately answer application fields.
    """
    try:
        # 1. Retrieve top matching chunks from ChromaDB
        results = profile_collection.query(
            query_texts=[req.question],
            n_results=3
        )
        matched_docs = results.get("documents", [[]])[0]
        context_str = "\n".join(matched_docs) if matched_docs else "No specific resume chunk matched."

        # 2. Prompt Gemini 2.5 Flash
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
            # Deterministic intelligent fallback when API key is not yet set
            q_lower = req.question.lower()
            if "notice" in q_lower:
                ans = "30"
            elif "experience" in q_lower:
                ans = "4"
            elif "visa" in q_lower or "sponsorship" in q_lower:
                ans = "No"
            elif "authorized" in q_lower:
                ans = "Yes"
            else:
                ans = req.options[0] if req.options else "Yes"

            return ReasonResponse(
                answer=ans,
                confidence=0.85,
                reasoning="Deterministic rule-based fallback active (set GEMINI_API_KEY in Render to activate Gemini 2.5 Flash)."
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
        raise HTTPException(status_code=500, detail=f"Reasoning error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

