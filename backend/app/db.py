import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

pool = ConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=10,
    open=False,
    kwargs={"prepare_threshold": None},
)


def get_conn() -> psycopg.Connection:
    """A standalone connection, for scripts and tests. Use as a context manager."""
    return psycopg.connect(DATABASE_URL)


def fetch_all(conn, sql, params=None) -> list[dict]:
    """Run a query, return all rows as dicts."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(conn, sql, params=None) -> dict | None:
    """Run a query, return the first row as a dict (or None)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone()