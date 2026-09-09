"""renombrar shifts.date a shift_date

Revision ID: 88f915f7400b
Revises: bb99f561dea3
Create Date: 2026-09-08 13:56:36.538046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88f915f7400b'
down_revision: Union[str, Sequence[str], None] = 'bb99f561dea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'shifts',
        'date',
        new_column_name='shift_date',
        existing_type=sa.Date(),
        existing_nullable=False,
    )
    op.drop_index(op.f('ix_shifts_employee_date'), table_name='shifts')
    op.create_index('ix_shifts_employee_shift_date', 'shifts', ['employee_id', 'shift_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_shifts_employee_shift_date', table_name='shifts')
    op.alter_column(
        'shifts',
        'shift_date',
        new_column_name='date',
        existing_type=sa.Date(),
        existing_nullable=False,
    )
    op.create_index(op.f('ix_shifts_employee_date'), 'shifts', ['employee_id', 'date'], unique=False)
