from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, chat, data


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Jobhatch4AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(data.router, prefix="/api/data", tags=["data"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
