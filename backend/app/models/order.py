# backend/app/models/order.py
import uuid
from sqlalchemy import Column, TEXT, TIMESTAMP, text, Numeric, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Order(Base):
    __tablename__ = "orders"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guest_name = Column(TEXT, nullable=False)
    phone      = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    items = relationship("OrderItem", back_populates="order", cascade="all, delete")

class OrderItem(Base):
    __tablename__ = "order_items"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True),
                      ForeignKey("orders.id", ondelete="CASCADE"),
                      nullable=False)
    drink_id = Column(UUID(as_uuid=True),
                      ForeignKey("drinks.id", ondelete="RESTRICT"),
                      nullable=False)
    quantity = Column(Integer, nullable=False)
    price    = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    drink = relationship("Drink")

    __table_args__ = (
        UniqueConstraint("order_id", "drink_id", name="uq_order_drink_once"),
        Index("idx_order_items_order", "order_id"),
        Index("idx_order_items_drink", "drink_id"),
    )
