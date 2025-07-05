#!/usr/bin/env python3
"""
CLI tool for managing mock NFL data
"""

import click
import sys
import os
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('PYTHONPATH', str(project_root))

from src.models.database import SessionLocal, create_tables, engine
from src.utils.mock_data import seed_mock_data
from src.models.player import Player, PlayerStats, Team
from src.models.fantasy import League, FantasyTeam, Roster
from src.models.user import User
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Fantasy Football Assistant Mock Data CLI"""
    pass


@click.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def seed(confirm):
    """Seed database with mock NFL data"""
    
    if not confirm:
        click.echo("🏈 Fantasy Football Assistant - Mock Data Seeder")
        click.echo("=" * 50)
        click.echo("This will create mock NFL data including:")
        click.echo("- 32 NFL teams")
        click.echo("- ~200 mock players")
        click.echo("- Weekly stats for current season")
        click.echo("- Test league with 10 users")
        click.echo("- Sample roster for testing")
        
        if not click.confirm('\nDo you want to continue?'):
            click.echo("Operation cancelled.")
            return
    
    try:
        # Create database tables
        click.echo("Creating database tables...")
        create_tables()
        click.echo("✓ Database tables created")
        
        # Create database session
        db = SessionLocal()
        
        try:
            click.echo("\nGenerating mock data...")
            with click.progressbar(length=100, label='Generating data') as bar:
                results = seed_mock_data(db)
                bar.update(100)
            
            click.echo("\n✅ Mock data generation completed successfully!")
            click.echo(f"✓ Created {len(results['teams'])} NFL teams")
            click.echo(f"✓ Created {len(results['players'])} players")
            click.echo(f"✓ Generated {len(results['stats'])} player stat records")
            click.echo(f"✓ Created test league with {len(results['test_users'])} users")
            
            click.echo("\n🎯 Test Login Credentials:")
            click.echo("Email: test@example.com")
            click.echo("Username: testuser")
            click.echo("Password: test_password_hash")
            
            click.echo("\n🚀 Ready to test Phase 2 features!")
            
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clear(confirm):
    """Clear all mock data from database"""
    
    if not confirm:
        if not click.confirm('⚠️  This will delete ALL data from the database. Are you sure?'):
            click.echo("Operation cancelled.")
            return
    
    try:
        db = SessionLocal()
        
        try:
            click.echo("Clearing database...")
            
            # Clear in order to respect foreign key constraints
            db.query(Roster).delete()
            db.query(PlayerStats).delete()
            db.query(Player).delete()
            db.query(FantasyTeam).delete()
            db.query(League).delete()
            db.query(User).delete()
            db.query(Team).delete()
            
            db.commit()
            click.echo("✅ Database cleared successfully!")
            
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
def status():
    """Show current database status"""
    
    try:
        db = SessionLocal()
        
        try:
            # Get counts
            team_count = db.query(Team).count()
            player_count = db.query(Player).count()
            stats_count = db.query(PlayerStats).count()
            user_count = db.query(User).count()
            league_count = db.query(League).count()
            fantasy_team_count = db.query(FantasyTeam).count()
            roster_count = db.query(Roster).count()
            
            click.echo("📊 Database Status")
            click.echo("=" * 30)
            click.echo(f"Teams: {team_count}")
            click.echo(f"Players: {player_count}")
            click.echo(f"Player Stats: {stats_count}")
            click.echo(f"Users: {user_count}")
            click.echo(f"Leagues: {league_count}")
            click.echo(f"Fantasy Teams: {fantasy_team_count}")
            click.echo(f"Roster Entries: {roster_count}")
            
            if team_count > 0:
                click.echo("\n🏈 Sample Teams:")
                teams = db.query(Team).limit(5).all()
                for team in teams:
                    click.echo(f"  - {team.name} ({team.abbreviation})")
            
            if player_count > 0:
                click.echo("\n⭐ Sample Players:")
                players = db.query(Player).limit(5).all()
                for player in players:
                    team_name = player.team.abbreviation if player.team else "FA"
                    click.echo(f"  - {player.name} ({player.position}) - {team_name}")
            
            if user_count > 0:
                click.echo("\n👥 Test Users:")
                users = db.query(User).limit(3).all()
                for user in users:
                    click.echo(f"  - {user.email} ({user.username})")
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--position', help='Filter by position (QB, RB, WR, TE, K, DEF)')
@click.option('--limit', default=10, help='Number of players to show')
def players(position: Optional[str], limit: int):
    """List players in database"""
    
    try:
        db = SessionLocal()
        
        try:
            query = db.query(Player)
            
            if position:
                query = query.filter(Player.position == position.upper())
            
            players = query.limit(limit).all()
            
            if not players:
                click.echo(f"No players found" + (f" for position {position}" if position else ""))
                return
            
            click.echo(f"🏈 {'Top ' + str(limit) + ' ' if limit < 50 else ''}Players" + 
                      (f" - {position.upper()}" if position else ""))
            click.echo("=" * 60)
            
            for i, player in enumerate(players, 1):
                team = db.query(Team).filter(Team.id == player.team_id).first()
                team_name = team.abbreviation if team else "FA"
                
                click.echo(f"{i:2d}. {player.name:<20} {player.position:<3} {team_name:<3} "
                          f"Age: {player.age or 'N/A'}")
            
        except Exception as e:
            logger.error(f"Error listing players: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--week', type=int, help='Specific week to show stats for')
def stats(week: Optional[int]):
    """Show player statistics"""
    
    try:
        db = SessionLocal()
        
        try:
            query = db.query(PlayerStats)
            
            if week:
                query = query.filter(PlayerStats.week == week)
            
            stats = query.limit(10).all()
            
            if not stats:
                click.echo(f"No stats found" + (f" for week {week}" if week else ""))
                return
            
            click.echo(f"📊 Player Stats" + (f" - Week {week}" if week else ""))
            click.echo("=" * 80)
            
            for stat in stats:
                player = db.query(Player).filter(Player.id == stat.player_id).first()
                if player:
                    click.echo(f"{player.name:<20} {player.position:<3} Week {stat.week:<2} "
                              f"{stat.fantasy_points_ppr:6.1f} pts")
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
def test_connection():
    """Test database connection"""
    
    try:
        db = SessionLocal()
        
        try:
            # Test connection
            result = db.execute(text("SELECT 1")).fetchone()
            if result:
                click.echo("✅ Database connection successful!")
            else:
                click.echo("❌ Database connection failed!")
                
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            click.echo(f"❌ Database connection failed: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# Add commands to CLI group
cli.add_command(seed)
cli.add_command(clear)
cli.add_command(status)
cli.add_command(players)
cli.add_command(stats)
cli.add_command(test_connection)


if __name__ == "__main__":
    cli()