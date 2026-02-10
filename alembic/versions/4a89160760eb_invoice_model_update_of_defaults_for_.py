"""invoice model update of defaults for status

Revision ID: 4a89160760eb
Revises: 9dacf40b23c5
Create Date: 2026-02-10 11:33:40.667063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a89160760eb'
down_revision: Union[str, Sequence[str], None] = '9dacf40b23c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""

    # status default
    op.alter_column(
        "invoices",
        "status",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default="pending",
    )

    # payment_status default
    op.alter_column(
        "invoices",
        "payment_status",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default="unpaid",
    )

def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "invoices",
        "payment_status",
        existing_type=sa.String(length=50),
        server_default=None,
    )

    op.alter_column(
        "invoices",
        "status",
        existing_type=sa.String(length=50),
        server_default=None,
    )

