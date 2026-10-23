from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.db import fetch_one
from app.deps import get_current_user_id, get_db
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterIn, conn=Depends(get_db)):
    email = body.email.lower()
    try:
        with conn.transaction():
            row = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, hash_password(body.password)),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered")
    conn.commit()
    return {"id": str(row[0]), "email": email}


@router.post("/login")
def login(body: LoginIn, conn=Depends(get_db)):
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE lower(email) = %s",
        (body.email.lower(),),
    ).fetchone()
    
    if row is None or not verify_password(row[1], body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(str(row[0])), "token_type": "bearer"}


@router.get("/me")
def me(conn=Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    user = fetch_one(
        conn, "SELECT id, email, created_at FROM users WHERE id = %s", (user_id,)
    )
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user