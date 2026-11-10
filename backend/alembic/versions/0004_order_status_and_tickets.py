"""order status and daily ticket numbers

Revision ID: 0004_order_status_and_tickets
Revises: 0003_item_masters
Create Date: 2026-11-10 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_order_status_and_tickets"
down_revision = "0003_item_masters"
branch_labels = None
depends_on = None

ORDER_STATUS = postgresql.ENUM(
    "pending", "accepted", "ready", "completed", "cancelled", name="order_status"
)


def upgrade() -> None:
    ORDER_STATUS.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "orders",
        sa.Column(
            "status",
            postgresql.ENUM(name="order_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column("orders", sa.Column("ticket_number", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("ticket_date", sa.DATE(), nullable=True))
    for col in ("accepted_at", "ready_at", "completed_at", "cancelled_at"):
        op.add_column("orders", sa.Column(col, sa.TIMESTAMP(), nullable=True))

    # Orders placed before this migration had no lifecycle. Treat them as
    # completed and number them per day in the order they came in.
    op.execute(
        """
        UPDATE orders o
        SET status = 'completed',
            completed_at = o.created_at,
            ticket_date = o.created_at::date,
            ticket_number = sub.n
        FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY created_at::date ORDER BY created_at, id
            ) AS n
            FROM orders
        ) sub
        WHERE o.id = sub.id
        """
    )

    op.alter_column("orders", "ticket_number", nullable=False)
    op.alter_column("orders", "ticket_date", nullable=False)
    op.create_unique_constraint(
        "uq_orders_ticket_per_day", "orders", ["ticket_date", "ticket_number"]
    )
    op.create_index("idx_orders_status", "orders", ["status"])


def downgrade() -> None:
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_constraint("uq_orders_ticket_per_day", "orders", type_="unique")
    for col in (
        "cancelled_at", "completed_at", "ready_at", "accepted_at",
        "ticket_date", "ticket_number", "status",
    ):
        op.drop_column("orders", col)
    ORDER_STATUS.drop(op.get_bind(), checkfirst=True)
