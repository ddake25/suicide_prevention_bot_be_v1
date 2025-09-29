import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.test_route import router as api_test_route


app = FastAPI()


# Reminders route
app.include_router(api_test_route, prefix="/test")

