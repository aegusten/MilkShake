# backend/app/models/drink.py
import uuid
from decimal import Decimal
from sqlalchemy import (
    Column, TEXT, Numeric, TIMESTAMP, text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
from .enums import DRINK_TYPE

class Drink(Base):
    __tablename__ = "drinks"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(TEXT, nullable=False)
    description = Column(TEXT)
    price       = Column(Numeric(10, 2), nullable=False)
    type        = Column(DRINK_TYPE, nullable=False, server_default="other")
    image_cover = Column(TEXT)
    created_at  = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    item_masters = relationship(
        "ItemMaster",
        secondary="item_master_drinks",
        back_populates="drinks",
    )
    images   = relationship("DrinkImage", back_populates="drink", cascade="all, delete")

Index("idx_drinks_type", Drink.type)
