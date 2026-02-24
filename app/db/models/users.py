import uuid
from sqlalchemy import (
    Boolean,
    String,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    auth_provider: Mapped[str] = mapped_column(String(50))
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    full_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(512))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    businesses: Mapped[list["Business"]] = relationship(  # type: ignore
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # type: ignore
        back_populates="user", cascade="all, delete-orphan"
    )
