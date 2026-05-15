from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemMasterBase(BaseModel):
    name: str


class ItemMasterCreate(ItemMasterBase):
    pass


class ItemMasterUpdate(BaseModel):
    name: Optional[str] = None


class ItemMasterOut(ItemMasterBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
