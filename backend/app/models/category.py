# backend/app/models/category.py
import uuid
from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class DrinkCategory(Base):
    __tablename__ = "drink_categories"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(TEXT, nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    drinks = relationship("Drink", back_populates="category", cascade="all, delete")
