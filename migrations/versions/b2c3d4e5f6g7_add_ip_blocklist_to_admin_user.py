"""
Add ip_blocklist column to admin_user table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-08 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ip_blocklist column to admin_user table."""
    # Add ip_blocklist column as JSON type
    op.add_column(
        'admin_user',
        sa.Column('ip_blocklist', sa.JSON(), nullable=True, default=[])
    )

    # Set default value for existing rows
    op.execute("UPDATE admin_user SET ip_blocklist = '[]' WHERE ip_blocklist IS NULL")


def downgrade() -> None:
    """Remove ip_blocklist column from admin_user table."""
    op.drop_column('admin_user', 'ip_blocklist')
