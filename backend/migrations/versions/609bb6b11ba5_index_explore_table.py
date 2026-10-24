"""index explore table

Revision ID: 609bb6b11ba5
Revises: 364375fc78f7
Create Date: 2026-10-24 00:07:06.469492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '609bb6b11ba5'
down_revision: Union[str, None] = '364375fc78f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STATEMENTS = [
    # Target for the composite foreign key below, so that explore.user_id can never
    # disagree with the owner of the word (same trick as uq_sets_id_user).
    "ALTER TABLE flashcard_words ADD CONSTRAINT uq_words_id_user UNIQUE (id, user_id)",

    # Links a user's saved word to each of its characters and that character's radical.
    # user_id is stored here too so the explore queries can filter by user straight from
    # the index, without first joining to flashcard_words.
    """
    CREATE TABLE explore (
        user_id       UUID     NOT NULL,
        radical_id    SMALLINT NOT NULL REFERENCES radicals(id),
        character_id  INT      NOT NULL REFERENCES characters(id),
        word_id       UUID     NOT NULL,
        PRIMARY KEY (word_id, character_id, radical_id),
        FOREIGN KEY (word_id, user_id)
            REFERENCES flashcard_words (id, user_id) ON DELETE CASCADE
    )
    """,
    # "words with this character":  WHERE user_id = ? AND character_id = ?
    "CREATE INDEX idx_explore_user_character_word ON explore (user_id, character_id, word_id)",
    # "words with this radical":    WHERE user_id = ? AND radical_id = ?
    "CREATE INDEX idx_explore_user_radical_word ON explore (user_id, radical_id, word_id)",
]


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # dropping the table also drops its indexes
    op.execute("DROP TABLE explore")
    op.execute("ALTER TABLE flashcard_words DROP CONSTRAINT uq_words_id_user")
