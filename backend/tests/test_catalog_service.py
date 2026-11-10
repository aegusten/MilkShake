import pytest

from app.schemas.drink import DrinkCreate, DrinkUpdate
from app.schemas.item_master import ItemMasterCreate, ItemMasterUpdate
from app.services import catalog_service
from app.services.errors import ConflictError, InvalidInputError, NotFoundError


async def _make_item_master(session, name: str = "Cocktails"):
    return await catalog_service.create_item_master(
        session, ItemMasterCreate(name=name)
    )


async def test_create_item_master_persists_row(session):
    created = await _make_item_master(session, "Milkshakes")

    listed = await catalog_service.list_item_masters(session)

    assert created.name == "Milkshakes"
    assert any(im.id == created.id for im in listed)


async def test_create_item_master_with_duplicate_name_raises_conflict(session):
    await _make_item_master(session, "Cocktails")

    with pytest.raises(ConflictError):
        await _make_item_master(session, "Cocktails")


async def test_update_item_master_renames_it(session):
    im = await _make_item_master(session, "OldName")

    updated = await catalog_service.update_item_master(
        session, im.id, ItemMasterUpdate(name="NewName")
    )

    assert updated.name == "NewName"


async def test_delete_unknown_item_master_raises_not_found(session):
    import uuid as uuid_lib

    with pytest.raises(NotFoundError):
        await catalog_service.delete_item_master(session, uuid_lib.uuid4())


async def test_create_drink_with_no_item_master_raises_invalid_input(session):
    payload = DrinkCreate(
        name="Solo", description="", price=1000, type="other", item_master_ids=[]
    )

    with pytest.raises(InvalidInputError):
        await catalog_service.create_drink(session, payload)


async def test_create_drink_eager_loads_item_masters(session):
    im = await _make_item_master(session, "Featured")
    payload = DrinkCreate(
        name="Vanilla Shake",
        description="Classic",
        price=15000,
        type="milkshake",
        item_master_ids=[str(im.id)],
    )

    drink = await catalog_service.create_drink(session, payload)

    assert drink.name == "Vanilla Shake"
    assert [im.id for im in drink.item_masters] == [im.id]


async def test_update_drink_replaces_item_masters(session):
    im_a = await _make_item_master(session, "A")
    im_b = await _make_item_master(session, "B")
    drink = await catalog_service.create_drink(
        session,
        DrinkCreate(
            name="X", description="", price=1000, type="other",
            item_master_ids=[str(im_a.id)],
        ),
    )

    updated = await catalog_service.update_drink(
        session,
        drink.id,
        DrinkUpdate(item_master_ids=[str(im_b.id)]),
    )

    assert [im.id for im in updated.item_masters] == [im_b.id]


async def _make_drink(session, name="Mojito", masters=None):
    masters = masters or [await _make_item_master(session, f"IM-{name}")]
    return await catalog_service.create_drink(
        session,
        DrinkCreate(
            name=name,
            price=30000,
            type="cocktail",
            item_master_ids=[str(m.id) for m in masters],
        ),
    )


async def test_update_unknown_item_master_raises_not_found(session):
    import uuid

    with pytest.raises(NotFoundError):
        await catalog_service.update_item_master(
            session, uuid.uuid4(), ItemMasterUpdate(name="x")
        )


async def test_renaming_item_master_onto_existing_name_raises_conflict(session):
    await _make_item_master(session, "Shakes")
    other = await _make_item_master(session, "Sodas")

    with pytest.raises(ConflictError):
        await catalog_service.update_item_master(
            session, other.id, ItemMasterUpdate(name="Shakes")
        )


async def test_delete_item_master_removes_it(session):
    im = await _make_item_master(session, "Seasonal")

    await catalog_service.delete_item_master(session, im.id)

    assert all(m.id != im.id for m in await catalog_service.list_item_masters(session))


async def test_list_drinks_can_filter_by_item_master(session):
    shakes = await _make_item_master(session, "Shakes")
    sodas = await _make_item_master(session, "Sodas")
    vanilla = await _make_drink(session, "Vanilla", [shakes])
    await _make_drink(session, "Cola", [sodas])

    only_shakes = await catalog_service.list_drinks(session, shakes.id)

    assert [d.id for d in only_shakes] == [vanilla.id]


async def test_update_drink_with_empty_item_masters_raises_invalid_input(session):
    drink = await _make_drink(session)

    with pytest.raises(InvalidInputError):
        await catalog_service.update_drink(session, drink.id, DrinkUpdate(item_master_ids=[]))


async def test_update_drink_changes_plain_fields(session):
    drink = await _make_drink(session)

    updated = await catalog_service.update_drink(session, drink.id, DrinkUpdate(price=31000))

    assert float(updated.price) == 31000


async def test_update_unknown_drink_raises_not_found(session):
    import uuid

    with pytest.raises(NotFoundError):
        await catalog_service.update_drink(session, uuid.uuid4(), DrinkUpdate(price=1))


async def test_delete_drink_removes_it(session):
    drink = await _make_drink(session)

    await catalog_service.delete_drink(session, drink.id)

    assert all(d.id != drink.id for d in await catalog_service.list_drinks(session))


async def test_delete_unknown_drink_raises_not_found(session):
    import uuid

    with pytest.raises(NotFoundError):
        await catalog_service.delete_drink(session, uuid.uuid4())


async def test_drink_image_position_must_be_one_to_three(session):
    from app.schemas.drink import DrinkImageCreate

    drink = await _make_drink(session)

    with pytest.raises(InvalidInputError):
        await catalog_service.add_drink_image(
            session, drink.id, DrinkImageCreate(url="/uploads/a.png", position=4)
        )


async def test_two_images_cannot_share_a_position(session):
    from app.schemas.drink import DrinkImageCreate

    drink = await _make_drink(session)
    await catalog_service.add_drink_image(
        session, drink.id, DrinkImageCreate(url="/uploads/a.png", position=1)
    )

    with pytest.raises(ConflictError):
        await catalog_service.add_drink_image(
            session, drink.id, DrinkImageCreate(url="/uploads/b.png", position=1)
        )
