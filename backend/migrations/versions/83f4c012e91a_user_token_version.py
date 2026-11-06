"""Revoke existing sessions when an administrator resets a password."""
from alembic import op

revision = "83f4c012e91a"
down_revision = "609bb6b11ba5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0 CHECK (token_version >= 0)")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN token_version")
