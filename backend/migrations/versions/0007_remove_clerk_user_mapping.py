"""Remove Clerk user mapping column and index."""

from alembic import op
import sqlalchemy as sa


revision = "0007_remove_clerk_user_mapping"
down_revision = "0006_clerk_user_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_clerk_user_id")
        batch_op.drop_column("clerk_user_id")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("clerk_user_id", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_users_clerk_user_id", ["clerk_user_id"], unique=True)
