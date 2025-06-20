# backend/app/models/admin.py
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, TIMESTAMP, TEXT
)
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Admin(Base):
    __tablename__ = "admins"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(TEXT, nullable=False, unique=True)
    password_hash = Column(TEXT, nullable=False)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(TIMESTAMP, nullable=False, server_default=text("now()"))
