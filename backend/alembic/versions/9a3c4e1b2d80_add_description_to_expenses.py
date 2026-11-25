"""add_description_to_expenses

Revision ID: 9a3c4e1b2d80
Revises: 5d17ffdbe907
Create Date: 2026-11-25 19:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a3c4e1b2d80'
down_revision: Union[str, None] = '5d17ffdbe907'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('expenses', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('expenses', 'description')
