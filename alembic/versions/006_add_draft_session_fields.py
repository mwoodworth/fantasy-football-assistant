"""Add draft session fields

Revision ID: 006_add_draft_session_fields
Revises: 005_add_user_league_settings
Create Date: 2025-07-09 19:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_draft_session_fields'
down_revision = '005_add_user_league_settings'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to draft_sessions table
    with op.batch_alter_table('draft_sessions') as batch_op:
        # Add draft status tracking
        batch_op.add_column(sa.Column('draft_status', sa.String(50), nullable=True, server_default='pending'))
        batch_op.add_column(sa.Column('current_pick_team_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('pick_deadline', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_espn_sync', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('sync_errors', sa.JSON(), nullable=True))
        
        # Add available players cache
        batch_op.add_column(sa.Column('available_players', sa.JSON(), nullable=True))
        
        # Add recommendation tracking
        batch_op.add_column(sa.Column('last_recommendation_time', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('recommendation_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Remove the columns
    with op.batch_alter_table('draft_sessions') as batch_op:
        batch_op.drop_column('draft_status')
        batch_op.drop_column('current_pick_team_id')
        batch_op.drop_column('pick_deadline')
        batch_op.drop_column('last_espn_sync')
        batch_op.drop_column('sync_errors')
        batch_op.drop_column('available_players')
        batch_op.drop_column('last_recommendation_time')
        batch_op.drop_column('recommendation_count')