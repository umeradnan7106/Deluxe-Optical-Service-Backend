"""add color_name to product_images and sub_options to lens_options

Revision ID: a1b2c3d4e5f6
Revises: 24c22feaa7c6
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '24c22feaa7c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('product_images', sa.Column('color_name', sa.String(100), nullable=True))
    op.add_column('lens_options', sa.Column('sub_options', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('product_images', 'color_name')
    op.drop_column('lens_options', 'sub_options')
