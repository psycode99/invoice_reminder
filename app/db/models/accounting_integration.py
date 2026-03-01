from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccountingIntegration(Base):
    __tablename__ = "accounting_integrations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # "qbo", "xero", "freshbooks"

    access_token: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    refresh_token: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    company_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # realm_id (QBO) or tenant_id (Xero)

    connected: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship
    business: Mapped["Business"] = relationship(back_populates="accounting_integrations") # type: ignore
    invoices: Mapped["Invoice"] = relationship(back_populates="accounting_integration") # type: ignore

    __table_args__ = (
    UniqueConstraint(
        "business_id",
        "provider",
        name="uq_business_provider",
    ),
)