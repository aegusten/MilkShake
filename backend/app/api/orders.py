from typing import Any, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import realtime
from app.api.admin_catalog import require_admin
from app.api.sse import open_stream, sse_response
from app.db import AsyncSessionLocal, get_db
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


async def _display_tickets(db: AsyncSession) -> list[dict[str, Any]]:
    orders = await order_service.list_ready_for_display(db)
    return [
        DisplayTicketOut(ticket=ticket_label(o.ticket_number), ready_at=o.ready_at).model_dump(mode="json")
        for o in orders
    ]


async def publish_order_change(
    db: AsyncSession, order: Order, *, display_changed: bool
) -> None:
    """Tell staff screens, the guest's phone and (if needed) the TV."""
    broadcaster = realtime.get_broadcaster()
    await broadcaster.publish(
        realtime.ADMIN_CHANNEL,
        {"type": "order", "order": build_order_out(order).model_dump(mode="json")},
    )
    await broadcaster.publish(
        realtime.guest_channel(str(order.id)),
        {"type": "order", "order": build_guest_order_out(order).model_dump(mode="json")},
    )
    if display_changed:
        await broadcaster.publish(
            realtime.DISPLAY_CHANNEL,
            {"type": "tickets", "tickets": await _display_tickets(db)},
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
    await publish_order_change(db, order, display_changed=False)
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
    # Any transition can add or remove a ready ticket, and the TV list is
    # one cheap query, so always resend it.
    await publish_order_change(db, order, display_changed=True)
    return build_order_out(order)


# --- Live streams -----------------------------------------------------------
#
# Each stream opens with a snapshot of current state, then sends changes.
# Snapshots use their own short session so no database connection is held
# for the life of the stream.


@router.get(
    "/stream/admin",
    dependencies=[Depends(require_admin)],
    response_class=StreamingResponse,
)
async def stream_admin(request: Request) -> StreamingResponse:
    """Open orders, then every new order and status change. Bearer auth, so
    the admin page reads it with fetch() rather than EventSource."""

    async def snapshot() -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            orders = await order_service.list_orders(db, order_service.ACTIVE_STATUSES)
        return [
            {
                "type": "snapshot",
                "orders": [build_order_out(o).model_dump(mode="json") for o in orders],
            }
        ]

    return sse_response(
        open_stream(realtime.ADMIN_CHANNEL, snapshot, request.is_disconnected)
    )


@router.get("/stream/display", response_class=StreamingResponse)
async def stream_display(request: Request) -> StreamingResponse:
    """Ready ticket numbers for the pickup TV. Every event is the full list,
    so the screen never has to merge or can drift."""

    async def snapshot() -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            return [{"type": "tickets", "tickets": await _display_tickets(db)}]

    return sse_response(
        open_stream(realtime.DISPLAY_CHANNEL, snapshot, request.is_disconnected)
    )


@router.get("/stream/orders/{order_id}", response_class=StreamingResponse)
async def stream_guest_order(
    order_id: UUID, request: Request, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """One guest's order, so their phone flips to Ready without polling."""
    await order_service.get_order(db, order_id)  # 404 before opening a stream

    async def snapshot() -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as s:
            order = await order_service.get_order(s, order_id)
        return [{"type": "order", "order": build_guest_order_out(order).model_dump(mode="json")}]

    return sse_response(
        open_stream(realtime.guest_channel(str(order_id)), snapshot, request.is_disconnected)
    )
