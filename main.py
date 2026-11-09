import os
import json
import itertools
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import chromadb
try:
    from groq import Groq
except ImportError:
    Groq = None

app = FastAPI(
    title="⚡ Automexa AI Cloud Intelligence Engine",
    description="Multi-Key Round-Robin Engine supporting Gemini 2.5 Flash and Groq AI with automatic failover.",
    version="1.0.4"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory ChromaDB vector store
chroma_client = chromadb.Client()
profile_collection = chroma_client.get_or_create_collection(name="automexa_candidate_context")

# Parse comma-separated keys from environment variables
def get_keys(env_var_name: str) -> List[str]:
    raw = os.getenv(env_var_name, "").strip()
    if not raw:
        return []
    # Split by comma or newline
    return [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]

gemini_keys = get_keys("GEMINI_API_KEYS") or get_keys("GEMINI_API_KEY")
groq_keys = get_keys("GROQ_API_KEYS") or get_keys("GROQ_API_KEY")

class KeyRotator:
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.index = 0

    def get_current(self) -> Optional[str]:
        if not self.keys:
            return None
        return self.keys[self.index % len(self.keys)]

    def rotate(self) -> Optional[str]:
        if not self.keys:
            return None
        self.index = (self.index + 1) % len(self.keys)
        return self.get_current()

gemini_rotator = KeyRotator(gemini_keys)
groq_rotator = KeyRotator(groq_keys)

class ReasonRequest(BaseModel):
    question: str
    field_type: str = "text"  # "text", "number", "dropdown", "radio"
    options: Optional[List[str]] = []
    user_id: Optional[str] = "farhan"

class ReasonResponse(BaseModel):
    answer: str
    confidence: float
    provider_used: str
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
        "service": "Automexa Multi-Key AI Engine",
        "version": "1.0.4",
        "gemini_keys_loaded": len(gemini_rotator.keys),
        "groq_keys_loaded": len(groq_rotator.keys)
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/sync-profile")
def sync_profile(req: ProfileSyncRequest):
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

def build_prompt(question: str, field_type: str, options: list, context_str: str) -> str:
    return f"""You are an autonomous job applicant assistant. Answer the form question based strictly on candidate context.

Candidate Profile Context:
{context_str}

Form Question:
- Question: "{question}"
- Field Type: {field_type}
- Options: {options}

Rules:
1. If field_type is 'number', return ONLY digits (e.g. 4 or 30).
2. If field_type is 'dropdown' or 'radio', choose the EXACT string match from Options.
3. Return strictly valid JSON:
{{
    "answer": "<exact string or number>",
    "confidence": 0.98,
    "reasoning": "<short 1-sentence rationale>"
}}
"""

@app.post("/api/v1/reason-field", response_model=ReasonResponse)
def reason_field(req: ReasonRequest):
    # 1. Retrieve top matching chunks from ChromaDB
    results = profile_collection.query(
        query_texts=[req.question],
        n_results=3
    )
    matched_docs = results.get("documents", [[]])[0]
    context_str = "\n".join(matched_docs) if matched_docs else "No specific resume chunk matched."
    prompt = build_prompt(req.question, req.field_type, req.options or [], context_str)

    # 2. Try Gemini with Round-Robin loop across all loaded keys
    if gemini_rotator.keys:
        initial_index = gemini_rotator.index
        for _ in range(len(gemini_rotator.keys)):
            current_key = gemini_rotator.get_current()
            try:
                client = genai.Client(api_key=current_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                data = json.loads(response.text)
                gemini_rotator.rotate() # advance to next key for fair load balancing
                return ReasonResponse(
                    answer=str(data.get("answer", "")),
                    confidence=float(data.get("confidence", 0.98)),
                    provider_used="Gemini 2.5 Flash (Key Rotation)",
                    reasoning=data.get("reasoning")
                )
            except Exception as e:
                # Key error or rate limit 429: rotate to next key
                gemini_rotator.rotate()

    # 3. Fallback: Try Groq AI with Round-Robin loop across all loaded Groq keys
    if groq_rotator.keys and Groq:
        for _ in range(len(groq_rotator.keys)):
            current_groq_key = groq_rotator.get_current()
            try:
                groq_client = Groq(api_key=current_groq_key)
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a job application answering assistant. Respond only in JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                )
                raw_text = chat_completion.choices[0].message.content
                data = json.loads(raw_text)
                groq_rotator.rotate()
                return ReasonResponse(
                    answer=str(data.get("answer", "")),
                    confidence=float(data.get("confidence", 0.96)),
                    provider_used="Groq Llama 3.3 70B (Key Rotation)",
                    reasoning=data.get("reasoning")
                )
            except Exception as e:
                groq_rotator.rotate()

    # 4. Deterministic safe fallback
    q_lower = req.question.lower()
    if "notice" in q_lower:
        ans = "30"
    elif "experience" in q_lower or "years" in q_lower:
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
        provider_used="Deterministic Fallback",
        reasoning="All cloud keys rotated; returning safe profile default."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
