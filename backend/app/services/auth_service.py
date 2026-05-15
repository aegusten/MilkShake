import uuid

from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.errors import ForbiddenError, UnauthorizedError
from app.utils.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)


async def authenticate_admin(
    session: AsyncSession, email: str, password: str
) -> tuple[str, int]:
    """Verify credentials and issue an access token.

    Returns ``(access_token, expires_in_seconds)``. Raises
    :class:`UnauthorizedError` for bad credentials and
    :class:`ForbiddenError` for a disabled account.
    """
    result = await session.execute(
        select(Admin).where(Admin.email == email.lower())
    )
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(password, admin.password_hash):
        raise UnauthorizedError("Invalid credentials.")
    if not admin.is_active:
        raise ForbiddenError("Admin account disabled.")
    return create_access_token(admin.id)


async def verify_access_token(
    session: AsyncSession, token: str | None
) -> Admin:
    """Decode an access token, load the matching admin, and return it.

    Raises :class:`UnauthorizedError` if the token is missing, malformed,
    expired, or references an unknown admin. Raises :class:`ForbiddenError`
    if the admin exists but is disabled.
    """
    if not token:
        raise UnauthorizedError("Admin credentials required.")
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    try:
        admin_uuid = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token subject.") from exc
    result = await session.execute(select(Admin).where(Admin.id == admin_uuid))
    admin = result.scalar_one_or_none()
    if not admin:
        raise UnauthorizedError("Admin not found.")
    if not admin.is_active:
        raise ForbiddenError("Admin access disabled.")
    return admin
