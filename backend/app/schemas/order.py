from datetime import datetime, timezone
from typing import Annotated, List, Literal, Optional

from pydantic import AfterValidator, BaseModel, Field, StringConstraints, field_validator


def _as_utc(value: datetime) -> datetime:
    # Columns are TIMESTAMP without time zone, written by Postgres now() in
    # UTC. Mark them as UTC so browsers don't read them as local time.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]

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
    created_at: UtcDatetime
    accepted_at: Optional[UtcDatetime] = None
    ready_at: Optional[UtcDatetime] = None
    completed_at: Optional[UtcDatetime] = None
    cancelled_at: Optional[UtcDatetime] = None
    items: List[OrderItemOut]
    total: float


class GuestOrderOut(BaseModel):
    """What the guest who placed the order may see. No name or phone."""

    id: str
    ticket: str
    status: OrderStatus
    created_at: UtcDatetime
    items: List[OrderItemOut]
    total: float


class DisplayTicketOut(BaseModel):
    ticket: str
    ready_at: Optional[UtcDatetime] = None
