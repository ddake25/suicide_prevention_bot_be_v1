from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.core_rag import ask

router = APIRouter()

class ChatRequest(BaseModel):
    message: str  # payload: { "message": "..." }

class RAGAsk(BaseModel):
    session_id: Optional[str] = None
    message: str

@router.post("/send")
def rag_ask(payload: RAGAsk):
    try:
        reply = ask(payload.session_id, payload.message)
        return {"payload": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




# @router.post("/send")
# async def process_chat(payload: ChatRequest):
#     user_message = payload.message.strip()
#     if not user_message:
#         raise HTTPException(status_code=400, detail="Empty 'message'")

#     # TODO: call your LLM here; for now echo back
#     bot_reply = f"You said: {user_message}"

#     # Keep it simple for TTS on the frontend
#     return {
#         "payload": bot_reply
#     }
