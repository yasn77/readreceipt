"""Add admin user and audit log tables.

Revision ID: a1b2c3d4e5f6
Revises: 57b703eb7a0a
Create Date: 2026-03-07 20:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '57b703eb7a0a'
branch_labels = None
depends_on = None


def upgrade():
    # Create admin_user table
    op.create_table(
        'admin_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('oidc_sub', sa.String(length=255), nullable=False),
        sa.Column('roles', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_user_email', 'admin_user', ['email'], unique=True)
    op.create_index('ix_admin_user_oidc_sub', 'admin_user', ['oidc_sub'], unique=True)

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('ix_audit_log_admin_user_id', 'audit_log', ['admin_user_id'])


def downgrade():
    op.drop_index('ix_audit_log_admin_user_id', table_name='audit_log')
    op.drop_index('ix_audit_log_timestamp', table_name='audit_log')
    op.drop_table('audit_log')
    
    op.drop_index('ix_admin_user_oidc_sub', table_name='admin_user')
    op.drop_index('ix_admin_user_email', table_name='admin_user')
    op.drop_table('admin_user')
