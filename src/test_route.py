from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter()

@router.get("/firstapi")
def create_reminder():
    
    return {
        "payload": "API Works Fine!"
    }

# uvicorn main:app --host 0.0.0.0 --port $PORT