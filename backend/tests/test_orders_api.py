"""Order endpoints over HTTP: auth, status codes, and what each audience sees."""

import uuid

from tests.test_order_service import _seed_drink


async def _place(client, drink, name="Alex"):
    response = await client.post(
        "/api/orders",
        json={
            "guest_name": name,
            "phone": "+998 90 000 00 00",
            "items": [{"drink_id": str(drink.id), "quantity": 2}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_guest_gets_ticket_but_never_name_or_phone(client, session):
    drink = await _seed_drink(session)

    body = await _place(client, drink)

    assert body["ticket"] == "001"
    assert body["status"] == "pending"
    assert "guest_name" not in body
    assert "phone" not in body


async def test_guest_can_follow_own_order(client, session, admin_headers):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)
    await client.post(f"/api/admin/orders/{placed['id']}/accept", headers=admin_headers)

    response = await client.get(f"/api/orders/{placed['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


async def test_unknown_order_is_404(client):
    response = await client.get(f"/api/orders/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_staff_actions_require_a_token(client, session):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)

    response = await client.post(f"/api/admin/orders/{placed['id']}/accept")

    assert response.status_code == 401


async def test_staff_walks_an_order_to_completed(client, session, admin_headers):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)

    for action, expected in (
        ("accept", "accepted"),
        ("ready", "ready"),
        ("complete", "completed"),
    ):
        response = await client.post(
            f"/api/admin/orders/{placed['id']}/{action}", headers=admin_headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == expected


async def test_skipping_a_step_is_409(client, session, admin_headers):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)

    response = await client.post(
        f"/api/admin/orders/{placed['id']}/ready", headers=admin_headers
    )

    assert response.status_code == 409
    assert "pending" in response.json()["detail"]


async def test_unknown_action_is_rejected(client, session, admin_headers):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)

    response = await client.post(
        f"/api/admin/orders/{placed['id']}/refund", headers=admin_headers
    )

    assert response.status_code == 422


async def test_display_shows_ticket_numbers_only(client, session, admin_headers):
    drink = await _seed_drink(session)
    placed = await _place(client, drink)
    for action in ("accept", "ready"):
        await client.post(f"/api/admin/orders/{placed['id']}/{action}", headers=admin_headers)

    response = await client.get("/api/display/ready")

    assert response.status_code == 200
    tickets = response.json()
    assert [t["ticket"] for t in tickets] == ["001"]
    assert set(tickets[0]) == {"ticket", "ready_at"}


async def test_admin_list_filters_by_status(client, session, admin_headers):
    drink = await _seed_drink(session)
    first = await _place(client, drink, name="First")
    await _place(client, drink, name="Second")
    await client.post(f"/api/admin/orders/{first['id']}/accept", headers=admin_headers)

    response = await client.get(
        "/api/admin/orders", params={"status": "pending"}, headers=admin_headers
    )

    assert response.status_code == 200
    assert [o["guest_name"] for o in response.json()] == ["Second"]


async def test_admin_list_rejects_unknown_status(client, admin_headers):
    response = await client.get(
        "/api/admin/orders", params={"status": "lost"}, headers=admin_headers
    )

    assert response.status_code == 400


async def test_timestamps_are_sent_as_utc(client, session):
    drink = await _seed_drink(session)

    body = await _place(client, drink)

    assert body["created_at"].endswith("Z") or body["created_at"].endswith("+00:00")
