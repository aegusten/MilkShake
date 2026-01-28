from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class ItemMasterBase(BaseModel):
    name: str


class ItemMasterCreate(ItemMasterBase):
    pass


class ItemMasterUpdate(BaseModel):
    name: Optional[str] = None


class ItemMasterOut(ItemMasterBase):
    id: UUID

    class Config:
        from_attributes = True
