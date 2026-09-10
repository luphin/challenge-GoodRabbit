"""agregar status a employees (soft delete)

Revision ID: 9bd019696898
Revises: 88f915f7400b
Create Date: 2026-09-09 21:12:13.217207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bd019696898'
down_revision: Union[str, Sequence[str], None] = '88f915f7400b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'employees',
        sa.Column('status', sa.String(), server_default='active', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('employees', 'status')
