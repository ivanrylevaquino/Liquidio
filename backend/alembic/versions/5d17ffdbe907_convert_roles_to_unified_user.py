"""convert_roles_to_unified_user

Revision ID: 5d17ffdbe907
Revises: f3347212e5a9
Create Date: 2026-11-24 23:43:28.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d17ffdbe907'
down_revision: Union[str, None] = 'f3347212e5a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert all existing legacy role rows to the unified 'USER' role
    op.execute("UPDATE users SET role = 'USER' WHERE role IN ('ADMIN', 'ENCODER', 'APPROVER')")


def downgrade() -> None:
    pass
