# backend/app/models/drink_image.py
import uuid
from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class DrinkImage(Base):
    __tablename__ = "drink_images"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drink_id  = Column(UUID(as_uuid=True),
                       ForeignKey("drinks.id", ondelete="CASCADE"),
                       nullable=False)
    url       = Column(TEXT, nullable=False)
    position  = Column(Integer, nullable=False)
    created_at= Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    drink = relationship("Drink", back_populates="images")

    __table_args__ = (
        CheckConstraint("position BETWEEN 1 AND 3", name="ck_drink_images_pos"),
        UniqueConstraint("drink_id", "position", name="uq_drink_images_unique"),
    )
