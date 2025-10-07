import os
import logging
import uuid
from pathlib import Path
from typing import Dict, Optional

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
)
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama  # NEW import (no deprecation)

# ---------- Logging ----------
logger = logging.getLogger("rag")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    logger.addHandler(h)

# ---------- Config ----------
OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "gemma3:1b")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./vectorstore/faiss")  # directory
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
INDEX_NAME       = os.getenv("FAISS_INDEX_NAME", "index")  # expects index.faiss / index.pkl

# Ensure FAISS dir exists to avoid noisy errors when empty
Path(FAISS_INDEX_PATH).mkdir(parents=True, exist_ok=True)

DEFAULT_SESSION_ID = "default"
_histories: Dict[str, ChatMessageHistory] = {}

FRIENDLY_FALLBACK = (
    "Sorry, I ran into a temporary glitch while retrieving information. "
    "Please try again in a moment."
)

def _get_history(session_id: str) -> ChatMessageHistory:
    if session_id not in _histories:
        _histories[session_id] = ChatMessageHistory()
    return _histories[session_id]

def _faiss_files_exist(dir_path: Path, index_name: str) -> bool:
    return (dir_path / f"{index_name}.faiss").exists() and (dir_path / f"{index_name}.pkl").exists()

def _load_vectorstore_safe() -> Optional[FAISS]:
    try:
        base = Path(FAISS_INDEX_PATH)
        if not _faiss_files_exist(base, INDEX_NAME):
            logger.info(f"FAISS files not found yet at: {base.resolve()} (running no-context)")
            return None

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vs = FAISS.load_local(
            str(base),
            embeddings,
            index_name=INDEX_NAME,
            allow_dangerous_deserialization=True
        )
        return vs
    except Exception:
        err_id = str(uuid.uuid4())
        logger.exception(f"[{err_id}] Failed to load FAISS index from {FAISS_INDEX_PATH}")
        return None  # fall back gracefully

def _build_retriever_safe(vs: Optional[FAISS]):
    if vs is None:
        class _NullRetriever:
            def get_relevant_documents(self, *_args, **_kwargs):
                return []
        return _NullRetriever()
    return vs.as_retriever(search_type="similarity", search_kwargs={"k": 4})

def _build_llm_safe() -> Optional[ChatOllama]:
    try:
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0.2,
        )
    except Exception:
        err_id = str(uuid.uuid4())
        logger.exception(f"[{err_id}] Failed to initialize ChatOllama at {OLLAMA_BASE_URL}")
        return None

SYSTEM_INSTRUCTIONS = (
    "You are Patient AI, a careful health-literacy assistant. "
    "Use only the provided context. If the answer is not in the context, say you don’t know briefly."
)

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_INSTRUCTIONS),
        ("system", "Context:\n{context}\n\nUse this context to answer."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

def _format_docs(docs) -> str:
    try:
        return "\n\n".join(f"[{(d.metadata or {}).get('source','unknown')}] {d.page_content}" for d in docs)
    except Exception:
        return ""

def get_rag_chain_safe() -> Optional[Runnable]:
    """
    Build an LCEL chain robustly and pass the correct types to the prompt:
    - history: List[BaseMessage]
    - question: str
    - context: str
    """
    vs = _load_vectorstore_safe()
    retriever = _build_retriever_safe(vs)
    llm = _build_llm_safe()
    if llm is None:
        return None

    def _retrieve(question: str):
        try:
            if hasattr(retriever, "get_relevant_documents"):
                return retriever.get_relevant_documents(question) or []
        except Exception:
            err_id = str(uuid.uuid4())
            logger.exception(f"[{err_id}] Retrieval failure")
        return []

    # Build each prompt var explicitly
    context_r = (
        RunnableLambda(lambda inp: inp.get("question", ""))   # str
        | RunnableLambda(_retrieve)                            # -> docs[]
        | RunnableLambda(lambda docs: _format_docs(docs))      # -> str
    )

    inputs = {
        "context": RunnableLambda(lambda inp: context_r.invoke(inp)),
        "history": RunnableLambda(lambda inp: inp.get("history", [])),   # MUST be List[BaseMessage]
        "question": RunnableLambda(lambda inp: inp.get("question", "")), # str
    }

    try:
        chain = (inputs | PROMPT | llm | StrOutputParser())
        return chain
    except Exception:
        err_id = str(uuid.uuid4())
        logger.exception(f"[{err_id}] Failed to build RAG chain")
        return None

def ask(session_id: Optional[str], user_message: str) -> str:
    """
    Always return a user-friendly string.
    On any internal error, log it and return FRIENDLY_FALLBACK.
    """
    sid = (session_id or DEFAULT_SESSION_ID).strip() or DEFAULT_SESSION_ID
    if not user_message or not user_message.strip():
        return "Please provide a message."

    hist = _get_history(sid)
    chain = get_rag_chain_safe()
    if chain is None:
        return FRIENDLY_FALLBACK

    try:
        response: str = chain.invoke({"history": hist.messages, "question": user_message})
        hist.add_user_message(user_message)
        hist.add_ai_message(response)
        return response or "I don’t know."
    except Exception:
        err_id = str(uuid.uuid4())
        logger.exception(f"[{err_id}] Generation failure")
        return FRIENDLY_FALLBACK

def reset_session(session_id: Optional[str] = None) -> None:
    sid = (session_id or DEFAULT_SESSION_ID).strip() or DEFAULT_SESSION_ID
    if sid in _histories:
        del _histories[sid]
