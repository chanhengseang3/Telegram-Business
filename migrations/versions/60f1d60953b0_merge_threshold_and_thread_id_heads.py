"""merge threshold and thread_id heads

Revision ID: 60f1d60953b0
Revises: 70055f5b9b3d, k6l7m8n9o0p1
Create Date: 2025-08-20 13:06:40.452700+07:00

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '60f1d60953b0'
down_revision: Union[str, Sequence[str], None] = ('70055f5b9b3d', 'k6l7m8n9o0p1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
