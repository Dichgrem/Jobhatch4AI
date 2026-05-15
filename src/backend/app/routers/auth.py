from fastapi import APIRouter, HTTPException
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth import authenticate, register, remove_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    token = authenticate(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(access_token=token, username=req.username)


@router.post("/register", response_model=TokenResponse)
async def register_user(req: RegisterRequest):
    token = register(req.username, req.password)
    if not token:
        raise HTTPException(status_code=409, detail="用户名已存在")
    return TokenResponse(access_token=token, username=req.username)


@router.post("/logout")
async def logout(token: str):
    remove_token(token)
    return {"status": "ok"}
