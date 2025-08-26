"""add_threshold_columns_to_chat_group

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2025-08-19 14:15:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade():
    # Add threshold columns to chat_group table
    op.add_column('chat_group', sa.Column('usd_threshold', sa.Numeric(10, 2), nullable=True))
    op.add_column('chat_group', sa.Column('khr_threshold', sa.Numeric(15, 2), nullable=True))


def downgrade():
    # Remove threshold columns from chat_group table
    op.drop_column('chat_group', 'khr_threshold')
    op.drop_column('chat_group', 'usd_threshold')