"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-12-22 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    drink_type = postgresql.ENUM(
        "soft",
        "milkshake",
        "cocktail",
        "other",
        name="drink_type",
        create_type=False,
    )
    drink_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.TEXT(), nullable=False),
        sa.Column("password_hash", sa.TEXT(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_admins_email"),
    )

    op.create_table(
        "drink_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_drink_categories_name"),
    )

    op.create_table(
        "drinks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("description", sa.TEXT()),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("type", drink_type, nullable=False, server_default="other"),
        sa.Column("image_cover", sa.TEXT()),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["drink_categories.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_drinks_category", "drinks", ["category_id"])
    op.create_index("idx_drinks_type", "drinks", ["type"])

    op.create_table(
        "drink_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("drink_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.TEXT(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("position BETWEEN 1 AND 3", name="ck_drink_images_pos"),
        sa.UniqueConstraint("drink_id", "position", name="uq_drink_images_unique"),
        sa.ForeignKeyConstraint(
            ["drink_id"],
            ["drinks.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("guest_name", sa.TEXT(), nullable=False),
        sa.Column("phone", sa.TEXT()),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("drink_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["drink_id"], ["drinks.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("order_id", "drink_id", name="uq_order_drink_once"),
    )
    op.create_index("idx_order_items_order", "order_items", ["order_id"])
    op.create_index("idx_order_items_drink", "order_items", ["drink_id"])


def downgrade() -> None:
    op.drop_index("idx_order_items_drink", table_name="order_items")
    op.drop_index("idx_order_items_order", table_name="order_items")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("drink_images")
    op.drop_index("idx_drinks_type", table_name="drinks")
    op.drop_index("idx_drinks_category", table_name="drinks")
    op.drop_table("drinks")
    op.drop_table("drink_categories")
    op.drop_table("admins")
    drink_type = postgresql.ENUM(
        "soft", "milkshake", "cocktail", "other", name="drink_type"
    )
    drink_type.drop(op.get_bind(), checkfirst=True)
