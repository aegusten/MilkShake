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
