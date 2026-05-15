from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drink import Drink
from app.models.drink_image import DrinkImage
from app.models.item_master import ItemMaster
from app.schemas.drink import (
    DrinkCreate,
    DrinkImageCreate,
    DrinkUpdate,
)
from app.schemas.item_master import ItemMasterCreate, ItemMasterUpdate
from app.services.errors import ConflictError, InvalidInputError, NotFoundError


# --- Item masters ---


async def list_item_masters(session: AsyncSession) -> list[ItemMaster]:
    result = await session.execute(
        select(ItemMaster).order_by(ItemMaster.sort_order)
    )
    return list(result.scalars().all())


async def create_item_master(
    session: AsyncSession, payload: ItemMasterCreate
) -> ItemMaster:
    item_master = ItemMaster(**payload.model_dump())
    session.add(item_master)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Item master name already exists.") from exc
    await session.refresh(item_master)
    return item_master


async def update_item_master(
    session: AsyncSession, item_master_id: UUID, payload: ItemMasterUpdate
) -> ItemMaster:
    result = await session.execute(
        select(ItemMaster).where(ItemMaster.id == item_master_id)
    )
    item_master = result.scalar_one_or_none()
    if not item_master:
        raise NotFoundError("Item master not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item_master, key, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Item master update failed.") from exc
    await session.refresh(item_master)
    return item_master


async def delete_item_master(session: AsyncSession, item_master_id: UUID) -> None:
    result = await session.execute(
        select(ItemMaster).where(ItemMaster.id == item_master_id)
    )
    item_master = result.scalar_one_or_none()
    if not item_master:
        raise NotFoundError("Item master not found.")
    await session.delete(item_master)
    await session.commit()


# --- Drinks ---


async def list_drinks(
    session: AsyncSession, item_master_id: UUID | None = None
) -> list[Drink]:
    stmt = (
        select(Drink)
        .options(selectinload(Drink.item_masters))
        .order_by(Drink.created_at.desc())
    )
    if item_master_id:
        stmt = stmt.join(Drink.item_masters).where(ItemMaster.id == item_master_id)
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def create_drink(session: AsyncSession, payload: DrinkCreate) -> Drink:
    if not payload.item_master_ids:
        raise InvalidInputError("At least one item master is required.")
    item_masters = await _resolve_item_masters(session, payload.item_master_ids)
    drink = Drink(**payload.model_dump(exclude={"item_master_ids"}))
    drink.item_masters = item_masters
    session.add(drink)
    await session.commit()
    return await _load_drink_with_relations(session, drink.id)


async def update_drink(
    session: AsyncSession, drink_id: UUID, payload: DrinkUpdate
) -> Drink:
    drink = await _load_drink_with_relations(session, drink_id)
    if not drink:
        raise NotFoundError("Drink not found.")
    if payload.item_master_ids is not None:
        if not payload.item_master_ids:
            raise InvalidInputError("At least one item master is required.")
        drink.item_masters = await _resolve_item_masters(
            session, payload.item_master_ids
        )
    for key, value in payload.model_dump(
        exclude_unset=True, exclude={"item_master_ids"}
    ).items():
        setattr(drink, key, value)
    await session.commit()
    return await _load_drink_with_relations(session, drink.id)


async def delete_drink(session: AsyncSession, drink_id: UUID) -> None:
    result = await session.execute(select(Drink).where(Drink.id == drink_id))
    drink = result.scalar_one_or_none()
    if not drink:
        raise NotFoundError("Drink not found.")
    await session.delete(drink)
    await session.commit()


async def add_drink_image(
    session: AsyncSession, drink_id: UUID, payload: DrinkImageCreate
) -> DrinkImage:
    result = await session.execute(select(Drink).where(Drink.id == drink_id))
    drink = result.scalar_one_or_none()
    if not drink:
        raise NotFoundError("Drink not found.")
    if payload.position < 1 or payload.position > 3:
        raise InvalidInputError("Image position must be 1-3.")
    image = DrinkImage(
        drink_id=drink_id, url=payload.url, position=payload.position
    )
    session.add(image)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Image position already used.") from exc
    await session.refresh(image)
    return image


async def _load_drink_with_relations(
    session: AsyncSession, drink_id: UUID
) -> Drink:
    result = await session.execute(
        select(Drink)
        .options(selectinload(Drink.item_masters))
        .where(Drink.id == drink_id)
    )
    drink = result.scalar_one_or_none()
    if drink is None:
        raise NotFoundError("Drink not found.")
    return drink


async def _resolve_item_masters(
    session: AsyncSession, ids: list[str]
) -> list[ItemMaster]:
    result = await session.execute(
        select(ItemMaster).where(ItemMaster.id.in_(ids))
    )
    item_masters = list(result.scalars().all())
    if len(item_masters) != len(set(ids)):
        raise NotFoundError("Item master not found.")
    return item_masters
