from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse
from app.utils.security import verify_password

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == payload.email.lower()).one_or_none()
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
