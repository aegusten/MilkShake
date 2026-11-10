"""Order state machine and daily ticket numbers (service layer)."""

import asyncio
from datetime import date

import pytest

from app.schemas.order import OrderCreate, OrderItemCreate
from app.services import order_service
from app.services.errors import ConflictError, NotFoundError
from tests.test_order_service import _seed_drink

DAY_ONE = date(2026, 3, 1)
DAY_TWO = date(2026, 3, 2)


def _payload(drink, name="Alex"):
    return OrderCreate(
        guest_name=name,
        items=[OrderItemCreate(drink_id=str(drink.id), quantity=1)],
    )


async def test_new_order_is_pending_with_ticket_one(session):
    drink = await _seed_drink(session)

    order = await order_service.place_order(session, _payload(drink), today=DAY_ONE)

    assert order.status == "pending"
    assert order.ticket_number == 1
    assert order.ticket_date == DAY_ONE


async def test_ticket_numbers_count_up_within_a_day(session):
    drink = await _seed_drink(session)

    numbers = [
        (await order_service.place_order(session, _payload(drink), today=DAY_ONE)).ticket_number
        for _ in range(3)
    ]

    assert numbers == [1, 2, 3]


async def test_ticket_numbers_restart_on_a_new_day(session):
    drink = await _seed_drink(session)
    await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    await order_service.place_order(session, _payload(drink), today=DAY_ONE)

    first_of_day_two = await order_service.place_order(
        session, _payload(drink), today=DAY_TWO
    )

    assert first_of_day_two.ticket_number == 1


async def test_concurrent_orders_never_share_a_ticket(session_factory):
    async with session_factory() as s:
        drink = await _seed_drink(s)

    async def place_one(i: int) -> int:
        async with session_factory() as s:
            order = await order_service.place_order(
                s, _payload(drink, name=f"Guest {i}"), today=DAY_ONE
            )
            return order.ticket_number

    numbers = await asyncio.gather(*(place_one(i) for i in range(50)))

    assert sorted(numbers) == list(range(1, 51))


async def test_happy_path_sets_each_timestamp(session):
    drink = await _seed_drink(session)
    order = await order_service.place_order(session, _payload(drink), today=DAY_ONE)

    for target in ("accepted", "ready", "completed"):
        order = await order_service.transition(session, order.id, target)
        assert order.status == target
        assert getattr(order, f"{target}_at") is not None


@pytest.mark.parametrize(
    "path, refused",
    [
        ([], "ready"),
        ([], "completed"),
        (["accepted"], "completed"),
        (["accepted"], "pending"),
        (["accepted", "ready", "completed"], "cancelled"),
        (["cancelled"], "accepted"),
    ],
)
async def test_illegal_transitions_raise_conflict(session, path, refused):
    drink = await _seed_drink(session)
    order = await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    order_id = order.id
    for step in path:
        await order_service.transition(session, order_id, step)

    with pytest.raises(ConflictError):
        await order_service.transition(session, order_id, refused)

    unchanged = await order_service.get_order(session, order_id)
    assert unchanged.status == (path[-1] if path else "pending")


@pytest.mark.parametrize("start", [[], ["accepted"], ["accepted", "ready"]])
async def test_any_open_order_can_be_cancelled(session, start):
    drink = await _seed_drink(session)
    order = await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    for step in start:
        order = await order_service.transition(session, order.id, step)

    order = await order_service.transition(session, order.id, "cancelled")

    assert order.status == "cancelled"
    assert order.cancelled_at is not None


async def test_transition_on_missing_order_raises_not_found(session):
    import uuid

    with pytest.raises(NotFoundError):
        await order_service.transition(session, uuid.uuid4(), "accepted")


async def test_display_lists_only_todays_ready_tickets_newest_first(session):
    drink = await _seed_drink(session)
    yesterday = await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    first = await order_service.place_order(session, _payload(drink), today=DAY_TWO)
    second = await order_service.place_order(session, _payload(drink), today=DAY_TWO)
    still_pending = await order_service.place_order(session, _payload(drink), today=DAY_TWO)
    for order in (yesterday, first, second):
        await order_service.transition(session, order.id, "accepted")
    for order in (yesterday, first):
        await order_service.transition(session, order.id, "ready")
    await asyncio.sleep(0.01)
    await order_service.transition(session, second.id, "ready")

    shown = await order_service.list_ready_for_display(session, today=DAY_TWO)

    assert [o.id for o in shown] == [second.id, first.id]
    assert still_pending.id not in [o.id for o in shown]


async def test_list_orders_filters_by_status(session):
    drink = await _seed_drink(session)
    a = await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    await order_service.place_order(session, _payload(drink), today=DAY_ONE)
    await order_service.transition(session, a.id, "accepted")

    accepted = await order_service.list_orders(session, ["accepted"])

    assert [o.id for o in accepted] == [a.id]
