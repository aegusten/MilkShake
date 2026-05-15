from typing import Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drink import Drink
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate
from app.services.errors import InvalidInputError, NotFoundError


async def place_order(session: AsyncSession, payload: OrderCreate) -> Order:
    """Create a new order and return it with items + drinks eagerly loaded.

    Merges duplicate drink lines so the same drink in the cart twice becomes
    one order item with summed quantity. The unique constraint
    ``uq_order_drink_once`` enforces this at the database level too.
    """
    if not payload.items:
        raise InvalidInputError("Order items required.")

    quantities: Dict[str, int] = {}
    for item in payload.items:
        quantities[item.drink_id] = quantities.get(item.drink_id, 0) + item.quantity

    result = await session.execute(
        select(Drink).where(Drink.id.in_(list(quantities.keys())))
    )
    drinks = list(result.scalars().all())
    if len(drinks) != len(quantities):
        raise NotFoundError("One or more drinks not found.")

    order = Order(guest_name=payload.guest_name, phone=payload.phone)
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


async def list_orders(session: AsyncSession) -> list[Order]:
    """List all orders newest-first, with items + drinks eagerly loaded."""
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def _load_order_with_relations(session: AsyncSession, order_id: UUID) -> Order:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .where(Order.id == order_id)
    )
    return result.scalar_one()
