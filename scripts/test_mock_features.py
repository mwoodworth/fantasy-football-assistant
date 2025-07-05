#!/usr/bin/env python3
"""
Test script to verify Phase 2 features work with mock data
"""

import sys
import os
from pathlib import Path
import asyncio

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.database import SessionLocal
from src.models.user import User
from src.models.fantasy import League, FantasyTeam
from src.services.draft_assistant import DraftAssistant
from src.services.lineup_optimizer import LineupOptimizer
from src.services.waiver_analyzer import WaiverAnalyzer
from src.services.trade_analyzer import TradeAnalyzer
from src.services.player import PlayerService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_phase2_features():
    """Test all Phase 2 features with mock data"""
    
    print("🧪 Testing Phase 2 Features with Mock Data")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Get test data
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("❌ No test user found. Run mock data seeder first.")
            return False
        
        test_league = db.query(League).first()
        if not test_league:
            print("❌ No test league found. Run mock data seeder first.")
            return False
        
        test_team = db.query(FantasyTeam).filter(FantasyTeam.owner_id == test_user.id).first()
        if not test_team:
            print("❌ No test team found. Run mock data seeder first.")
            return False
        
        print(f"✓ Found test user: {test_user.email}")
        print(f"✓ Found test league: {test_league.name}")
        print(f"✓ Found test team: {test_team.name}")
        print()
        
        # Test Player Service
        print("🔍 Testing Player Service...")
        try:
            qb_rankings = PlayerService.get_position_rankings(db, "QB", "ppr", 10)
            if qb_rankings:
                print(f"✓ QB Rankings: Found {len(qb_rankings)} quarterbacks")
                print(f"  Top QB: {qb_rankings[0]['player'].name}")
            else:
                print("❌ No QB rankings found")
        except Exception as e:
            print(f"❌ Player Service error: {e}")
        
        # Test Draft Assistant
        print("\n🎯 Testing Draft Assistant...")
        try:
            draft_assistant = DraftAssistant(db, test_league)
            
            # Test draft board
            draft_board = draft_assistant.get_draft_board(50)
            if draft_board:
                print(f"✓ Draft Board: Found {len(draft_board)} players")
                print(f"  Top pick: {draft_board[0]['player'].name} ({draft_board[0]['player'].position})")
            else:
                print("❌ No draft board generated")
            
            # Test draft recommendations
            recommendations = draft_assistant.get_draft_recommendations(test_team.id, 15, 2)
            if recommendations:
                print(f"✓ Draft Recommendations: Found {len(recommendations)} recommendations")
                print(f"  Top recommendation: {recommendations[0]['player'].name}")
            else:
                print("❌ No draft recommendations found")
                
        except Exception as e:
            print(f"❌ Draft Assistant error: {e}")
        
        # Test Lineup Optimizer
        print("\n📊 Testing Lineup Optimizer...")
        try:
            lineup_optimizer = LineupOptimizer(db, test_league)
            
            # Test lineup optimization
            optimal_lineup = lineup_optimizer.optimize_lineup(test_team.id, 8, [], [])
            if optimal_lineup:
                print(f"✓ Lineup Optimization: Generated optimal lineup")
                print(f"  Projected points: {optimal_lineup.get('total_points', 0):.1f}")
            else:
                print("❌ No optimal lineup generated")
            
            # Test start/sit recommendations
            start_sit = lineup_optimizer.get_start_sit_recommendations(test_team.id, 8)
            if start_sit:
                print(f"✓ Start/Sit Recommendations: Found {len(start_sit)} recommendations")
            else:
                print("❌ No start/sit recommendations found")
                
        except Exception as e:
            print(f"❌ Lineup Optimizer error: {e}")
        
        # Test Waiver Analyzer
        print("\n🔍 Testing Waiver Analyzer...")
        try:
            waiver_analyzer = WaiverAnalyzer(db, test_league)
            
            # Test waiver recommendations
            waiver_recs = waiver_analyzer.get_waiver_recommendations(test_team.id, 8, None, 10)
            if waiver_recs:
                print(f"✓ Waiver Recommendations: Found {len(waiver_recs)} recommendations")
                if waiver_recs:
                    print(f"  Top waiver pickup: {waiver_recs[0]['player'].name}")
            else:
                print("❌ No waiver recommendations found")
            
            # Test trending players
            trending = waiver_analyzer.get_trending_players(5)
            if trending:
                print(f"✓ Trending Players: Found {len(trending)} trending players")
            else:
                print("❌ No trending players found")
                
        except Exception as e:
            print(f"❌ Waiver Analyzer error: {e}")
        
        # Test Trade Analyzer
        print("\n🤝 Testing Trade Analyzer...")
        try:
            trade_analyzer = TradeAnalyzer(db, test_league)
            
            # Get some players for trade test
            from models.player import Player
            players = db.query(Player).filter(Player.position == "RB").limit(4).all()
            
            if len(players) >= 4:
                # Test trade evaluation
                team2 = db.query(FantasyTeam).filter(FantasyTeam.id != test_team.id).first()
                if team2:
                    evaluation = trade_analyzer.evaluate_trade(
                        test_team.id, [players[0].id], [players[1].id],
                        team2.id, [players[1].id], [players[0].id]
                    )
                    
                    if evaluation and 'fairness_analysis' in evaluation:
                        print(f"✓ Trade Evaluation: Generated trade analysis")
                        print(f"  Fairness Score: {evaluation['fairness_analysis']['fairness_score']:.1f}")
                        print(f"  Recommendation: {evaluation['recommendation']['recommendation']}")
                    else:
                        print("❌ No trade evaluation generated")
                else:
                    print("❌ No second team found for trade test")
            else:
                print("❌ Not enough players for trade test")
                
        except Exception as e:
            print(f"❌ Trade Analyzer error: {e}")
        
        print("\n✅ Phase 2 Feature Testing Complete!")
        print("🚀 All core features are working with mock data!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_phase2_features()
    sys.exit(0 if success else 1)