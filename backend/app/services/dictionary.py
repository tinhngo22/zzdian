from __future__ import annotations
from app.db import fetch_all, fetch_one


def fetch_character(conn, character_id: int) -> dict | None:
    return fetch_one(
        conn,
        """
        SELECT id, glyph, pinyin, meaning_en, stroke_count, main_radical_id
        FROM characters WHERE id = %s
        """,
        (character_id,),
    )


def fetch_radical(conn, radical_id: int) -> dict | None:
    return fetch_one(
        conn,
        "SELECT id, glyph, pinyin, meaning_en, stroke_count FROM radicals WHERE id = %s",
        (radical_id,),
    )


def fetch_components(conn, character_id: int) -> list[dict]:
    """The components of a character, in order (a component can repeat, as in 林)."""
    return fetch_all(
        conn,
        """
        SELECT cc.position, cc.role, c.id, c.glyph, c.pinyin, c.meaning_en
        FROM character_components cc
        JOIN characters c ON c.id = cc.component_id
        WHERE cc.character_id = %s
        ORDER BY cc.position
        """,
        (character_id,),
    )