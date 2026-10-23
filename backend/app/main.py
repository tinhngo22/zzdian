from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.db import pool
from app.deps import get_db
from app.routers import dictionary, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()      
    yield
    pool.close()  


app = FastAPI(title="Hanzi App", lifespan=lifespan)


app.include_router(dictionary.router)
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(conn=Depends(get_db)):
    row = conn.execute("SELECT 1").fetchone()
    return {"db": row[0]}

