"""Live events: the broadcaster, the SSE framing, and that routes publish."""

import asyncio
import json

from app import realtime
from app.api.sse import open_stream
from tests.test_order_service import _seed_drink


def _parse(frame: str) -> dict:
    fields = dict(
        line.split(": ", 1) for line in frame.strip().splitlines() if ": " in line
    )
    return {"event": fields["event"], "id": int(fields["id"]), "data": json.loads(fields["data"])}


async def _never_disconnected() -> bool:
    return False


async def test_broadcaster_delivers_only_to_its_channel(in_memory_broadcaster):
    async with in_memory_broadcaster.subscribe("a") as a, in_memory_broadcaster.subscribe("b") as b:
        await in_memory_broadcaster.publish("a", {"type": "x"})

        assert a.get_nowait() == {"type": "x"}
        assert b.empty()


async def test_unsubscribed_queue_is_released(in_memory_broadcaster):
    async with in_memory_broadcaster.subscribe("a"):
        assert in_memory_broadcaster.subscriber_count("a") == 1

    assert in_memory_broadcaster.subscriber_count("a") == 0


async def test_slow_subscriber_is_dropped_not_grown(in_memory_broadcaster):
    async with in_memory_broadcaster.subscribe("a") as queue:
        for i in range(realtime.MAX_QUEUE + 5):
            await in_memory_broadcaster.publish("a", {"type": "x", "i": i})

        assert queue.qsize() == realtime.MAX_QUEUE
        assert in_memory_broadcaster.subscriber_count("a") == 0


async def test_stream_sends_snapshot_then_live_events(in_memory_broadcaster):
    async def snapshot():
        return [{"type": "tickets", "tickets": []}]

    stream = open_stream("chan", snapshot, _never_disconnected)

    assert (await anext(stream)).startswith("retry:")
    first = _parse(await anext(stream))
    assert first["event"] == "tickets" and first["id"] == 1

    pending = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0)
    await in_memory_broadcaster.publish("chan", {"type": "tickets", "tickets": [{"ticket": "007"}]})
    second = _parse(await asyncio.wait_for(pending, 1))

    assert second["id"] == 2
    assert second["data"]["tickets"] == [{"ticket": "007"}]
    await stream.aclose()
    assert in_memory_broadcaster.subscriber_count("chan") == 0


async def test_stream_subscribes_before_reading_the_snapshot(in_memory_broadcaster):
    """An event published while the snapshot query runs must not be lost."""

    async def slow_snapshot():
        await in_memory_broadcaster.publish("chan", {"type": "order", "n": 1})
        return []

    stream = open_stream("chan", slow_snapshot, _never_disconnected)
    await anext(stream)  # retry line

    caught = _parse(await asyncio.wait_for(anext(stream), 1))

    assert caught["data"] == {"type": "order", "n": 1}
    await stream.aclose()


async def test_idle_stream_sends_heartbeat_comment(in_memory_broadcaster):
    async def snapshot():
        return []

    stream = open_stream("chan", snapshot, _never_disconnected, heartbeat=0.05)
    await anext(stream)

    assert await asyncio.wait_for(anext(stream), 1) == ": ping\n\n"
    await stream.aclose()


async def test_stream_ends_when_client_has_gone(in_memory_broadcaster):
    async def snapshot():
        return []

    async def gone() -> bool:
        return True

    stream = open_stream("chan", snapshot, gone, heartbeat=0.05)
    await anext(stream)

    chunks = [chunk async for chunk in stream]

    assert chunks == []
    assert in_memory_broadcaster.subscriber_count("chan") == 0


async def test_placing_an_order_notifies_staff(client, session, in_memory_broadcaster):
    drink = await _seed_drink(session)
    async with in_memory_broadcaster.subscribe(realtime.ADMIN_CHANNEL) as admin:
        await client.post(
            "/api/orders",
            json={"guest_name": "Alex", "items": [{"drink_id": str(drink.id), "quantity": 1}]},
        )

        event = admin.get_nowait()

    assert event["type"] == "order"
    assert event["order"]["status"] == "pending"
    assert event["order"]["guest_name"] == "Alex"


async def test_marking_ready_updates_tv_and_guest(client, session, admin_headers, in_memory_broadcaster):
    drink = await _seed_drink(session)
    placed = (
        await client.post(
            "/api/orders",
            json={"guest_name": "Alex", "items": [{"drink_id": str(drink.id), "quantity": 1}]},
        )
    ).json()
    await client.post(f"/api/admin/orders/{placed['id']}/accept", headers=admin_headers)

    async with in_memory_broadcaster.subscribe(realtime.DISPLAY_CHANNEL) as tv, \
            in_memory_broadcaster.subscribe(realtime.guest_channel(placed["id"])) as phone:
        await client.post(f"/api/admin/orders/{placed['id']}/ready", headers=admin_headers)

        tv_event = tv.get_nowait()
        phone_event = phone.get_nowait()

    assert [t["ticket"] for t in tv_event["tickets"]] == ["001"]
    assert phone_event["order"]["status"] == "ready"
    assert "guest_name" not in phone_event["order"]


async def test_refused_transition_publishes_nothing(client, session, admin_headers, in_memory_broadcaster):
    drink = await _seed_drink(session)
    placed = (
        await client.post(
            "/api/orders",
            json={"items": [{"drink_id": str(drink.id), "quantity": 1}]},
        )
    ).json()

    async with in_memory_broadcaster.subscribe(realtime.ADMIN_CHANNEL) as admin:
        response = await client.post(
            f"/api/admin/orders/{placed['id']}/complete", headers=admin_headers
        )

        assert response.status_code == 409
        assert admin.empty()
