import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models.admin import Admin
from app.utils.security import hash_password


async def create_or_update_admin(email: str, password: str, force: bool) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin).where(Admin.email == email))
        existing = result.scalar_one_or_none()

        if existing and not force:
            raise SystemExit("Admin already exists. Use --force to overwrite.")

        if existing and force:
            existing.password_hash = hash_password(password)
            existing.is_active = True
        else:
            session.add(
                Admin(
                    email=email,
                    password_hash=hash_password(password),
                    is_active=True,
                )
            )

        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", help="Admin password (optional; will prompt if missing)")
    parser.add_argument("--force", action="store_true", help="Overwrite if admin exists")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if not password:
        raise SystemExit("Password is required.")

    email = args.email.strip().lower()
    asyncio.run(create_or_update_admin(email, password, args.force))
    print("Admin user saved.")


if __name__ == "__main__":
    main()
