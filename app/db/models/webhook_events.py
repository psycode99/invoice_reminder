from datetime import datetime, UTC
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # CloudEvent id from provider
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    # provider name (qbo, xero, freshbooks etc.)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    
    company_id: Mapped[str] = mapped_column(String(64), index=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )