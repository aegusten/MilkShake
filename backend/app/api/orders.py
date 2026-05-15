from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin_catalog import require_admin
from app.db import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderItemOut, OrderOut
from app.services import order_service

router = APIRouter()


def build_order_out(order: Order) -> OrderOut:
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
    return OrderOut(
        id=str(order.id),
        guest_name=order.guest_name,
        phone=order.phone,
        created_at=order.created_at,
        status="pending",
        items=items_out,
        total=total,
    )


@router.post(
    "/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    order = await order_service.place_order(db, payload)
    return build_order_out(order)


@router.get(
    "/admin/orders",
    response_model=List[OrderOut],
    dependencies=[Depends(require_admin)],
)
async def list_orders(db: AsyncSession = Depends(get_db)) -> list[OrderOut]:
    orders = await order_service.list_orders(db)
    return [build_order_out(order) for order in orders]
