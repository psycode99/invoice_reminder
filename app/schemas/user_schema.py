from pydantic import BaseModel, EmailStr, HttpUrl
from uuid import UUID
from datetime import datetime


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: HttpUrl | None = None
    auth_provider: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
