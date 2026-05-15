import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Security, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.admin import Admin
from app.models.drink import Drink
from app.models.drink_image import DrinkImage
from app.models.item_master import ItemMaster
from app.schemas.drink import (
    DrinkCreate,
    DrinkImageCreate,
    DrinkImageOut,
    DrinkOut,
    DrinkUpdate,
)
from app.schemas.item_master import ItemMasterCreate, ItemMasterOut, ItemMasterUpdate
from app.utils.security import decode_access_token

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

bearer_scheme = HTTPBearer(auto_error=False)

_BEARER_HEADERS = {"WWW-Authenticate": "Bearer"}


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin credentials required.",
            headers=_BEARER_HEADERS,
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers=_BEARER_HEADERS,
        ) from exc
    try:
        admin_uuid = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers=_BEARER_HEADERS,
        ) from exc
    result = await db.execute(select(Admin).where(Admin.id == admin_uuid))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return admin


async def _get_drink_with_item_masters(db: AsyncSession, drink_id: uuid.UUID) -> Drink | None:
    result = await db.execute(
        select(Drink)
        .options(selectinload(Drink.item_masters))
        .where(Drink.id == drink_id)
    )
    return result.scalar_one_or_none()


@router.get("/item-masters", response_model=List[ItemMasterOut])
async def list_item_masters(db: AsyncSession = Depends(get_db)) -> list[ItemMaster]:
    result = await db.execute(select(ItemMaster).order_by(ItemMaster.sort_order))
    return list(result.scalars().all())


@router.post(
    "/item-masters",
    response_model=ItemMasterOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_item_master(
    payload: ItemMasterCreate,
    db: AsyncSession = Depends(get_db),
) -> ItemMaster:
    item_master = ItemMaster(**payload.model_dump())
    db.add(item_master)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Item master name already exists.")
    await db.refresh(item_master)
    return item_master


@router.patch(
    "/item-masters/{item_master_id}",
    response_model=ItemMasterOut,
    dependencies=[Depends(require_admin)],
)
async def update_item_master(
    item_master_id: str,
    payload: ItemMasterUpdate,
    db: AsyncSession = Depends(get_db),
) -> ItemMaster:
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id == item_master_id)
    )
    item_master = result.scalar_one_or_none()
    if not item_master:
        raise HTTPException(status_code=404, detail="Item master not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item_master, key, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Item master update failed.")
    await db.refresh(item_master)
    return item_master


@router.delete(
    "/item-masters/{item_master_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_item_master(
    item_master_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id == item_master_id)
    )
    item_master = result.scalar_one_or_none()
    if not item_master:
        raise HTTPException(status_code=404, detail="Item master not found.")
    await db.delete(item_master)
    await db.commit()
    return None


@router.get("/drinks", response_model=List[DrinkOut])
async def list_drinks(db: AsyncSession = Depends(get_db)) -> list[Drink]:
    result = await db.execute(
        select(Drink)
        .options(selectinload(Drink.item_masters))
        .order_by(Drink.created_at.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/drinks",
    response_model=DrinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_drink(
    payload: DrinkCreate,
    db: AsyncSession = Depends(get_db),
) -> Drink:
    if not payload.item_master_ids:
        raise HTTPException(status_code=400, detail="At least one item master is required.")
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id.in_(payload.item_master_ids))
    )
    item_masters = list(result.scalars().all())
    if len(item_masters) != len(set(payload.item_master_ids)):
        raise HTTPException(status_code=404, detail="Item master not found.")
    drink = Drink(**payload.model_dump(exclude={"item_master_ids"}))
    drink.item_masters = item_masters
    db.add(drink)
    await db.commit()
    refreshed = await _get_drink_with_item_masters(db, drink.id)
    if refreshed is None:
        raise HTTPException(status_code=500, detail="Failed to load drink after create.")
    return refreshed


@router.patch(
    "/drinks/{drink_id}",
    response_model=DrinkOut,
    dependencies=[Depends(require_admin)],
)
async def update_drink(
    drink_id: str,
    payload: DrinkUpdate,
    db: AsyncSession = Depends(get_db),
) -> Drink:
    drink = await _get_drink_with_item_masters(db, uuid.UUID(drink_id))
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    if payload.item_master_ids is not None:
        if not payload.item_master_ids:
            raise HTTPException(status_code=400, detail="At least one item master is required.")
        result = await db.execute(
            select(ItemMaster).where(ItemMaster.id.in_(payload.item_master_ids))
        )
        item_masters = list(result.scalars().all())
        if len(item_masters) != len(set(payload.item_master_ids)):
            raise HTTPException(status_code=404, detail="Item master not found.")
        drink.item_masters = item_masters
    for key, value in payload.model_dump(exclude_unset=True, exclude={"item_master_ids"}).items():
        setattr(drink, key, value)
    await db.commit()
    refreshed = await _get_drink_with_item_masters(db, drink.id)
    if refreshed is None:
        raise HTTPException(status_code=500, detail="Failed to load drink after update.")
    return refreshed


@router.delete(
    "/drinks/{drink_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_drink(
    drink_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Drink).where(Drink.id == drink_id))
    drink = result.scalar_one_or_none()
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    await db.delete(drink)
    await db.commit()
    return None


@router.post(
    "/drinks/{drink_id}/images",
    response_model=DrinkImageOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def add_drink_image(
    drink_id: str,
    payload: DrinkImageCreate,
    db: AsyncSession = Depends(get_db),
) -> DrinkImage:
    result = await db.execute(select(Drink).where(Drink.id == drink_id))
    drink = result.scalar_one_or_none()
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    if payload.position < 1 or payload.position > 3:
        raise HTTPException(status_code=400, detail="Image position must be 1-3.")
    image = DrinkImage(drink_id=drink_id, url=payload.url, position=payload.position)
    db.add(image)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Image position already used.")
    await db.refresh(image)
    return image


@router.post(
    "/uploads",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def upload_image(
    file: UploadFile = File(...),
) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed.")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(UPLOAD_DIR, filename)
    contents = await file.read()
    with open(target_path, "wb") as buffer:
        buffer.write(contents)
    return {"url": f"/uploads/{filename}"}
