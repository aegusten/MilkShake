from collections.abc import Iterable
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.drink import Drink
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate
from app.services.errors import ConflictError, InvalidInputError, NotFoundError

# Every status an order can move to from a given status. Anything not listed
# is refused with a 409. completed and cancelled are terminal.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"accepted", "cancelled"}),
    "accepted": frozenset({"ready", "cancelled"}),
    "ready": frozenset({"completed", "cancelled"}),
    "completed": frozenset(),
    "cancelled": frozenset(),
}

ACTIVE_STATUSES = ("pending", "accepted", "ready")

# Namespace for the advisory lock that serializes ticket numbering. Added to
# the date ordinal so each day gets its own lock key.
_TICKET_LOCK_BASE = 7_340_000_000


def bar_today() -> date:
    """Today's date where the bar is, which is when ticket numbers reset."""
    return datetime.now(ZoneInfo(get_settings().BAR_TIMEZONE)).date()


async def _next_ticket_number(session: AsyncSession, ticket_date: date) -> int:
    """Allocate the next ticket number for ``ticket_date``.

    Two guests ordering at the same instant would both read the same MAX
    without a lock. The transaction-scoped advisory lock makes the second
    one wait until the first commits, so numbers never collide. The unique
    constraint on (ticket_date, ticket_number) is the backstop.
    """
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": _TICKET_LOCK_BASE + ticket_date.toordinal()},
    )
    result = await session.execute(
        select(func.coalesce(func.max(Order.ticket_number), 0)).where(
            Order.ticket_date == ticket_date
        )
    )
    return int(result.scalar_one()) + 1


async def place_order(
    session: AsyncSession,
    payload: OrderCreate,
    today: date | None = None,
) -> Order:
    """Create a new pending order with today's next ticket number.

    Merges duplicate drink lines so the same drink in the cart twice becomes
    one order item with summed quantity. The unique constraint
    ``uq_order_drink_once`` enforces this at the database level too.
    """
    if not payload.items:
        raise InvalidInputError("Order items required.")

    quantities: dict[str, int] = {}
    for item in payload.items:
        quantities[item.drink_id] = quantities.get(item.drink_id, 0) + item.quantity

    result = await session.execute(
        select(Drink).where(Drink.id.in_(list(quantities.keys())))
    )
    drinks = list(result.scalars().all())
    if len(drinks) != len(quantities):
        raise NotFoundError("One or more drinks not found.")

    ticket_date = today or bar_today()
    order = Order(
        guest_name=payload.guest_name,
        phone=payload.phone,
        status="pending",
        ticket_date=ticket_date,
        ticket_number=await _next_ticket_number(session, ticket_date),
    )
    session.add(order)
    await session.flush()

    drink_map = {str(drink.id): drink for drink in drinks}
    for drink_id, quantity in quantities.items():
        drink = drink_map[drink_id]
        session.add(
            OrderItem(
                order_id=order.id,
                drink_id=drink.id,
                quantity=quantity,
                price=drink.price,
            )
        )

    await session.commit()
    return await _load_order_with_relations(session, order.id)


async def transition(session: AsyncSession, order_id: UUID, target: str) -> Order:
    """Move an order to ``target`` if the state machine allows it.

    The row is locked first so two staff tapping different buttons on the
    same order cannot both win.
    """
    if target not in ALLOWED_TRANSITIONS:
        raise InvalidInputError(f"Unknown status: {target}.")

    result = await session.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        await session.rollback()
        raise NotFoundError("Order not found.")

    if target not in ALLOWED_TRANSITIONS[order.status]:
        current = order.status
        await session.rollback()
        raise ConflictError(f"Cannot move order from {current} to {target}.")

    order.status = target
    setattr(order, f"{target}_at", func.now())
    await session.commit()
    return await _load_order_with_relations(session, order_id)


async def get_order(session: AsyncSession, order_id: UUID) -> Order:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order not found.")
    return order


async def list_orders(
    session: AsyncSession, statuses: Iterable[str] | None = None
) -> list[Order]:
    """List orders newest-first, optionally only those in ``statuses``."""
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .order_by(Order.created_at.desc(), Order.ticket_number.desc())
    )
    statuses = list(statuses or [])
    if statuses:
        unknown = set(statuses) - set(ALLOWED_TRANSITIONS)
        if unknown:
            raise InvalidInputError(f"Unknown status: {', '.join(sorted(unknown))}.")
        query = query.where(Order.status.in_(statuses))
    result = await session.execute(query)
    return list(result.scalars().all())


async def list_ready_for_display(
    session: AsyncSession, today: date | None = None
) -> list[Order]:
    """Tickets waiting to be picked up today, newest ready first.

    Filtering on today's ticket_date is what clears the TV at midnight.
    """
    result = await session.execute(
        select(Order)
        .where(Order.status == "ready", Order.ticket_date == (today or bar_today()))
        .order_by(Order.ready_at.desc(), Order.ticket_number.desc())
    )
    return list(result.scalars().all())


async def _load_order_with_relations(session: AsyncSession, order_id: UUID) -> Order:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .where(Order.id == order_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()
