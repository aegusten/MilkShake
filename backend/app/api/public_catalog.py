from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.item_master import ItemMaster
from app.models.drink import Drink
from app.schemas.item_master import ItemMasterOut
from app.schemas.drink import DrinkOut

router = APIRouter()


@router.get("/item-masters", response_model=List[ItemMasterOut])
def list_item_masters(db: Session = Depends(get_db)):
    return db.query(ItemMaster).order_by(ItemMaster.sort_order).all()


@router.get("/drinks", response_model=List[DrinkOut])
def list_drinks(item_master_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Drink).order_by(Drink.created_at.desc())
    if item_master_id:
        query = query.join(Drink.item_masters).filter(ItemMaster.id == item_master_id)
    return query.all()
