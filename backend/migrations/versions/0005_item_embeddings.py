"""Add owner-isolated item embedding storage."""

from alembic import op
import sqlalchemy as sa


revision = "0005_item_embeddings"
down_revision = "0004_user_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "item_embeddings",
        sa.Column("item_id", sa.String(length=36), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("vector", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index("ix_item_embeddings_item_id", "item_embeddings", ["item_id"])
    op.create_index("ix_item_embeddings_model", "item_embeddings", ["model"])


def downgrade() -> None:
    op.drop_index("ix_item_embeddings_model", table_name="item_embeddings")
    op.drop_index("ix_item_embeddings_item_id", table_name="item_embeddings")
    op.drop_table("item_embeddings")
