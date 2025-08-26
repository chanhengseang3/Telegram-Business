"""add_shift_permissions_table_only

Revision ID: add_shift_permissions_only
Revises: 60f1d60953b0
Create Date: 2025-08-25 04:50:00.000000+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_shift_permissions_only'
down_revision: Union[str, Sequence[str], None] = '60f1d60953b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create shift_permissions table
    op.create_table('shift_permissions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create unique constraint on chat_id + username
    op.create_index('idx_shift_permissions_chat_username', 'shift_permissions', ['chat_id', 'username'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table
    op.drop_index('idx_shift_permissions_chat_username', table_name='shift_permissions')
    op.drop_table('shift_permissions')