from collections.abc import Iterator

import psycopg
from app.db import pool

from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import decode_access_token


def get_db() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: lend one pooled connection to a request."""
    with pool.connection() as conn:
        yield conn


bearer_scheme = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    """Read 'Authorization: Bearer <token>' and return the user's id.
    """
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    try:
        return UUID(user_id)
    except ValueError:
        raise unauthorized