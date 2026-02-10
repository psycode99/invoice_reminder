from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import date, datetime


class InvoiceCreate(BaseModel):
    business_id: UUID

    invoice_number: str
    currency: str

    customer_name: str
    customer_email: EmailStr | None = None
    customer_company: str | None = None

    subtotal_amount: float
    tax_amount: float
    total_amount: float

    issue_date: date
    due_date: date

    notes: str | None = None
    

class InvoiceUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    payment_method: str | None = None

    customer_name: str | None = None
    customer_email: EmailStr | None = None
    customer_company: str | None = None

    subtotal_amount: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None

    due_date: date | None = None
    paid_at: datetime | None = None

    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    business_id: UUID

    invoice_number: str
    status: str

    currency: str

    customer_name: str
    customer_email: EmailStr | None
    customer_company: str | None

    subtotal_amount: float
    tax_amount: float
    total_amount: float

    issue_date: date
    due_date: date
    paid_at: datetime | None

    payment_status: str
    payment_method: str | None

    notes: str | None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
