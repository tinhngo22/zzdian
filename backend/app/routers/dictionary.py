from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.deps import get_db
from app.services import dictionary as dictionary_service
# from app.services import search as search_service

router = APIRouter(tags=["dictionary"])

# Dictionary data barely changes, so clients and CDNs may cache these responses.
CACHE_HEADER = "public, max-age=3600"


# @router.get("/search")
# def search(
#     q: str = Query(..., min_length=1, max_length=50),
#     limit: int = Query(20, ge=1, le=50),
#     conn=Depends(get_db),
# ):
#     return search_service.search(conn, q, limit)


# @router.get("/words/{word_id}")
# def get_word(word_id: int, response: Response, conn=Depends(get_db)):
#     word = dictionary_service.fetch_word(conn, word_id)
#     if word is None:
#         raise HTTPException(status_code=404, detail="Word not found")
#     word["characters"] = dictionary_service.fetch_word_characters(conn, word_id)
#     response.headers["Cache-Control"] = CACHE_HEADER
#     return word


@router.get("/words")
def lookup_words(
    response: Response,
    simplified: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(20, ge=1, le=50),
    conn=Depends(get_db),
):
    """Reference dictionary entries for an exact simplified word; `entries` is empty
    when the word is not in the dictionary.

    Example: GET /words?simplified=好
    """
    simplified = simplified.strip()
    entries = (
        dictionary_service.fetch_words_by_simplified(conn, simplified, limit)
        if simplified
        else []
    )
    response.headers["Cache-Control"] = CACHE_HEADER
    return {"simplified": simplified, "entries": entries}


def _character_detail(conn, character_id: int) -> dict | None:
    char = dictionary_service.fetch_character(conn, character_id)
    if char is None:
        return None
    radical_id = char.pop("main_radical_id")
    char["main_radical"] = (
        dictionary_service.fetch_radical(conn, radical_id) if radical_id else None
    )
    char["components"] = dictionary_service.fetch_components(conn, character_id)
    return char


@router.get("/characters/{character_id}")
def get_character(character_id: int, response: Response, conn=Depends(get_db)):
    char = _character_detail(conn, character_id)
    if char is None:
        raise HTTPException(status_code=404, detail="Character not found")
    response.headers["Cache-Control"] = CACHE_HEADER
    return char


@router.get("/characters/glyph/{glyph}")
def get_character_by_glyph(glyph: str, response: Response, conn=Depends(get_db)):
    if len(glyph) != 1:
        raise HTTPException(status_code=400, detail="Provide exactly one character")
    char = _character_detail(conn, ord(glyph))   # id is the Unicode code point
    if char is None:
        raise HTTPException(status_code=404, detail="Character not found")
    response.headers["Cache-Control"] = CACHE_HEADER
    return char