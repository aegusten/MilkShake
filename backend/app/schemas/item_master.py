from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemMasterBase(BaseModel):
    name: str


class ItemMasterCreate(ItemMasterBase):
    pass


class ItemMasterUpdate(BaseModel):
    name: str | None = None


class ItemMasterOut(ItemMasterBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
