import pytest

from app.models.admin import Admin
from app.services import auth_service
from app.services.errors import ForbiddenError, UnauthorizedError
from app.utils.security import hash_password


async def _seed_admin(
    session, *, email: str = "test@example.com", password: str = "Password123",
    active: bool = True,
) -> Admin:
    admin = Admin(
        email=email,
        password_hash=hash_password(password),
        is_active=active,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def test_authenticate_with_correct_credentials_issues_token(session):
    await _seed_admin(session)

    token, expires_in = await auth_service.authenticate_admin(
        session, "test@example.com", "Password123"
    )

    assert isinstance(token, str) and token.count(".") == 2
    assert expires_in > 0


async def test_authenticate_with_wrong_password_raises_unauthorized(session):
    await _seed_admin(session)

    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate_admin(
            session, "test@example.com", "wrong-password"
        )


async def test_authenticate_disabled_account_raises_forbidden(session):
    await _seed_admin(session, active=False)

    with pytest.raises(ForbiddenError):
        await auth_service.authenticate_admin(
            session, "test@example.com", "Password123"
        )


async def test_verify_access_token_round_trips(session):
    seeded = await _seed_admin(session)
    token, _ = await auth_service.authenticate_admin(
        session, "test@example.com", "Password123"
    )

    loaded = await auth_service.verify_access_token(session, token)

    assert loaded.id == seeded.id


async def test_verify_access_token_rejects_missing_token(session):
    with pytest.raises(UnauthorizedError):
        await auth_service.verify_access_token(session, None)


async def test_verify_access_token_rejects_garbage(session):
    with pytest.raises(UnauthorizedError):
        await auth_service.verify_access_token(session, "not-a-real-jwt")
