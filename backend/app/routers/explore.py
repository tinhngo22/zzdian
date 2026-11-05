from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field

from app.deps import get_current_user_id, get_db
from app.services import explore as explore_service

router = APIRouter(prefix="/explore", tags=["explore"])

# characters.id is the Unicode code point, e.g. 好 = 22909
MAX_CODE_POINT = 0x10FFFF
CodePoint = Annotated[int, Field(ge=0, le=MAX_CODE_POINT)]
CharacterId = Query(
    ..., ge=0, le=MAX_CODE_POINT, description="characters.id (Unicode code point)"
)


@router.get("/characters")
def get_word_characters(
    character_id: list[CodePoint] = Query(
        ...,
        min_length=1,
        max_length=50,
        description="characters.id of each character of the word, in order (repeat the param)",
    ),
    conn=Depends(get_db),
):
    """Character info and component breakdown for each unique id, in order of first
    appearance.

    Example: GET /explore/characters?character_id=20320&character_id=22909   (你好)
    """
    return {
        "character_ids": character_id,
        "characters": explore_service.characters_in_word(conn, character_id),
    }


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


@router.get("/words/by-component")
def get_words_by_component(
    component_id: int = Query(
        ..., ge=0, le=MAX_CODE_POINT, description="characters.id of the component"
    ),
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Your saved words containing a character built from this component, including
    the component itself (distinct simplified).

    Example: GET /explore/words/by-component?component_id=22899   (女)
    """
    return {
        "component_id": component_id,
        "words": explore_service.fetch_words_with_component(conn, user_id, component_id),
    }
