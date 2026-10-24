from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user_id, get_db
from app.services import explore as explore_service

router = APIRouter(prefix="/explore", tags=["explore"])

# characters.id is the Unicode code point, e.g. 好 = 22909
CharacterId = Query(..., ge=0, description="characters.id (Unicode code point)")


@router.get("/characters")
def get_word_characters(
    word: str = Query(..., min_length=1, max_length=50),
    conn=Depends(get_db),
):
    """Character info for each unique character in `word`, in order of first appearance.

    Example: GET /explore/characters?word=你好
    """
    return {"word": word, "characters": explore_service.characters_in_word(conn, word)}


@router.get("/words/by-character")
def get_words_by_character(
    character_id: int = CharacterId,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Your saved words containing this character (distinct simplified).

    Example: GET /explore/words/by-character?character_id=22909
    """
    return {
        "character_id": character_id,
        "words": explore_service.fetch_words_with_character(conn, user_id, character_id),
    }


@router.get("/words/by-radical")
def get_words_by_radical(
    character_id: int = CharacterId,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Your saved words containing a character with the same main radical as this
    character (distinct simplified).

    Example: GET /explore/words/by-radical?character_id=22909
    """
    return {
        "character_id": character_id,
        "words": explore_service.fetch_words_with_same_radical(
            conn, user_id, character_id
        ),
    }
