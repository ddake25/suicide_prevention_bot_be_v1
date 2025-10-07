import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.test_route import router as api_test_route
from src.chat_llm import router as chat_llm_route


app = FastAPI()

# CORS settings
# Allow your React dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://192.168.1.185:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        "*"
    ],   # adjust if your frontend runs elsewhere
    allow_credentials=True,
    allow_methods=["*"],       # important: lets preflight succeed for POST
    allow_headers=["*"],       # important: lets Content-Type: application/json through
)

# Reminders route
app.include_router(api_test_route, prefix="/test")

# app.include_router(api_test_route, prefix="/rag_document")

app.include_router(chat_llm_route, prefix="/chat_llm")


# uvicorn app:app --host 0.0.0.0 --port 8000 --ssl-certfile certs\api.pem --ssl-keyfile certs\api-key.pem


# $uri = "https://api.github.com/repos/FiloSottile/mkcert/releases/latest"
# $asset = (Invoke-RestMethod $uri).assets | Where-Object { $_.name -match "windows-amd64\.exe$" } | Select-Object -First 1
# Invoke-WebRequest $asset.browser_download_url -OutFile mkcert.exe