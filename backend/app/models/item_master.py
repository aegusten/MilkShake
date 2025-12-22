# backend/app/models/item_master.py
import uuid
from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, text, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

item_master_drinks = Table(
    "item_master_drinks",
    Base.metadata,
    Column("item_master_id", UUID(as_uuid=True), ForeignKey("item_masters.id", ondelete="CASCADE"), primary_key=True),
    Column("drink_id", UUID(as_uuid=True), ForeignKey("drinks.id", ondelete="CASCADE"), primary_key=True),
)


class ItemMaster(Base):
    __tablename__ = "item_masters"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(TEXT, nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    drinks = relationship(
        "Drink",
        secondary=item_master_drinks,
        back_populates="item_masters",
    )
