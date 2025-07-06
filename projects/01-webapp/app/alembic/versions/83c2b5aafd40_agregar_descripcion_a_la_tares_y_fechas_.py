"""agregar descripcion a la tares y fechas de creación y completado

Revision ID: 83c2b5aafd40
Revises:
Create Date: 2025-07-03 18:44:33.713193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83c2b5aafd40'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('task', sa.Column('description', sa.String(), nullable=True))
    op.add_column('task', sa.Column('creation_date', sa.Date(), nullable=True))
    op.add_column('task', sa.Column('done_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass
