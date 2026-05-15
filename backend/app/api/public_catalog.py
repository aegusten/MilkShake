from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.drink import Drink
from app.models.item_master import ItemMaster
from app.schemas.drink import DrinkOut
from app.schemas.item_master import ItemMasterOut

router = APIRouter()


@router.get("/item-masters", response_model=List[ItemMasterOut])
async def list_item_masters(db: AsyncSession = Depends(get_db)) -> list[ItemMaster]:
    result = await db.execute(select(ItemMaster).order_by(ItemMaster.sort_order))
    return list(result.scalars().all())


@router.get("/drinks", response_model=List[DrinkOut])
async def list_drinks(
    item_master_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[Drink]:
    stmt = (
        select(Drink)
        .options(selectinload(Drink.item_masters))
        .order_by(Drink.created_at.desc())
    )
    if item_master_id:
        stmt = stmt.join(Drink.item_masters).where(ItemMaster.id == item_master_id)
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
