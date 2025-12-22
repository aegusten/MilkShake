from typing import Optional
from pydantic import BaseModel


class ItemMasterBase(BaseModel):
    name: str


class ItemMasterCreate(ItemMasterBase):
    pass


class ItemMasterUpdate(BaseModel):
    name: Optional[str] = None


class ItemMasterOut(ItemMasterBase):
    id: str

    class Config:
        from_attributes = True
