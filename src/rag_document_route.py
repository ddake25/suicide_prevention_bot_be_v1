from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter()

@router.post("/send")
def process_chat():
    
    return {
        "payload": "Chuncking Successful!"
    }

