"""Assign pre-authentication items to the single configured owner.

Revision ID: 0003_milestone_9_owner
Revises: 0002_milestone_8_fts
"""

from alembic import op


revision = "0003_milestone_9_owner"
down_revision = "0002_milestone_8_fts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE items SET owner_id = 'legacy-owner' WHERE owner_id IS NULL")


def downgrade() -> None:
    op.execute("UPDATE items SET owner_id = NULL WHERE owner_id = 'legacy-owner'")
