from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = '0002_add_extraction_jobs'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'extraction_jobs',
        sa.Column('id', sa.String(length=50), primary_key=True),
        sa.Column('case_id', sa.String(length=100), index=True, nullable=False),
        sa.Column('status', sa.String(length=20), index=True, nullable=False),
        sa.Column('callback_url', sa.String(length=500), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table('extraction_jobs')
