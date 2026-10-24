from __future__ import annotations
from uuid import UUID

from app.db import fetch_all

# Unicode blocks that hold Han characters (what the `characters` table contains).
_HAN_RANGES = (
    (0x3400, 0x4DBF),    # CJK Extension A
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
    (0x20000, 0x323AF),  # CJK Extensions B-H
)


def is_hanzi(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _HAN_RANGES)


def fetch_characters_by_ids(conn, ids: list[int]) -> list[dict]:
    """get infos of characters by a list of ids"""
    if not ids:
        return []
    return fetch_all(
        conn,
        """
        SELECT id, glyph, pinyin, meaning_en, stroke_count, main_radical_id
        FROM characters
        WHERE id = ANY(%s)
        """,
        (ids,),
    )


def characters_in_word(conn, word: str) -> list[dict]:
    """Look up each *unique* character of `word` (妈妈 -> just 妈).

    Returns one entry per distinct character, in order of first appearance:
        {"glyph": "好", "is_hanzi": True, "character": {...} | None}

    - non-Han characters (letters, digits, punctuation) get is_hanzi=False and
      character=None, and never reach the database
    - a Han character missing from the table gets is_hanzi=True, character=None
    """
    glyphs = list(dict.fromkeys(word))  # unique, keeps first-appearance order
    ids = [ord(ch) for ch in glyphs if is_hanzi(ch)]
    by_id = {row["id"]: row for row in fetch_characters_by_ids(conn, ids)}

    return [
        {
            "glyph": ch,
            "is_hanzi": is_hanzi(ch),
            "character": by_id.get(ord(ch)),
        }
        for ch in glyphs
    ]


# Both queries below return each distinct `simplified` once (DISTINCT ON); when the
# user saved the same simplified word several times, the earliest-added row wins.
# They only look at the caller's own flashcard_words.

def fetch_words_with_character(conn, user_id: UUID, character_id: int) -> list[dict]:
    """All the user's saved words that contain this character (distinct simplified)."""
    return fetch_all(
        conn,
        """
        SELECT DISTINCT ON (fw.simplified)
               fw.id, fw.simplified, fw.traditional, fw.pinyin, fw.definitions, fw.added_at
        FROM explore e
        JOIN flashcard_words fw ON fw.id = e.word_id
        WHERE e.user_id = %s AND e.character_id = %s
        ORDER BY fw.simplified, fw.added_at, fw.id
        """,
        (user_id, character_id),
    )


def fetch_words_with_same_radical(conn, user_id: UUID, character_id: int) -> list[dict]:
    """All the user's saved words containing a character that shares this character's
    main radical (distinct simplified). Empty if the character is unknown or has no
    main radical.
    """
    return fetch_all(
        conn,
        """
        SELECT DISTINCT ON (fw.simplified)
               fw.id, fw.simplified, fw.traditional, fw.pinyin, fw.definitions, fw.added_at
        FROM explore e
        JOIN flashcard_words fw ON fw.id = e.word_id
        WHERE e.user_id = %s
          AND e.radical_id = (SELECT main_radical_id FROM characters WHERE id = %s)
        ORDER BY fw.simplified, fw.added_at, fw.id
        """,
        (user_id, character_id),
    )
