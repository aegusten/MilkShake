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
