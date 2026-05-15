from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse
from app.utils.security import verify_password

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    payload: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminLoginResponse:
    result = await db.execute(
        select(Admin).where(Admin.email == payload.email.lower())
    )
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account disabled.",
        )
    return AdminLoginResponse(ok=True, admin_id=str(admin.id))
