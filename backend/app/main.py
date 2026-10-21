from fastapi import FastAPI
from app.db import get_conn


app = FastAPI(title="My Hanzi App")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/health/db")
def health_db():
    with get_conn() as conn:
        row = conn.execute("SELECT 1").fetchone()
    return {"db": row[0]}