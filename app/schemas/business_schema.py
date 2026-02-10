from pydantic import BaseModel, EmailStr, HttpUrl
from uuid import UUID
from datetime import datetime


class BusinessCreate(BaseModel):
    name: str
    legal_name: str | None = None
    tax_id: str | None = None

    currency: str  # ISO 4217

    email: EmailStr | None = None
    phone: str | None = None
    website: HttpUrl | None = None

    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    logo_url: HttpUrl | None = None
    timezone: str | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None

    currency: str | None = None

    email: EmailStr | None = None
    phone: str | None = None
    website: HttpUrl | None = None

    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    logo_url: HttpUrl | None = None
    timezone: str | None = None

    is_active: bool | None = None


class BusinessResponse(BaseModel):
    id: UUID
    owner_id: UUID

    name: str
    legal_name: str | None
    tax_id: str | None

    currency: str

    email: EmailStr | None
    phone: str | None
    website: HttpUrl | None

    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None

    logo_url: HttpUrl | None
    timezone: str

    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
