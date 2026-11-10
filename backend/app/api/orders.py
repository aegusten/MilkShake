from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin_catalog import require_admin
from app.db import get_db
from app.models.order import Order
from app.schemas.order import (
    DisplayTicketOut,
    GuestOrderOut,
    OrderCreate,
    OrderItemOut,
    OrderOut,
)
from app.services import order_service

router = APIRouter()

# Staff button -> status it moves the order to.
ACTIONS = {
    "accept": "accepted",
    "ready": "ready",
    "complete": "completed",
    "cancel": "cancelled",
}


def ticket_label(number: int) -> str:
    return f"{number:03d}"


def _items_and_total(order: Order) -> tuple[list[OrderItemOut], float]:
    items_out: list[OrderItemOut] = []
    total = 0.0
    for item in order.items:
        line_total = float(item.price) * item.quantity
        total += line_total
        items_out.append(
            OrderItemOut(
                drink_id=str(item.drink_id),
                drink_name=item.drink.name if item.drink else "Unknown",
                quantity=item.quantity,
                price=float(item.price),
                line_total=line_total,
            )
        )
    return items_out, total


def build_order_out(order: Order) -> OrderOut:
    items_out, total = _items_and_total(order)
    return OrderOut(
        id=str(order.id),
        ticket_number=order.ticket_number,
        ticket=ticket_label(order.ticket_number),
        guest_name=order.guest_name,
        phone=order.phone,
        status=order.status,
        created_at=order.created_at,
        accepted_at=order.accepted_at,
        ready_at=order.ready_at,
        completed_at=order.completed_at,
        cancelled_at=order.cancelled_at,
        items=items_out,
        total=total,
    )


def build_guest_order_out(order: Order) -> GuestOrderOut:
    items_out, total = _items_and_total(order)
    return GuestOrderOut(
        id=str(order.id),
        ticket=ticket_label(order.ticket_number),
        status=order.status,
        created_at=order.created_at,
        items=items_out,
        total=total,
    )


@router.post(
    "/orders",
    response_model=GuestOrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> GuestOrderOut:
    order = await order_service.place_order(db, payload)
    return build_guest_order_out(order)


@router.get("/orders/{order_id}", response_model=GuestOrderOut)
async def get_order(order_id: UUID, db: AsyncSession = Depends(get_db)) -> GuestOrderOut:
    """Lets the guest's phone follow its own order. The id is a random UUID
    returned only to the device that placed it."""
    return build_guest_order_out(await order_service.get_order(db, order_id))


@router.get("/display/ready", response_model=List[DisplayTicketOut])
async def display_ready(db: AsyncSession = Depends(get_db)) -> list[DisplayTicketOut]:
    """Public feed for the pickup TV. Ticket numbers only."""
    orders = await order_service.list_ready_for_display(db)
    return [
        DisplayTicketOut(ticket=ticket_label(o.ticket_number), ready_at=o.ready_at)
        for o in orders
    ]


@router.get(
    "/admin/orders",
    response_model=List[OrderOut],
    dependencies=[Depends(require_admin)],
)
async def list_orders(
    status_filter: Optional[List[str]] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[OrderOut]:
    orders = await order_service.list_orders(db, status_filter)
    return [build_order_out(order) for order in orders]


@router.post(
    "/admin/orders/{order_id}/{action}",
    response_model=OrderOut,
    dependencies=[Depends(require_admin)],
)
async def change_order_status(
    order_id: UUID,
    action: Literal["accept", "ready", "complete", "cancel"],
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    order = await order_service.transition(db, order_id, ACTIONS[action])
    return build_order_out(order)
