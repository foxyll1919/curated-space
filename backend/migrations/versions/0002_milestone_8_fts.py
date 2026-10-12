"""Add a synchronized FTS5 index for searchable item metadata."""

from alembic import op


revision = "0002_milestone_8_fts"
down_revision = "0001_backend_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE VIRTUAL TABLE item_fts USING fts5(item_id UNINDEXED, title, description, tags)"
    )
    op.execute(
        """INSERT INTO item_fts (item_id, title, description, tags)
           SELECT id, coalesce(title, ''), coalesce(description, ''), coalesce(tags, '')
           FROM items"""
    )
    op.execute(
        """CREATE TRIGGER items_fts_insert AFTER INSERT ON items BEGIN
             INSERT INTO item_fts (item_id, title, description, tags)
             VALUES (new.id, coalesce(new.title, ''), coalesce(new.description, ''), coalesce(new.tags, ''));
           END"""
    )
    op.execute(
        """CREATE TRIGGER items_fts_delete AFTER DELETE ON items BEGIN
             DELETE FROM item_fts WHERE item_id = old.id;
           END"""
    )
    op.execute(
        """CREATE TRIGGER items_fts_update AFTER UPDATE OF title, description, tags ON items BEGIN
             DELETE FROM item_fts WHERE item_id = old.id;
             INSERT INTO item_fts (item_id, title, description, tags)
             VALUES (new.id, coalesce(new.title, ''), coalesce(new.description, ''), coalesce(new.tags, ''));
           END"""
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS items_fts_update")
    op.execute("DROP TRIGGER IF EXISTS items_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS items_fts_insert")
    op.execute("DROP TABLE IF EXISTS item_fts")
