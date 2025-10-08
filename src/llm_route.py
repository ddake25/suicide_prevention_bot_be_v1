# src/llm_route.py
from fastapi import APIRouter
from pydantic import BaseModel
from .llm_client import chat
from .synth_data import retrieve
from .response_builder import build_response

router = APIRouter()

class AskBody(BaseModel):
    message: str
    session_id: str | None = None

@router.post("/ask")
def ask(body: AskBody):
    # 1) retrieve context from your synthetic md files
    ctx_docs = retrieve(body.message, k=3)
    context = "\n\n".join([f"[{name}]\n{snippet}" for name, snippet in ctx_docs])

    # 2) prepare messages for the local LLM (Ollama)
    system = (
        "You are a supportive assistant. Do not give clinical advice. "
        "Use the CONTEXT to answer briefly and kindly."
    )
    messages = [
        {"role": "system", "content": system + "\n\nCONTEXT:\n" + context},
        {"role": "user", "content": body.message}
    ]

    # 3) call the local model
    model_text = chat(messages)

    # 4) format final response (risk/actions/refs)
    refs = [name for name, _ in ctx_docs]
    return build_response(model_text=model_text, user_text=body.message, refs=refs).model_dump()
