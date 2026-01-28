from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.order import Order, OrderItem
from app.models.drink import Drink
from app.api.admin_catalog import require_admin
from app.schemas.order import OrderCreate, OrderOut, OrderItemOut

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
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order items required.")

    quantities: Dict[str, int] = {}
    for item in payload.items:
        quantities[item.drink_id] = quantities.get(item.drink_id, 0) + item.quantity

    drinks = (
        db.query(Drink)
        .filter(Drink.id.in_(list(quantities.keys())))
        .all()
    )
    if len(drinks) != len(quantities):
        raise HTTPException(status_code=404, detail="Drink not found.")

    order = Order(guest_name=payload.guest_name, phone=payload.phone)
    db.add(order)
    db.flush()

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

    db.commit()
    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .filter(Order.id == order.id)
        .one()
    )
    return build_order_out(order)


@router.get("/admin/orders", response_model=List[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.drink))
        .order_by(Order.created_at.desc())
        .all()
    )
    return [build_order_out(order) for order in orders]
