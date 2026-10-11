"""Create the screenshot item schema and preserve legacy item rows."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

import sqlalchemy as sa
from alembic import op


revision = "0001_backend_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _tags(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [tag for tag in value if isinstance(tag, str)]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [tag for tag in parsed if isinstance(tag, str)]
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    return []


def _legacy_key(image_url: str | None, item_id: str) -> str:
    basename = PurePosixPath((image_url or "").replace("\\", "/")).name or item_id
    return basename


def _create_supporting_tables() -> None:
    op.create_table(
        "analysis_cache",
        sa.Column("key", sa.String(length=512), primary_key=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )
    op.create_table(
        "llm_usage",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column(
            "item_id",
            sa.String(length=36),
            sa.ForeignKey("items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thinking_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )
    op.create_index("ix_llm_usage_item_id", "llm_usage", ["item_id"])
    op.create_index("ix_llm_usage_created_at", "llm_usage", ["created_at"])


def _create_items_table() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("image_key", sa.String(length=512), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
        sa.Column("mime", sa.String(length=64), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("classifier_score", sa.Float(), nullable=True),
        sa.Column("abstained", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("taxonomy_version", sa.String(length=64), nullable=True),
        sa.Column("classifier_version", sa.String(length=128), nullable=True),
        sa.Column("extractor_model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("user_corrected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed', 'deferred')",
            name="ck_items_status",
        ),
    )
    op.create_index("ix_items_owner_id", "items", ["owner_id"])
    op.create_index("ix_items_status", "items", ["status"])
    op.create_index("ix_items_created_at", "items", ["created_at"])


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "items" not in inspector.get_table_names():
        _create_items_table()
        _create_supporting_tables()
        return

    legacy_table = sa.Table("items", sa.MetaData(), autoload_with=op.get_bind())
    legacy_columns = set(legacy_table.columns.keys())
    if "image_url" not in legacy_columns:
        raise RuntimeError("Unsupported existing items schema; refusing to replace data")

    op.rename_table("items", "items_legacy")
    _create_items_table()
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT * FROM items_legacy")).mappings()
    insert_item = sa.text(
        """INSERT INTO items (
            id, status, image_key, title, description, tags, labels,
            created_at, updated_at
        ) VALUES (
            :id, :status, :image_key, :title, :description, :tags, :labels,
            :created_at, :updated_at
        )"""
    )
    for row in rows:
        item_id = str(row["id"])
        tags = _tags(row.get("tags"))
        category = row.get("category") if "category" in legacy_columns else None
        labels = {"category": category} if category else {}
        has_metadata = bool(row.get("title") or row.get("description") or tags or labels)
        created_at = row.get("created_at") or datetime.now(UTC).isoformat()
        connection.execute(
            insert_item,
            {
                "id": item_id,
                "status": "ready" if has_metadata else "pending",
                "image_key": _legacy_key(row.get("image_url"), item_id),
                "title": row.get("title"),
                "description": row.get("description"),
                "tags": json.dumps(tags),
                "labels": json.dumps(labels),
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
    op.drop_table("items_legacy")
    _create_supporting_tables()


def downgrade() -> None:
    op.drop_table("llm_usage")
    op.drop_table("analysis_cache")
    op.create_table(
        "items_legacy",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT * FROM items")).mappings()
    insert_legacy = sa.text(
        """INSERT INTO items_legacy
            (id, image_url, title, description, category, tags, confidence, created_at)
        VALUES (:id, :image_url, :title, :description, :category, :tags, NULL, :created_at)"""
    )
    for row in rows:
        labels = row["labels"]
        if isinstance(labels, str):
            labels = json.loads(labels)
        key = row["image_key"]
        basename = PurePosixPath(key).name
        connection.execute(
            insert_legacy,
            {
                "id": row["id"],
                "image_url": f"uploads/{basename}",
                "title": row["title"],
                "description": row["description"],
                "category": labels.get("category") if isinstance(labels, dict) else None,
                "tags": ", ".join(_tags(row["tags"])),
                "created_at": row["created_at"],
            },
        )
    op.drop_table("items")
    op.rename_table("items_legacy", "items")
