"""guest name is optional

Revision ID: 0005_orders_guest_name_nullable
Revises: 0004_order_status_and_tickets
Create Date: 2026-11-10 12:05:00.000000
"""
from alembic import op

revision = "0005_orders_guest_name_nullable"
down_revision = "0004_order_status_and_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("orders", "guest_name", nullable=True)


def downgrade() -> None:
    op.execute("UPDATE orders SET guest_name = 'Guest' WHERE guest_name IS NULL")
    op.alter_column("orders", "guest_name", nullable=False)
