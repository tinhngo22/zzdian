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


def fetch_components_by_character_ids(conn, ids: list[int]) -> dict[int, list[dict]]:
    """Components of each character, in position order (a component can repeat, as in 林).

    Characters without a decomposition are absent from the result.
    """
    if not ids:
        return {}
    rows = fetch_all(
        conn,
        """
        SELECT cc.character_id, cc.position, cc.role, c.id, c.glyph, c.pinyin, c.meaning_en
        FROM character_components cc
        JOIN characters c ON c.id = cc.component_id
        WHERE cc.character_id = ANY(%s)
        ORDER BY cc.character_id, cc.position
        """,
        (ids,),
    )
    by_character: dict[int, list[dict]] = {}
    for row in rows:
        by_character.setdefault(row.pop("character_id"), []).append(row)
    return by_character


def characters_in_word(conn, character_ids: list[int]) -> list[dict]:
    """Look up each *unique* character id of a word, given in word order (妈妈 -> just 妈).

    Returns one entry per distinct id, in order of first appearance:
        {"id": 22909, "glyph": "好", "is_hanzi": True,
         "character": {..., "components": [...]} | None}

    - non-Han code points (letters, digits, punctuation) get is_hanzi=False and
      character=None, and never reach the database
    - a Han character missing from the table gets is_hanzi=True, character=None
    - `components` is the character's breakdown from character_components; empty for
      characters that do not decompose (人, 女, ...)
    """
    unique_ids = list(dict.fromkeys(character_ids))  # keeps first-appearance order
    han_ids = [i for i in unique_ids if is_hanzi(chr(i))]
    by_id = {row["id"]: row for row in fetch_characters_by_ids(conn, han_ids)}
    components = fetch_components_by_character_ids(conn, list(by_id))
    for character_id, character in by_id.items():
        character["components"] = components.get(character_id, [])

    return [
        {
            "id": i,
            "glyph": chr(i),
            "is_hanzi": is_hanzi(chr(i)),
            "character": by_id.get(i),
        }
        for i in unique_ids
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


def fetch_words_with_component(conn, user_id: UUID, component_id: int) -> list[dict]:
    """All the user's saved words containing a character built from this component
    (distinct simplified). A character counts as its own component, so 女 also matches
    words that contain 女 itself. Empty if the id is unknown.
    """
    return fetch_all(
        conn,
        """
        SELECT DISTINCT ON (fw.simplified)
               fw.id, fw.simplified, fw.traditional, fw.pinyin, fw.definitions, fw.added_at
        FROM explore e
        JOIN flashcard_words fw ON fw.id = e.word_id
        WHERE e.user_id = %s AND e.component_id = %s
        ORDER BY fw.simplified, fw.added_at, fw.id
        """,
        (user_id, component_id),
    )
