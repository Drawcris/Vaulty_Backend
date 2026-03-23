"""add filename to files

Revision ID: b7f91c2d4e6a
Revises: a13d9b1b2c3d
Create Date: 2026-03-23 16:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7f91c2d4e6a'
down_revision: Union[str, Sequence[str], None] = 'a13d9b1b2c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('files', sa.Column('filename', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_files_filename'), 'files', ['filename'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_files_filename'), table_name='files')
    op.drop_column('files', 'filename')
