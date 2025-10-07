# scripts/seed_faiss.py
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Must match your runtime env vars
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./vectorstore/faiss")
INDEX_NAME       = os.getenv("FAISS_INDEX_NAME", "index")

# Some quick demo texts; replace with anything you want
docs = [
    ("amoxicillin", "Amoxicillin is a penicillin-type antibiotic. Typical adult dose for mild infections is 500 mg every 8 hours or 875 mg every 12 hours, per clinician guidance."),
    ("acetaminophen", "Acetaminophen helps with pain and fever. Do not exceed 3,000 mg/day for most adults without clinician advice."),
    ("hydration", "Staying hydrated supports general health. Small, frequent sips can help if you feel nauseated."),
]

def main():
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    texts = [d[1] for d in docs]
    metadatas = [{"source": f"seed::{d[0]}"} for d in docs]

    vs = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)

    # save as index.faiss + index.pkl
    vs.save_local(FAISS_INDEX_PATH, index_name=INDEX_NAME)
    print(f"Seeded FAISS at {Path(FAISS_INDEX_PATH).resolve()} (name='{INDEX_NAME}') with {len(texts)} texts.")

if __name__ == "__main__":
    main()
