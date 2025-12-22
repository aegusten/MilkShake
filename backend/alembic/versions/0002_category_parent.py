"""add category parent

Revision ID: 0002_category_parent
Revises: 0001_init
Create Date: 2025-12-22 01:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_category_parent"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("drink_categories", sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_drink_categories_parent",
        "drink_categories",
        "drink_categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_drink_categories_parent", "drink_categories", ["parent_id"])


def downgrade() -> None:
    op.drop_index("idx_drink_categories_parent", table_name="drink_categories")
    op.drop_constraint("fk_drink_categories_parent", "drink_categories", type_="foreignkey")
    op.drop_column("drink_categories", "parent_id")
