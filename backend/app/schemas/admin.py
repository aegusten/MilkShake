from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    ok: bool
    admin_id: str
