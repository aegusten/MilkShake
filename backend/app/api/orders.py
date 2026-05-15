from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.admin_catalog import require_admin
from app.db import get_db
from app.models.drink import Drink
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderItemOut, OrderOut

router = APIRouter()


def build_order_out(order: Order) -> OrderOut:
    items_out: List[OrderItemOut] = []
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
    return OrderOut(
        id=str(order.id),
        guest_name=order.guest_name,
        phone=order.phone,
        created_at=order.created_at,
        status="pending",
        items=items_out,
        total=total,
    )


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order items required.")

    quantities: Dict[str, int] = {}
    for item in payload.items:
        quantities[item.drink_id] = quantities.get(item.drink_id, 0) + item.quantity

    result = await db.execute(
        select(Drink).where(Drink.id.in_(list(quantities.keys())))
    )
    drinks = list(result.scalars().all())
    if len(drinks) != len(quantities):
        raise HTTPException(status_code=404, detail="Drink not found.")

    order = Order(guest_name=payload.guest_name, phone=payload.phone)
    db.add(order)
    await db.flush()

    drink_map = {str(drink.id): drink for drink in drinks}
    for drink_id, quantity in quantities.items():
        drink = drink_map.get(drink_id)
        if not drink:
            continue
        order_item = OrderItem(
            order_id=order.id,
            drink_id=drink.id,
            quantity=quantity,
            price=drink.price,
        )
        db.add(order_item)

    await db.commit()
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .where(Order.id == order.id)
    )
    refreshed = result.scalar_one()
    return build_order_out(refreshed)


@router.get(
    "/admin/orders",
    response_model=List[OrderOut],
    dependencies=[Depends(require_admin)],
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
) -> list[OrderOut]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .order_by(Order.created_at.desc())
    )
    orders = list(result.scalars().all())
    return [build_order_out(order) for order in orders]
