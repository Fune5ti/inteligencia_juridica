from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'cases',
        sa.Column('case_id', sa.String(length=100), primary_key=True),
        sa.Column('resume', sa.Text(), nullable=False),
    )
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_id', sa.String(length=100), sa.ForeignKey('cases.case_id', ondelete='CASCADE'), index=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('event_date', sa.String(length=40), nullable=False),
        sa.Column('event_page_init', sa.Integer(), nullable=False),
        sa.Column('event_page_end', sa.Integer(), nullable=False),
    )
    op.create_table(
        'evidences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_id', sa.String(length=100), sa.ForeignKey('cases.case_id', ondelete='CASCADE'), index=True),
        sa.Column('evidence_id', sa.Integer(), nullable=False),
        sa.Column('evidence_name', sa.String(length=255), nullable=False),
        sa.Column('evidence_flaw', sa.Text(), nullable=False),
        sa.Column('evidence_page_init', sa.Integer(), nullable=False),
        sa.Column('evidence_page_end', sa.Integer(), nullable=False),
    )

def downgrade():
    op.drop_table('evidences')
    op.drop_table('timeline_events')
    op.drop_table('cases')
