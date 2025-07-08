"""Add ESPN team models and trade recommendations

Revision ID: 003_add_espn_team_models
Revises: 002_add_espn_league_models
Create Date: 2025-07-08 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_espn_team_models'
down_revision = '002_add_espn_league_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create espn_teams table
    op.create_table('espn_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('espn_league_id', sa.Integer(), nullable=False),
        sa.Column('espn_team_id', sa.Integer(), nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('owner_name', sa.String(length=100), nullable=True),
        sa.Column('team_abbreviation', sa.String(length=10), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True, default=0),
        sa.Column('losses', sa.Integer(), nullable=True, default=0),
        sa.Column('ties', sa.Integer(), nullable=True, default=0),
        sa.Column('points_for', sa.Float(), nullable=True, default=0.0),
        sa.Column('points_against', sa.Float(), nullable=True, default=0.0),
        sa.Column('roster_data', sa.JSON(), nullable=True),
        sa.Column('starting_lineup', sa.JSON(), nullable=True),
        sa.Column('bench_players', sa.JSON(), nullable=True),
        sa.Column('position_strengths', sa.JSON(), nullable=True),
        sa.Column('position_depth_scores', sa.JSON(), nullable=True),
        sa.Column('tradeable_assets', sa.JSON(), nullable=True),
        sa.Column('team_needs', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_user_team', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_synced', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('sync_status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('sync_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['espn_league_id'], ['espn_leagues.id'], ),
    )
    op.create_index(op.f('ix_espn_teams_id'), 'espn_teams', ['id'], unique=False)
    op.create_index(op.f('ix_espn_teams_espn_league_id'), 'espn_teams', ['espn_league_id'], unique=False)
    op.create_index(op.f('ix_espn_teams_espn_team_id'), 'espn_teams', ['espn_team_id'], unique=False)

    # Create trade_recommendations table
    op.create_table('trade_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_team_id', sa.Integer(), nullable=False),
        sa.Column('target_team_id', sa.Integer(), nullable=False),
        sa.Column('target_player_id', sa.Integer(), nullable=False),
        sa.Column('target_player_name', sa.String(length=100), nullable=False),
        sa.Column('target_player_position', sa.String(length=10), nullable=False),
        sa.Column('target_player_team', sa.String(length=10), nullable=True),
        sa.Column('suggested_offer', sa.JSON(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('trade_value', sa.Integer(), nullable=False),
        sa.Column('likelihood', sa.String(length=10), nullable=False),
        sa.Column('user_team_impact', sa.JSON(), nullable=True),
        sa.Column('target_team_impact', sa.JSON(), nullable=True),
        sa.Column('position_analysis', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_expired', sa.Boolean(), nullable=True, default=False),
        sa.Column('user_viewed', sa.Boolean(), nullable=True, default=False),
        sa.Column('user_interest_level', sa.String(length=10), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_team_id'], ['espn_teams.id'], ),
        sa.ForeignKeyConstraint(['target_team_id'], ['espn_teams.id'], ),
    )
    op.create_index(op.f('ix_trade_recommendations_id'), 'trade_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_trade_recommendations_user_team_id'), 'trade_recommendations', ['user_team_id'], unique=False)
    op.create_index(op.f('ix_trade_recommendations_target_team_id'), 'trade_recommendations', ['target_team_id'], unique=False)
    op.create_index(op.f('ix_trade_recommendations_expires_at'), 'trade_recommendations', ['expires_at'], unique=False)
    op.create_index(op.f('ix_trade_recommendations_is_expired'), 'trade_recommendations', ['is_expired'], unique=False)

    # Create team_sync_logs table
    op.create_table('team_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('espn_league_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('teams_processed', sa.Integer(), nullable=True, default=0),
        sa.Column('teams_updated', sa.Integer(), nullable=True, default=0),
        sa.Column('teams_failed', sa.Integer(), nullable=True, default=0),
        sa.Column('total_duration_seconds', sa.Float(), nullable=True),
        sa.Column('sync_summary', sa.JSON(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['espn_league_id'], ['espn_leagues.id'], ),
    )
    op.create_index(op.f('ix_team_sync_logs_id'), 'team_sync_logs', ['id'], unique=False)
    op.create_index(op.f('ix_team_sync_logs_espn_league_id'), 'team_sync_logs', ['espn_league_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_team_sync_logs_espn_league_id'), table_name='team_sync_logs')
    op.drop_index(op.f('ix_team_sync_logs_id'), table_name='team_sync_logs')
    op.drop_table('team_sync_logs')
    
    op.drop_index(op.f('ix_trade_recommendations_is_expired'), table_name='trade_recommendations')
    op.drop_index(op.f('ix_trade_recommendations_expires_at'), table_name='trade_recommendations')
    op.drop_index(op.f('ix_trade_recommendations_target_team_id'), table_name='trade_recommendations')
    op.drop_index(op.f('ix_trade_recommendations_user_team_id'), table_name='trade_recommendations')
    op.drop_index(op.f('ix_trade_recommendations_id'), table_name='trade_recommendations')
    op.drop_table('trade_recommendations')
    
    op.drop_index(op.f('ix_espn_teams_espn_team_id'), table_name='espn_teams')
    op.drop_index(op.f('ix_espn_teams_espn_league_id'), table_name='espn_teams')
    op.drop_index(op.f('ix_espn_teams_id'), table_name='espn_teams')
    op.drop_table('espn_teams')