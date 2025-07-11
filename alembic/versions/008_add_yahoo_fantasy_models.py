"""Add Yahoo Fantasy models

Revision ID: 008_add_yahoo_fantasy_models
Revises: 007_add_espn_player_fields
Create Date: 2025-01-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_yahoo_fantasy_models'
down_revision = '007_add_espn_player_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add yahoo_oauth_token to users table
    op.add_column('users', sa.Column('yahoo_oauth_token', sa.Text(), nullable=True))
    
    # Create yahoo_leagues table
    op.create_table('yahoo_leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('league_key', sa.String(), nullable=False),
        sa.Column('league_id', sa.String(), nullable=False),
        sa.Column('game_key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('num_teams', sa.Integer(), nullable=False),
        sa.Column('scoring_type', sa.String(), nullable=True),
        sa.Column('league_type', sa.String(), nullable=True),
        sa.Column('draft_status', sa.String(), nullable=True),
        sa.Column('current_week', sa.Integer(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('scoring_settings', sa.JSON(), nullable=True),
        sa.Column('roster_positions', sa.JSON(), nullable=True),
        sa.Column('user_team_key', sa.String(), nullable=True),
        sa.Column('user_team_name', sa.String(), nullable=True),
        sa.Column('user_team_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_yahoo_leagues_league_key'), 'yahoo_leagues', ['league_key'], unique=True)
    
    # Create yahoo_teams table
    op.create_table('yahoo_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('team_key', sa.String(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('manager_name', sa.String(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('points_for', sa.Float(), nullable=True),
        sa.Column('points_against', sa.Float(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('losses', sa.Integer(), nullable=True),
        sa.Column('ties', sa.Integer(), nullable=True),
        sa.Column('waiver_priority', sa.Integer(), nullable=True),
        sa.Column('faab_balance', sa.Float(), nullable=True),
        sa.Column('number_of_moves', sa.Integer(), nullable=True),
        sa.Column('number_of_trades', sa.Integer(), nullable=True),
        sa.Column('is_owned_by_current_login', sa.Boolean(), nullable=True),
        sa.Column('roster', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['league_id'], ['yahoo_leagues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_yahoo_teams_team_key'), 'yahoo_teams', ['team_key'], unique=True)
    
    # Create yahoo_players table
    op.create_table('yahoo_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_key', sa.String(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('name_full', sa.String(), nullable=False),
        sa.Column('name_first', sa.String(), nullable=True),
        sa.Column('name_last', sa.String(), nullable=True),
        sa.Column('editorial_team_abbr', sa.String(), nullable=True),
        sa.Column('uniform_number', sa.Integer(), nullable=True),
        sa.Column('position_type', sa.String(), nullable=True),
        sa.Column('primary_position', sa.String(), nullable=True),
        sa.Column('eligible_positions', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('injury_note', sa.String(), nullable=True),
        sa.Column('season_points', sa.Float(), nullable=True),
        sa.Column('projected_season_points', sa.Float(), nullable=True),
        sa.Column('percent_owned', sa.Float(), nullable=True),
        sa.Column('bye_week', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_yahoo_players_name_full'), 'yahoo_players', ['name_full'], unique=False)
    op.create_index(op.f('ix_yahoo_players_player_key'), 'yahoo_players', ['player_key'], unique=True)


def downgrade():
    # Drop indexes and tables
    op.drop_index(op.f('ix_yahoo_players_player_key'), table_name='yahoo_players')
    op.drop_index(op.f('ix_yahoo_players_name_full'), table_name='yahoo_players')
    op.drop_table('yahoo_players')
    
    op.drop_index(op.f('ix_yahoo_teams_team_key'), table_name='yahoo_teams')
    op.drop_table('yahoo_teams')
    
    op.drop_index(op.f('ix_yahoo_leagues_league_key'), table_name='yahoo_leagues')
    op.drop_table('yahoo_leagues')
    
    # Remove column from users table
    op.drop_column('users', 'yahoo_oauth_token')