from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone

from app.config import OWNER_PASSWORD, JWT_SECRET

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

@router.post("/auth/login")
async def login(request: LoginRequest):
    if request.password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    payload = {
        "sub": "owner",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token}
