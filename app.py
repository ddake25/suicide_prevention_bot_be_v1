from fastapi import FastAPI
from src.test_route import router as test_router
from src.llm_route import router as llm_router   # <-- add this

app = FastAPI(title="SP Chatbot API")

app.include_router(test_router)  # /firstapi
app.include_router(llm_router)   # /ask
