from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.drink import DrinkOut
from app.schemas.item_master import ItemMasterOut
from app.services import catalog_service

router = APIRouter()


@router.get("/item-masters", response_model=list[ItemMasterOut])
async def list_item_masters(db: AsyncSession = Depends(get_db)):
    return await catalog_service.list_item_masters(db)


@router.get("/drinks", response_model=list[DrinkOut])
async def list_drinks(
    item_master_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    parsed: UUID | None = None
    if item_master_id:
        try:
            parsed = UUID(item_master_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid item_master_id."
            ) from exc
    return await catalog_service.list_drinks(db, parsed)
