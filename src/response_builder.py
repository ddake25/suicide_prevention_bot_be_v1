# src/response_builder.py
import re
from typing import List, Optional, Literal
from pydantic import BaseModel

class Action(BaseModel):
    type: Literal["open_link", "copy_text", "show_help"]
    label: str
    payload: Optional[dict] = None

class ChatResponse(BaseModel):
    text: str
    risk: Literal["low", "medium", "high"] = "low"
    actions: List[Action] = []
    references: List[str] = []

HIGH = [r"\bkill myself\b", r"\bsuicide\b", r"\bend my life\b", r"\bi want to die\b", r"\bi can.?t go on\b"]
MED  = [r"\bhopeless\b", r"\bno point\b", r"\bself[- ]?harm\b", r"\bcutting\b", r"\bplan\b", r"\bmeans\b", r"\bmethod\b"]

def _match_any(text: str, pats: List[str]) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in pats)

def classify_risk(user_text: str, model_text: str = "") -> str:
    if _match_any(user_text, HIGH) or _match_any(model_text, HIGH):
        return "high"
    if _match_any(user_text, MED) or _match_any(model_text, MED):
        return "medium"
    return "low"

def _prefix(risk: str) -> str:
    if risk == "high":
        return ("I'm really glad you reached out. I’m not a crisis service. "
                "If you might harm yourself, call 911 (US) or contact 988 now. ")
    if risk == "medium":
        return ("Thanks for sharing this—you're not alone. "
                "Here are a few grounding steps and resources that may help. ")
    return ""

def _actions(risk: str) -> List[Action]:
    if risk == "high":
        return [
            Action(type="open_link", label="Emergency: 911", payload={"href": "tel:911"}),
            Action(type="open_link", label="988 Lifeline", payload={"href": "https://988lifeline.org"})
        ]
    if risk == "medium":
        return [
            Action(type="copy_text", label="5-4-3-2-1 Grounding",
                   payload={"text": "Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste."}),
            Action(type="open_link", label="988 Lifeline", payload={"href": "https://988lifeline.org"})
        ]
    return []

def _tidy(text: str, max_lines: int = 6) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(lines[:max_lines])

def build_response(model_text: str, user_text: str, refs: List[str]) -> ChatResponse:
    risk = classify_risk(user_text, model_text)
    final_text = (_prefix(risk) + _tidy(model_text)).strip()
    return ChatResponse(text=final_text, risk=risk, actions=_actions(risk), references=refs)
