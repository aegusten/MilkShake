"""refactor categories into item masters

Revision ID: 0003_item_masters
Revises: 0002_category_parent
Create Date: 2025-12-22 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_item_masters"
down_revision = "0002_category_parent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "item_masters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_item_masters_name"),
    )

    op.create_table(
        "item_master_drinks",
        sa.Column("item_master_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("drink_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["item_master_id"],
            ["item_masters.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["drink_id"],
            ["drinks.id"],
            ondelete="CASCADE",
        ),
    )

    op.execute(
        """
        INSERT INTO item_masters (id, name, sort_order, created_at)
        SELECT id, name, sort_order, created_at FROM drink_categories
        """
    )
    op.execute(
        """
        INSERT INTO item_master_drinks (item_master_id, drink_id)
        SELECT category_id, id FROM drinks
        """
    )

    op.drop_constraint("drinks_category_id_fkey", "drinks", type_="foreignkey")
    op.drop_index("idx_drinks_category", table_name="drinks")
    op.drop_column("drinks", "category_id")

    op.drop_index("idx_drink_categories_parent", table_name="drink_categories")
    op.drop_constraint("fk_drink_categories_parent", "drink_categories", type_="foreignkey")
    op.drop_table("drink_categories")


def downgrade() -> None:
    op.create_table(
        "drink_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_drink_categories_name"),
    )
    op.create_foreign_key(
        "fk_drink_categories_parent",
        "drink_categories",
        "drink_categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_drink_categories_parent", "drink_categories", ["parent_id"])

    op.execute(
        """
        INSERT INTO drink_categories (id, name, sort_order, created_at)
        SELECT id, name, sort_order, created_at FROM item_masters
        """
    )

    op.add_column("drinks", sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE drinks d
        SET category_id = sub.item_master_id
        FROM (
            SELECT drink_id, MIN(item_master_id) AS item_master_id
            FROM item_master_drinks
            GROUP BY drink_id
        ) sub
        WHERE d.id = sub.drink_id
        """
    )
    op.alter_column("drinks", "category_id", nullable=False)
    op.create_foreign_key(
        "drinks_category_id_fkey",
        "drinks",
        "drink_categories",
        ["category_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_drinks_category", "drinks", ["category_id"])

    op.drop_table("item_master_drinks")
    op.drop_table("item_masters")
