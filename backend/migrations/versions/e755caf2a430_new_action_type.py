import sqlmodel
"""new action type

Revision ID: e755caf2a430
Revises: 6f11ec5e283e
Create Date: 2025-06-24 01:43:25.475942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e755caf2a430'
down_revision: Union[str, Sequence[str], None] = '6f11ec5e283e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE action_type ADD VALUE 'TOUR_CONFIRMED'")
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
