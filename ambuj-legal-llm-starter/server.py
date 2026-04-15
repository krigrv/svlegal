import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from pydantic import BaseModel, Field


load_dotenv()

MODEL_REPO = "invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF"
MODEL_FILE = "llama-3.2-1b-instruct.Q4_K_M.gguf"
DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / "models"

BASE_SYSTEM_PROMPT = """You are SV Legal AI, an Indian legal drafting and research assistant for a lawyer's internal educational use.
You help with legal notices, issue spotting, case briefs, client emails, clause review, compliance checklists, and research memos.
Do not claim to be a lawyer. Do not present output as final legal advice.
Use Indian legal context by default. If jurisdiction, dates, parties, forum, value, limitation, or key facts are missing, ask for them briefly before making strong conclusions.
Prefer structured, lawyer-ready output with concise headings, numbered clauses where useful, and practical next steps.
If you are unsure about a section number, citation, limitation period, or current legal position, say it must be verified from an official source.
Never invent case citations. Mark placeholders clearly in square brackets.
"""

WORKFLOW_PROMPTS = {
    "general": "Answer as a concise legal assistant. Give assumptions, analysis, and next steps.",
    "legal_notice": "Draft a formal Indian legal notice. Include parties, facts, demand, timeline to comply, consequences of non-compliance, and placeholders for missing details.",
    "case_brief": "Prepare a case brief. Use: Facts, Issues, Applicable Law To Verify, Arguments For Client, Risks, Evidence Needed, Next Steps.",
    "clause_review": "Review the clause or contract extract. Use: Concern, Risk Level, Why It Matters, Suggested Revision, Negotiation Note.",
    "research_memo": "Prepare a short research memo. Use: Question Presented, Short Answer, Legal Position To Verify, Analysis, Practical Recommendation.",
    "client_email": "Draft a polished client email. Keep it professional, clear, and cautious. Include caveats and action items.",
    "compliance_checklist": "Create a compliance checklist. Group by immediate, short-term, and ongoing actions with owner/document columns where useful.",
    "document_summary": "Summarize the supplied document or facts. Use: Executive Summary, Key Points, Risks, Missing Information, Questions For Client.",
}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    workflow: str = Field(default="general", max_length=40)
    temperature: float = Field(default=0.35, ge=0.0, le=1.0)
    max_tokens: int = Field(default=768, ge=64, le=1600)


class ChatResponse(BaseModel):
    answer: str
    model_repo: str = MODEL_REPO
    model_file: str = MODEL_FILE


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def allowed_origins() -> list[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:4174,http://localhost:4174,http://127.0.0.1:5500,http://localhost:5500",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def resolve_model_path() -> Path:
    configured_path = os.getenv("MODEL_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return DEFAULT_MODEL_DIR / MODEL_FILE


def ensure_model_file() -> Path:
    model_path = resolve_model_path()
    if model_path.exists():
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        local_dir=str(model_path.parent),
        token=os.getenv("HF_TOKEN"),
    )
    return Path(downloaded_path).resolve()


def verify_backend_token(authorization: str | None) -> None:
    expected_token = os.getenv("LEGAL_AI_BACKEND_TOKEN")
    if not expected_token:
        return

    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Invalid backend token")


@lru_cache(maxsize=1)
def load_llm() -> Llama:
    model_path = ensure_model_file()
    return Llama(
        model_path=str(model_path),
        n_ctx=env_int("N_CTX", 4096),
        n_gpu_layers=env_int("N_GPU_LAYERS", 0),
        chat_format="llama-3",
        verbose=False,
    )


def build_system_prompt(workflow: str) -> str:
    workflow_prompt = WORKFLOW_PROMPTS.get(workflow, WORKFLOW_PROMPTS["general"])
    return f"{BASE_SYSTEM_PROMPT}\n\nCurrent work product mode: {workflow_prompt}"


app = FastAPI(title="SV Legal AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health(authorization: str | None = Header(default=None)) -> dict[str, str]:
    verify_backend_token(authorization)
    return {"status": "ok", "model_repo": MODEL_REPO, "model_file": MODEL_FILE}


@app.post("/api/legal-ai", response_model=ChatResponse)
def legal_ai(request: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    verify_backend_token(authorization)
    try:
        llm = load_llm()
        messages = [{"role": "system", "content": build_system_prompt(request.workflow)}]
        messages.extend(message.model_dump() for message in request.history)
        messages.append({"role": "user", "content": request.message})

        result = llm.create_chat_completion(
            messages=messages,
            temperature=request.temperature,
            top_p=0.9,
            max_tokens=request.max_tokens,
        )
        answer = result["choices"][0]["message"]["content"]
        return ChatResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
