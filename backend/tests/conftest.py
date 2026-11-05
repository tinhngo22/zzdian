"""Shared fixtures for the service tests.

The service tests talk to the real Postgres from DATABASE_URL (start it with
`docker compose up -d`) and need the reference data imported (radicals, characters).

Isolation: every test gets one connection, the services never commit, and the fixture
always rolls back. So tests leave nothing behind, even on a dev database.
"""
from uuid import uuid4

import pytest


@pytest.fixture
def conn():
    import psycopg

    from app.db import DATABASE_URL

    with psycopg.connect(DATABASE_URL, connect_timeout=5) as c:
        has_reference_data = c.execute("SELECT count(*) FROM characters").fetchone()[0] > 0
        if not has_reference_data:
            pytest.skip("reference data not imported (run the scripts/import_* first)")
        try:
            yield c
        finally:
            c.rollback()


def _make_user(conn):
    return conn.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, 'x') RETURNING id",
        (f"{uuid4()}@test.invalid",),
    ).fetchone()[0]


@pytest.fixture
def user_id(conn):
    return _make_user(conn)


@pytest.fixture
def other_user_id(conn):
    return _make_user(conn)


@pytest.fixture
def set_id(conn, user_id):
    from app.services import sets

    return sets.create_set(conn, user_id, "test set")["id"]


@pytest.fixture
def missing_han_id(conn):
    """A code point in the main CJK block that is NOT in the characters table."""
    row = conn.execute(
        """
        SELECT g FROM generate_series(19968, 40959) g
        WHERE g NOT IN (SELECT id FROM characters) LIMIT 1
        """
    ).fetchone()
    if row is None:
        pytest.skip("every code point in the CJK block is in characters")
    return row[0]


@pytest.fixture
def no_components_id(conn):
    """A Han character that exists but has no rows in character_components."""
    row = conn.execute(
        """
        SELECT c.id FROM characters c
        WHERE c.id BETWEEN 19968 AND 40959
          AND NOT EXISTS (SELECT 1 FROM character_components cc WHERE cc.character_id = c.id)
        ORDER BY c.id LIMIT 1
        """
    ).fetchone()
    if row is None:
        pytest.skip("every character has components")
    return row[0]
