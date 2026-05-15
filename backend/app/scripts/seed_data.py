"""Seed a fresh database with a default admin + sample catalog.

Intended for local development and demos. Idempotent: a second run skips
anything that already exists. For production, use ``create_superuser``
with explicit credentials and add real menu items via the admin UI.

Usage:
    docker compose exec backend python -m app.scripts.seed_data
"""

import asyncio
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select

from app.db import AsyncSessionLocal

# Import every model so SQLAlchemy can resolve string-based relationships
# (e.g. Drink -> DrinkImage) when the seed runs in isolation.
from app.models import admin as _admin_mod  # noqa: F401
from app.models import drink as _drink_mod  # noqa: F401
from app.models import drink_image as _drink_image_mod  # noqa: F401
from app.models import item_master as _item_master_mod  # noqa: F401
from app.models import order as _order_mod  # noqa: F401
from app.models.admin import Admin
from app.models.drink import Drink
from app.models.item_master import ItemMaster
from app.utils.security import hash_password

DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123"


class ItemMasterSpec(TypedDict):
    name: str
    sort_order: int


class DrinkSpec(TypedDict):
    name: str
    description: str
    price: Decimal
    type: str
    item_master: str


SAMPLE_ITEM_MASTERS: list[ItemMasterSpec] = [
    {"name": "Milkshakes", "sort_order": 10},
    {"name": "Cocktails", "sort_order": 20},
    {"name": "Soft drinks", "sort_order": 30},
]


SAMPLE_DRINKS: list[DrinkSpec] = [
    {
        "name": "Vanilla Shake",
        "description": "Classic vanilla bean ice cream blended with milk.",
        "price": Decimal("25000"),
        "type": "milkshake",
        "item_master": "Milkshakes",
    },
    {
        "name": "Strawberry Shake",
        "description": "Fresh strawberries, sweet, topped with whipped cream.",
        "price": Decimal("27000"),
        "type": "milkshake",
        "item_master": "Milkshakes",
    },
    {
        "name": "Mojito",
        "description": "Lime, mint, soda. Non-alcoholic.",
        "price": Decimal("32000"),
        "type": "cocktail",
        "item_master": "Cocktails",
    },
    {
        "name": "Blue Lagoon",
        "description": "Blue curacao syrup, lemonade, ice.",
        "price": Decimal("35000"),
        "type": "cocktail",
        "item_master": "Cocktails",
    },
    {
        "name": "Cola",
        "description": "Chilled, served with ice.",
        "price": Decimal("10000"),
        "type": "soft",
        "item_master": "Soft drinks",
    },
    {
        "name": "Sparkling Water",
        "description": "Lightly carbonated, lemon wedge.",
        "price": Decimal("8000"),
        "type": "soft",
        "item_master": "Soft drinks",
    },
]


async def _seed_admin(session) -> None:
    result = await session.execute(
        select(Admin).where(Admin.email == DEFAULT_ADMIN_EMAIL)
    )
    if result.scalar_one_or_none():
        print(f"  · admin {DEFAULT_ADMIN_EMAIL} already exists, skipping")
        return
    session.add(
        Admin(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            is_active=True,
        )
    )
    await session.commit()
    print(
        f"  + created admin {DEFAULT_ADMIN_EMAIL} "
        f"(password: {DEFAULT_ADMIN_PASSWORD})"
    )


async def _seed_item_masters(session) -> dict[str, ItemMaster]:
    created: dict[str, ItemMaster] = {}
    for spec in SAMPLE_ITEM_MASTERS:
        result = await session.execute(
            select(ItemMaster).where(ItemMaster.name == spec["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  · item master '{spec['name']}' already exists, skipping")
            created[spec["name"]] = existing
            continue
        im = ItemMaster(name=spec["name"], sort_order=spec["sort_order"])
        session.add(im)
        await session.commit()
        await session.refresh(im)
        created[spec["name"]] = im
        print(f"  + created item master '{spec['name']}'")
    return created


async def _seed_drinks(
    session, item_masters: dict[str, ItemMaster]
) -> None:
    for spec in SAMPLE_DRINKS:
        result = await session.execute(
            select(Drink).where(Drink.name == spec["name"])
        )
        if result.scalar_one_or_none():
            print(f"  · drink '{spec['name']}' already exists, skipping")
            continue
        drink = Drink(
            name=spec["name"],
            description=spec["description"],
            price=spec["price"],
            type=spec["type"],
        )
        drink.item_masters = [item_masters[spec["item_master"]]]
        session.add(drink)
        await session.commit()
        print(f"  + created drink '{spec['name']}'")


async def _seed_async() -> None:
    async with AsyncSessionLocal() as session:
        print("Seeding admin:")
        await _seed_admin(session)
        print("Seeding item masters:")
        item_masters = await _seed_item_masters(session)
        print("Seeding drinks:")
        await _seed_drinks(session, item_masters)


def main() -> None:
    asyncio.run(_seed_async())
    print("\nSeed complete.")
    print(
        f"Log in at /admin with {DEFAULT_ADMIN_EMAIL} / "
        f"{DEFAULT_ADMIN_PASSWORD} and change the password before launch."
    )


if __name__ == "__main__":
    main()
