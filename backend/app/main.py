import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import pool
from app.deps import get_db
from app.middleware import RequestSizeLimitMiddleware
from app.routers import sets, dictionary, auth, explore

# Comma-separated browser origins allowed to call the API (the Vite dev server by default).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        pool.open(wait=True, timeout=10)
        yield
    finally:
        pool.close()


app = FastAPI(title="Hanzi App", lifespan=lifespan)
app.add_middleware(RequestSizeLimitMiddleware)

# Auth is a bearer token in the Authorization header, not a cookie, so no credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(dictionary.router)
app.include_router(auth.router)
app.include_router(sets.router)
app.include_router(explore.router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(conn=Depends(get_db)):
    row = conn.execute("SELECT 1").fetchone()
    return {"db": row[0]}

