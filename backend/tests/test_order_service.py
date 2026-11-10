import pytest

from app.schemas.drink import DrinkCreate
from app.schemas.item_master import ItemMasterCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services import catalog_service, order_service
from app.services.errors import NotFoundError


async def _seed_drink(session, name: str = "Vanilla Shake", price: int = 15000):
    im = await catalog_service.create_item_master(
        session, ItemMasterCreate(name=f"Cat-{name}")
    )
    return await catalog_service.create_drink(
        session,
        DrinkCreate(
            name=name,
            description="",
            price=price,
            type="milkshake",
            item_master_ids=[str(im.id)],
        ),
    )


async def test_place_order_creates_order_with_items_eager_loaded(session):
    drink = await _seed_drink(session)

    order = await order_service.place_order(
        session,
        OrderCreate(
            guest_name="Alex",
            phone=None,
            items=[OrderItemCreate(drink_id=str(drink.id), quantity=2)],
        ),
    )

    assert order.guest_name == "Alex"
    assert len(order.items) == 1
    assert order.items[0].quantity == 2
    assert order.items[0].drink.name == "Vanilla Shake"


async def test_place_order_merges_duplicate_drink_lines(session):
    drink = await _seed_drink(session)

    order = await order_service.place_order(
        session,
        OrderCreate(
            guest_name="Alex",
            items=[
                OrderItemCreate(drink_id=str(drink.id), quantity=1),
                OrderItemCreate(drink_id=str(drink.id), quantity=3),
            ],
        ),
    )

    assert len(order.items) == 1
    assert order.items[0].quantity == 4


async def test_place_order_with_unknown_drink_raises_not_found(session):
    import uuid as uuid_lib

    with pytest.raises(NotFoundError):
        await order_service.place_order(
            session,
            OrderCreate(
                guest_name="Alex",
                items=[
                    OrderItemCreate(drink_id=str(uuid_lib.uuid4()), quantity=1)
                ],
            ),
        )


async def test_place_order_captures_price_snapshot(session):
    drink = await _seed_drink(session, price=12500)

    order = await order_service.place_order(
        session,
        OrderCreate(
            guest_name="Alex",
            items=[OrderItemCreate(drink_id=str(drink.id), quantity=1)],
        ),
    )

    assert int(order.items[0].price) == 12500


async def test_list_orders_returns_newest_first(session):
    drink = await _seed_drink(session)

    await order_service.place_order(
        session,
        OrderCreate(
            guest_name="First",
            items=[OrderItemCreate(drink_id=str(drink.id), quantity=1)],
        ),
    )
    await order_service.place_order(
        session,
        OrderCreate(
            guest_name="Second",
            items=[OrderItemCreate(drink_id=str(drink.id), quantity=1)],
        ),
    )

    orders = await order_service.list_orders(session)

    assert [o.guest_name for o in orders[:2]] == ["Second", "First"]
