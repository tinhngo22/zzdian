"""SQL for flashcard sets and the words inside them.

Tables (see migrations 364375fc78f7 and 609bb6b11ba5):
  flashcard_sets  (id, user_id, name, created_at)
  flashcard_words (id, user_id, set_id, added_at, simplified, traditional, pinyin, definitions)
  explore         (user_id, radical_id, character_id, word_id)  -- one row per character of a word

Deleting a word (or its set) also deletes its `explore` rows: the foreign keys are
ON DELETE CASCADE all the way down.

Functions here never commit; the router owns the transaction.
"""
from __future__ import annotations

from uuid import UUID

from app.db import fetch_all, fetch_one


# ---------- sets ----------

def set_exists_for_user(conn, set_id: UUID, user_id: UUID) -> bool:
    row = fetch_one(
        conn,
        "SELECT 1 AS ok FROM flashcard_sets WHERE id = %s AND user_id = %s",
        (set_id, user_id),
    )
    return row is not None


def create_set(conn, user_id: UUID, name: str) -> dict:
    return fetch_one(
        conn,
        """
        INSERT INTO flashcard_sets (user_id, name)
        VALUES (%s, %s)
        RETURNING id, name, created_at
        """,
        (user_id, name),
    )


def list_sets(conn, user_id: UUID) -> list[dict]:
    return fetch_all(
        conn,
        """
        SELECT s.id, s.name, s.created_at, count(fw.id) AS word_count
        FROM flashcard_sets s
        LEFT JOIN flashcard_words fw ON fw.set_id = s.id
        WHERE s.user_id = %s
        GROUP BY s.id
        ORDER BY s.created_at, s.id
        """,
        (user_id,),
    )


def rename_set(conn, user_id: UUID, set_id: UUID, name: str) -> dict | None:
    """Return the updated set, or None if it does not exist / is not the caller's."""
    return fetch_one(
        conn,
        """
        UPDATE flashcard_sets SET name = %s
        WHERE id = %s AND user_id = %s
        RETURNING id, name, created_at
        """,
        (name, set_id, user_id),
    )


def delete_set(conn, user_id: UUID, set_id: UUID) -> bool:
    """Delete a set (its words go with it via ON DELETE CASCADE).

    Returns False if nothing was deleted.
    """
    row = fetch_one(
        conn,
        "DELETE FROM flashcard_sets WHERE id = %s AND user_id = %s RETURNING id",
        (set_id, user_id),
    )
    return row is not None


# ---------- words in a set ----------

def count_words(conn, user_id: UUID, set_id: UUID) -> int:
    row = fetch_one(
        conn,
        "SELECT count(*) AS total FROM flashcard_words WHERE set_id = %s AND user_id = %s",
        (set_id, user_id),
    )
    return row["total"]


def list_words(
    conn, user_id: UUID, set_id: UUID, limit: int, offset: int
) -> list[dict]:
    return fetch_all(
        conn,
        """
        SELECT id, simplified, traditional, pinyin, definitions, added_at
        FROM flashcard_words
        WHERE set_id = %s AND user_id = %s
        ORDER BY added_at, id
        LIMIT %s OFFSET %s
        """,
        (set_id, user_id, limit, offset),
    )


def add_word(
    conn,
    user_id: UUID,
    set_id: UUID,
    simplified: str,
    traditional: str | None,
    pinyin: str | None,
    definitions: str | None,
) -> dict:
    """Insert the word, and link it to each of its characters in `explore`."""
    word = fetch_one(
        conn,
        """
        INSERT INTO flashcard_words
            (user_id, set_id, simplified, traditional, pinyin, definitions)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, simplified, traditional, pinyin, definitions, added_at
        """,
        (user_id, set_id, simplified, traditional, pinyin, definitions),
    )
    link_word_characters(conn, user_id, word["id"], simplified)
    return word


def link_word_characters(conn, user_id: UUID, word_id: UUID, simplified: str) -> None:
    """Fill `explore` with one row per distinct character of `simplified`.

    characters.id is the Unicode code point, so we look characters up by ord(ch);
    anything not in `characters` (letters, punctuation, unknown hanzi) is skipped
    by the join, and so are characters with no main radical (radical_id is NOT NULL).
    """
    ids = sorted({ord(ch) for ch in simplified})
    conn.execute(
        """
        INSERT INTO explore (user_id, radical_id, character_id, word_id)
        SELECT %s, c.main_radical_id, c.id, %s
        FROM characters c
        WHERE c.id = ANY(%s) AND c.main_radical_id IS NOT NULL
        """,
        (user_id, word_id, ids),
    )


def remove_word(conn, user_id: UUID, set_id: UUID, word_id: UUID) -> bool:
    """Returns False if no such word in this caller's set."""
    row = fetch_one(
        conn,
        """
        DELETE FROM flashcard_words
        WHERE id = %s AND set_id = %s AND user_id = %s
        RETURNING id
        """,
        (word_id, set_id, user_id),
    )
    return row is not None
