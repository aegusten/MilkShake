from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .item_master import ItemMasterOut


class DrinkBase(BaseModel):
    name: str
    description: str | None = Field(default=None, max_length=160)
    price: float
    type: str = "other"
    image_cover: str | None = None


class DrinkCreate(DrinkBase):
    item_master_ids: list[str]


class DrinkUpdate(BaseModel):
    name: str | None = None
    description: str | None = Field(default=None, max_length=160)
    price: float | None = None
    type: str | None = None
    image_cover: str | None = None
    item_master_ids: list[str] | None = None


class DrinkOut(DrinkBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_masters: list[ItemMasterOut] = []


class DrinkImageCreate(BaseModel):
    url: str
    position: int


class DrinkImageOut(DrinkImageCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
