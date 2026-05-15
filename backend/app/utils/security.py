from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext

from app.config import get_settings
from app.schemas.admin import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(admin_id: UUID | str) -> tuple[str, int]:
    """Issue a signed access token for the given admin.

    Returns the encoded JWT and the TTL in seconds (for the client to compute
    its own local expiry).
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    payload = {
        "sub": str(admin_id),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, settings.JWT_ACCESS_TTL_MINUTES * 60


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate an access token.

    Raises ``jwt.InvalidTokenError`` (or a subclass like
    ``ExpiredSignatureError``) if the token is invalid, expired, or the wrong
    type.
    """
    settings = get_settings()
    raw = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    payload = TokenPayload(**raw)
    if payload.type != "access":
        raise InvalidTokenError("Wrong token type.")
    return payload
