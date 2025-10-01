# src/synth_data.py
from pathlib import Path
import re

# points to: <repo_root>/data/synth
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synth"

def _load_docs():
    """
    Loads all .md files from data/synth and returns a list of (name, text).
    """
    docs = []
    if DATA_DIR.exists():
        for p in DATA_DIR.glob("*.md"):
            try:
                docs.append((p.name, p.read_text(encoding="utf-8")))
            except Exception:
                pass  # skip unreadable files
    return docs

def retrieve(query: str, k: int = 3):
    """
    Very simple keyword scoring:
    - split query into words
    - score each doc by occurrences
    - return top k snippets (name, first 500 chars)
    """
    docs = _load_docs()
    if not docs:
        return []

    q = (query or "").lower()
    words = re.findall(r"\w+", q)

    scored = []
    for name, text in docs:
        t = text.lower()
        score = sum(t.count(w) for w in words)  # naive frequency score
        scored.append((score, name, text))

    # sort by score descending
    scored.sort(reverse=True, key=lambda x: x[0])

    # pick top k with positive score; fallback to just top k
    top = [(name, text[:500]) for s, name, text in scored if s > 0][:k]
    if not top:
        top = [(name, text[:500]) for _, name, text in scored[:k]]

    return top
