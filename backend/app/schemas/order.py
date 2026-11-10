from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, StringConstraints, field_validator


def _as_utc(value: datetime) -> datetime:
    # Columns are TIMESTAMP without time zone, written by Postgres now() in
    # UTC. Mark them as UTC so browsers don't read them as local time.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]

OrderStatus = Literal["pending", "accepted", "ready", "completed", "cancelled"]


class OrderItemCreate(BaseModel):
    drink_id: str
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    guest_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] | None = None
    phone: str | None = None
    items: list[OrderItemCreate]

    @field_validator("guest_name")
    @classmethod
    def _blank_name_is_none(cls, value: str | None) -> str | None:
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
    guest_name: str | None = None
    phone: str | None = None
    status: OrderStatus
    created_at: UtcDatetime
    accepted_at: UtcDatetime | None = None
    ready_at: UtcDatetime | None = None
    completed_at: UtcDatetime | None = None
    cancelled_at: UtcDatetime | None = None
    items: list[OrderItemOut]
    total: float


class GuestOrderOut(BaseModel):
    """What the guest who placed the order may see. No name or phone."""

    id: str
    ticket: str
    status: OrderStatus
    created_at: UtcDatetime
    items: list[OrderItemOut]
    total: float


class DisplayTicketOut(BaseModel):
    ticket: str
    ready_at: UtcDatetime | None = None
