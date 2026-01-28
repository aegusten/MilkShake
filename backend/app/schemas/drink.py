from typing import List, Optional
from pydantic import BaseModel, constr
from uuid import UUID
from .item_master import ItemMasterOut


class DrinkBase(BaseModel):
    name: str
    description: Optional[constr(max_length=160)] = None
    price: float
    type: str = "other"
    image_cover: Optional[str] = None


class DrinkCreate(DrinkBase):
    item_master_ids: List[str]


class DrinkUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[constr(max_length=160)] = None
    price: Optional[float] = None
    type: Optional[str] = None
    image_cover: Optional[str] = None
    item_master_ids: Optional[List[str]] = None


class DrinkOut(DrinkBase):
    id: UUID
    item_masters: List[ItemMasterOut] = []

    class Config:
        from_attributes = True


class DrinkImageCreate(BaseModel):
    url: str
    position: int


class DrinkImageOut(DrinkImageCreate):
    id: UUID

    class Config:
        from_attributes = True
