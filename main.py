import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
import uvicorn
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/signup", status_code=201)
async def signup(request: SignupRequest):
    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        response = supabase.auth.sign_up({"email": request.email, "password": request.password})
        return {"id": response.user.id, "email": response.user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
async def login(request: LoginRequest):
    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


def get_token(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Access token required")
    
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Access token required")
    
    return parts[1].strip()


@app.get("/public/info")
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
async def protected_profile(token: str = Depends(get_token)):
    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if response is None or response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = response.user
    return {"id": user.id, "email": user.email, "created_at": user.created_at}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)