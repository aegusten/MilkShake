from datetime import datetime
from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator

OrderStatus = Literal["pending", "accepted", "ready", "completed", "cancelled"]


class OrderItemCreate(BaseModel):
    drink_id: str
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    guest_name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
    ] = None
    phone: Optional[str] = None
    items: List[OrderItemCreate]

    @field_validator("guest_name")
    @classmethod
    def _blank_name_is_none(cls, value: Optional[str]) -> Optional[str]:
        return value or None


class OrderItemOut(BaseModel):
    drink_id: str
    drink_name: str
    quantity: int
    price: float
    line_total: float


class OrderOut(BaseModel):
    """Full order, for staff."""

    id: str
    ticket_number: int
    ticket: str
    guest_name: Optional[str] = None
    phone: Optional[str] = None
    status: OrderStatus
    created_at: datetime
    accepted_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    items: List[OrderItemOut]
    total: float


class GuestOrderOut(BaseModel):
    """What the guest who placed the order may see. No name or phone."""

    id: str
    ticket: str
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemOut]
    total: float


class DisplayTicketOut(BaseModel):
    ticket: str
    ready_at: Optional[datetime] = None
