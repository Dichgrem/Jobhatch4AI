from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []


class TokenResponse(BaseModel):
    access_token: str
    username: str
