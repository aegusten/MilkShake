import argparse
import getpass

from app.db import SessionLocal
from app.models.admin import Admin
from app.utils.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", help="Admin password (optional; will prompt if missing)")
    parser.add_argument("--force", action="store_true", help="Overwrite if admin exists")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if not password:
        raise SystemExit("Password is required.")

    session = SessionLocal()
    try:
        email = args.email.strip().lower()
        existing = session.query(Admin).filter(Admin.email == email).one_or_none()
        if existing and not args.force:
            raise SystemExit("Admin already exists. Use --force to overwrite.")

        if existing and args.force:
            existing.password_hash = hash_password(password)
            existing.is_active = True
            session.add(existing)
        else:
            admin = Admin(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
            )
            session.add(admin)

        session.commit()
        print("Admin user saved.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
