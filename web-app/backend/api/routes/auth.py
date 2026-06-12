from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.security import create_access_token

router = APIRouter()

# TODO: Replace with real database
MOCK_USER = {"username": "admin", "password": "admin123"}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    # TODO: Query user from DB and verify hashed password
    if data.username != MOCK_USER["username"] or data.password != MOCK_USER["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": data.username})
    return {"access_token": token, "token_type": "bearer"}
