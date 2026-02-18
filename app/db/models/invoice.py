import uuid
from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        index=True,
    )

    invoice_number: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # draft, sent, cancelled

    currency: Mapped[str] = mapped_column(String(3))

    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_company: Mapped[str | None] = mapped_column(String(255))

    subtotal_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2))

    issue_date: Mapped[Date] = mapped_column(Date)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    payment_status: Mapped[str] = mapped_column(
        String(50), default="unpaid"
    )  # unpaid, paid, overdue, partial
    payment_method: Mapped[str | None] = mapped_column(String(50))

    notes: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)

    last_reminder_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_reminder_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    business: Mapped["Business"] = relationship(back_populates="invoices")  # type: ignore
