from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, StringConstraints

from app.deps import get_current_user_id, get_db
from app.services import sets as sets_service

router = APIRouter(prefix="/sets", tags=["sets"])

SetName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Required = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SetIn(BaseModel):
    name: SetName


class AddWordIn(BaseModel):
    simplified: Required
    traditional: str | None = None
    pinyin: str | None = None
    definitions: str | None = None


def require_set(conn, set_id: UUID, user_id: UUID) -> None:
    """404 unless this set exists AND belongs to the caller.

    404 (not 403) on purpose: do not reveal that someone else's set id exists.
    """
    if not sets_service.set_exists_for_user(conn, set_id, user_id):
        raise HTTPException(status_code=404, detail="Set not found")


@router.post("", status_code=201)
def create_set(
    body: SetIn,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    row = sets_service.create_set(conn, user_id, body.name)
    conn.commit()
    return row


@router.get("")
def list_sets(conn=Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return sets_service.list_sets(conn, user_id)


@router.patch("/{set_id}")
def rename_set(
    set_id: UUID,
    body: SetIn,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    row = sets_service.rename_set(conn, user_id, set_id, body.name)
    if row is None:
        raise HTTPException(status_code=404, detail="Set not found")
    conn.commit()
    return row


@router.delete("/{set_id}", status_code=204)
def delete_set(
    set_id: UUID,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    if not sets_service.delete_set(conn, user_id, set_id):
        raise HTTPException(status_code=404, detail="Set not found")
    conn.commit()


@router.get("/{set_id}/words")
def list_set_words(
    set_id: UUID,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    require_set(conn, set_id, user_id)
    total = sets_service.count_words(conn, user_id, set_id)
    items = sets_service.list_words(conn, user_id, set_id, limit, offset)
    return {"total": total, "items": items}


@router.post("/{set_id}/words", status_code=201)
def add_word(
    set_id: UUID,
    body: AddWordIn,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Save a word to the set. It is also linked to each of its characters (and their
    radicals) in the `explore` table, in the same transaction.
    """
    require_set(conn, set_id, user_id)
    row = sets_service.add_word(
        conn,
        user_id,
        set_id,
        body.simplified,
        body.traditional,
        body.pinyin,
        body.definitions,
    )
    conn.commit()
    return row


@router.delete("/{set_id}/words/{word_id}", status_code=204)
def remove_word(
    set_id: UUID,
    word_id: UUID,
    conn=Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    require_set(conn, set_id, user_id)
    if not sets_service.remove_word(conn, user_id, set_id, word_id):
        raise HTTPException(status_code=404, detail="Word not found in set")
    conn.commit()
