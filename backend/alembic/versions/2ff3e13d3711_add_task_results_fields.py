"""add_task_results_fields

Revision ID: 2ff3e13d3711
Revises: 65381f53ee81
Create Date: 2026-04-15 13:15:30.703110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ff3e13d3711'
down_revision: Union[str, None] = '65381f53ee81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add output, error, and execution_time columns to tasks table
    op.add_column('tasks', sa.Column('output', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('error', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column(
        'execution_time', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove output, error, and execution_time columns from tasks table
    op.drop_column('tasks', 'execution_time')
    op.drop_column('tasks', 'error')
    op.drop_column('tasks', 'output')
