# backend/app/models/enums.py
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import ENUM

# Postgres native ENUM for drink_type
DRINK_TYPE = Enum(
    "soft",
    "milkshake",
    "cocktail",
    "other",
    name="drink_type",
    native_enum=True,
    create_type=True,  
    inherit_schema=True
)

# Order lifecycle. See docs/BUSINESS_LOGIC.md for the allowed transitions.
ORDER_STATUSES = ("pending", "accepted", "ready", "completed", "cancelled")

ORDER_STATUS = Enum(
    *ORDER_STATUSES,
    name="order_status",
    native_enum=True,
    create_type=True,
)
