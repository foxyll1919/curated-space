"""Add a Clerk identity mapping without changing item ownership IDs."""

from alembic import op
import sqlalchemy as sa


revision = "0006_clerk_user_mapping"
down_revision = "0005_item_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("clerk_user_id", sa.String(length=128), nullable=True))
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_column("users", "clerk_user_id")
