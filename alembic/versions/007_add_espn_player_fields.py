"""Add ESPN player fields

Revision ID: 007
Revises: 006
Create Date: 2024-01-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add ESPN fields to players table
    with op.batch_alter_table('players') as batch_op:
        batch_op.add_column(sa.Column('ownership_percentage', sa.Float(), nullable=True, default=0.0))
        batch_op.add_column(sa.Column('start_percentage', sa.Float(), nullable=True, default=0.0))
        batch_op.add_column(sa.Column('pro_team_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('default_position_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('draft_rank', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('draft_average_pick', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('projected_total_points', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('rest_of_season_projection', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('consistency_rating', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('boom_percentage', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('bust_percentage', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('team_name', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('team_abbreviation', sa.String(10), nullable=True))
    
    # Add ESPN ID to teams table
    with op.batch_alter_table('teams') as batch_op:
        batch_op.add_column(sa.Column('espn_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_teams_espn_id', ['espn_id'], unique=True)


def downgrade():
    # Remove ESPN fields from players table
    with op.batch_alter_table('players') as batch_op:
        batch_op.drop_column('ownership_percentage')
        batch_op.drop_column('start_percentage')
        batch_op.drop_column('pro_team_id')
        batch_op.drop_column('default_position_id')
        batch_op.drop_column('draft_rank')
        batch_op.drop_column('draft_average_pick')
        batch_op.drop_column('projected_total_points')
        batch_op.drop_column('rest_of_season_projection')
        batch_op.drop_column('consistency_rating')
        batch_op.drop_column('boom_percentage')
        batch_op.drop_column('bust_percentage')
        batch_op.drop_column('team_name')
        batch_op.drop_column('team_abbreviation')
    
    # Remove ESPN ID from teams table
    with op.batch_alter_table('teams') as batch_op:
        batch_op.drop_index('ix_teams_espn_id')
        batch_op.drop_column('espn_id')