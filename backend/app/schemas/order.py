from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, StringConstraints


class OrderItemCreate(BaseModel):
    drink_id: str
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    guest_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1)
    ]
    phone: Optional[str] = None
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    drink_id: str
    drink_name: str
    quantity: int
    price: float
    line_total: float


class OrderOut(BaseModel):
    id: str
    guest_name: str
    phone: Optional[str] = None
    created_at: datetime
    status: str
    items: List[OrderItemOut]
    total: float
