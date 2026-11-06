from collections.abc import Iterator

import psycopg
from app.db import pool

from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import decode_access_claims


def get_db() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: lend one pooled connection to a request."""
    with pool.connection() as conn:
        yield conn


bearer_scheme = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    conn=Depends(get_db),
) -> UUID:
    """Read 'Authorization: Bearer <token>' and return the user's id.
    """
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    claims = decode_access_claims(credentials.credentials)
    if claims is None:
        raise unauthorized
    try:
        user_id = UUID(claims["sub"])
    except (ValueError, TypeError):
        raise unauthorized
    row = conn.execute("SELECT token_version FROM users WHERE id = %s", (user_id,)).fetchone()
    if row is None or row[0] != claims["ver"]:
        raise unauthorized
    return user_id
