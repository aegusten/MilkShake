from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    payload: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminLoginResponse:
    token, expires_in = await auth_service.authenticate_admin(
        db, payload.email, payload.password
    )
    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )
