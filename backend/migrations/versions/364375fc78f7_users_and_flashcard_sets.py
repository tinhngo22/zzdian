"""users and flashcard sets

Revision ID: 364375fc78f7
Revises: 951d7229445d
Create Date: 2026-10-23 14:15:07.492964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '364375fc78f7'
down_revision: Union[str, None] = '951d7229445d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STATEMENTS = [
    # gen_random_uuid() is built into Postgres 13+
    """
    CREATE TABLE users (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email          TEXT NOT NULL,
        password_hash  TEXT NOT NULL,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE UNIQUE INDEX uq_users_email ON users (lower(email))",

    """
    CREATE TABLE flashcard_sets (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name        TEXT NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_sets_id_user UNIQUE (id, user_id)
    )
    """,
    "CREATE INDEX idx_sets_user ON flashcard_sets (user_id)",

    # The user's library: one row per (user, word), however many sets it is in.
    """
    CREATE TABLE flashcard_words (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        set_id         UUID NOT NULL REFERENCES flashcard_sets(id) ON DELETE CASCADE,
        added_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
        simplified      TEXT NOT NULL,
        traditional     TEXT,
        pinyin          TEXT,              
        definitions     TEXT
    )
    """,
    "CREATE INDEX idx_set_words ON flashcard_words (user_id, set_id)",

   
]


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TABLE flashcard_words")
    op.execute("DROP TABLE flashcard_sets")
    op.execute("DROP TABLE users")
