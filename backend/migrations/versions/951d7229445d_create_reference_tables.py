"""create reference tables

Revision ID: 951d7229445d
Revises: 
Create Date: 2026-10-21 17:19:12.098119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '951d7229445d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op

STATEMENTS = [
    # --- radicals: the 214 Kangxi radicals ---
    """
    CREATE TABLE radicals (
        id            SMALLINT PRIMARY KEY,         -- Kangxi number, 1 to 214
        glyph         TEXT NOT NULL UNIQUE,
        pinyin        TEXT,
        meaning_en    TEXT,
        stroke_count  SMALLINT
    )
    """,
    # --- characters: id is the Unicode code point, so ids are stable forever ---
    """
    CREATE TABLE characters (
        id               INT PRIMARY KEY,
        glyph            TEXT NOT NULL UNIQUE,
        pinyin           TEXT[] NOT NULL DEFAULT '{}',
        meaning_en       TEXT,
        stroke_count     SMALLINT,
        main_radical_id  SMALLINT REFERENCES radicals(id),
        frequency_rank   INT
    )
    """,
    # --- components of a character, in order ---
    """
    CREATE TABLE character_components (
        character_id  INT NOT NULL REFERENCES characters(id),
        position      SMALLINT NOT NULL,
        component_id  INT NOT NULL REFERENCES characters(id),
        role          TEXT NOT NULL DEFAULT 'component',
        PRIMARY KEY (character_id, position)
    )
    """,
    "CREATE INDEX idx_cc_component ON character_components (component_id)",
    # --- words ---
    """
    CREATE TABLE words (
        id               INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        simplified       TEXT NOT NULL,
        traditional      TEXT NOT NULL,
        pinyin           TEXT NOT NULL,              -- tone marks: nǐ hǎo
        pinyin_numbered  TEXT NOT NULL,              -- as in CEDICT: ni3 hao3
        pinyin_plain     TEXT NOT NULL,              -- for search: ni hao
        definitions      JSONB NOT NULL DEFAULT '[]',
        hsk_level        SMALLINT,
        frequency_rank   INT,
        is_custom        BOOLEAN NOT NULL DEFAULT FALSE,
        created_by       UUID,
        CONSTRAINT uq_word_entry UNIQUE (traditional, simplified, pinyin_numbered)
    )
    """,
    "CREATE INDEX idx_words_simplified ON words (simplified)",
    "CREATE INDEX idx_words_traditional ON words (traditional)",
    # --- which characters each word contains, in order ---
    """
    CREATE TABLE word_characters (
        word_id       INT NOT NULL REFERENCES words(id),
        position      SMALLINT NOT NULL,
        character_id  INT NOT NULL REFERENCES characters(id),
        PRIMARY KEY (word_id, position)
    )
    """,
    "CREATE INDEX idx_wc_character ON word_characters (character_id, word_id)",
]


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # reverse order of creation (tables that depend on others go first)
    op.execute("DROP TABLE word_characters")
    op.execute("DROP TABLE words")
    op.execute("DROP TABLE character_components")
    op.execute("DROP TABLE characters")
    op.execute("DROP TABLE radicals")
