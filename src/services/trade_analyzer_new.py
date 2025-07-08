"""
Dynamic Trade Analysis Engine
Analyzes team rosters and generates intelligent trade recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.espn_team import ESPNTeam, TradeRecommendation
from ..models.espn_league import ESPNLeague

logger = logging.getLogger(__name__)


class TradeAnalysisEngine:
    """Engine for analyzing rosters and generating trade recommendations"""
    
    def __init__(self):
        # Player value tiers for trade analysis
        self.position_values = {
            'QB': {'tier1': 90, 'tier2': 75, 'tier3': 60, 'tier4': 45},
            'RB': {'tier1': 95, 'tier2': 80, 'tier3': 65, 'tier4': 50},
            'WR': {'tier1': 92, 'tier2': 78, 'tier3': 63, 'tier4': 48},
            'TE': {'tier1': 85, 'tier2': 70, 'tier3': 55, 'tier4': 40},
            'K': {'tier1': 50, 'tier2': 45, 'tier3': 40, 'tier4': 35},
            'D/ST': {'tier1': 55, 'tier2': 50, 'tier3': 45, 'tier4': 40}
        }
    
    async def generate_trade_recommendations(self, db: Session, user_team: ESPNTeam, 
                                           max_recommendations: int = 5) -> List[TradeRecommendation]:
        """
        Generate trade recommendations for a user's team
        
        Args:
            db: Database session
            user_team: User's ESPN team
            max_recommendations: Maximum number of recommendations to generate
            
        Returns:
            List of TradeRecommendation objects
        """
        logger.info(f"Generating trade recommendations for {user_team.team_name}")
        
        # Get all other teams in the league
        other_teams = db.query(ESPNTeam).filter(
            and_(
                ESPNTeam.espn_league_id == user_team.espn_league_id,
                ESPNTeam.id != user_team.id,
                ESPNTeam.is_active == True
            )
        ).all()
        
        if not other_teams:
            logger.warning(f"No other teams found for league {user_team.espn_league_id}")
            return []
        
        # Analyze user team needs and assets
        user_analysis = self._analyze_team_for_trades(user_team)
        
        # Find trade opportunities with each team
        all_opportunities = []
        for target_team in other_teams:
            target_analysis = self._analyze_team_for_trades(target_team)
            opportunities = self._find_trade_opportunities(user_team, target_team, user_analysis, target_analysis)
            all_opportunities.extend(opportunities)
        
        # Score and rank opportunities
        scored_opportunities = self._score_trade_opportunities(all_opportunities)
        
        # Convert top opportunities to TradeRecommendation objects
        recommendations = []
        for opportunity in scored_opportunities[:max_recommendations]:
            recommendation = self._create_trade_recommendation(db, user_team, opportunity)
            if recommendation:
                recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_team_for_trades(self, team: ESPNTeam) -> Dict[str, Any]:
        """Analyze a team's roster for trading purposes"""
        if not team.roster_data:
            return {
                'needs': [],
                'surplus': [],
                'tradeable_players': [],
                'untouchable_players': [],
                'position_strength': {}
            }
        
        roster = team.roster_data
        analysis = {
            'needs': team.team_needs or [],
            'surplus': [],
            'tradeable_players': team.tradeable_assets or [],
            'untouchable_players': [],
            'position_strength': team.position_strengths or {}
        }
        
        # Identify surplus positions
        for pos, strength in analysis['position_strength'].items():
            if strength == 'surplus':
                analysis['surplus'].append(pos)
        
        # Identify untouchable players (top starters)
        starters = [p for p in roster if p.get('status') == 'starter']
        for player in starters:
            pos = player.get('position')
            # Top performers at non-surplus positions are untouchable
            if pos not in analysis['surplus']:
                analysis['untouchable_players'].append({
                    'player_id': player.get('id'),
                    'name': player.get('name'),
                    'position': pos,
                    'reason': 'Key starter'
                })
        
        return analysis
    
    def _find_trade_opportunities(self, user_team: ESPNTeam, target_team: ESPNTeam,
                                user_analysis: Dict[str, Any], target_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find specific trade opportunities between two teams"""
        opportunities = []
        
        # Look for complementary needs
        user_needs = set(user_analysis['needs'])
        target_needs = set(target_analysis['needs'])
        user_surplus = set(user_analysis['surplus'])
        target_surplus = set(target_analysis['surplus'])
        
        # Find positions where user needs what target has surplus of
        mutual_opportunities = user_needs.intersection(target_surplus)
        reverse_opportunities = target_needs.intersection(user_surplus)
        
        # Generate trade packages for mutual opportunities
        for position in mutual_opportunities:
            opportunity = self._create_trade_opportunity(
                user_team, target_team, user_analysis, target_analysis, 
                user_gets_position=position, target_gets_position=None
            )
            if opportunity:
                opportunities.append(opportunity)
        
        # Generate trade packages for reverse opportunities (user gives what target needs)
        for position in reverse_opportunities:
            opportunity = self._create_trade_opportunity(
                user_team, target_team, user_analysis, target_analysis,
                user_gets_position=None, target_gets_position=position
            )
            if opportunity:
                opportunities.append(opportunity)
        
        # Look for even swaps (both teams have needs the other can fill)
        for user_need in user_needs:
            for target_need in target_needs:
                if user_need != target_need and user_need in target_surplus and target_need in user_surplus:
                    opportunity = self._create_trade_opportunity(
                        user_team, target_team, user_analysis, target_analysis,
                        user_gets_position=user_need, target_gets_position=target_need
                    )
                    if opportunity:
                        opportunities.append(opportunity)
        
        return opportunities
    
    def _create_trade_opportunity(self, user_team: ESPNTeam, target_team: ESPNTeam,
                                user_analysis: Dict[str, Any], target_analysis: Dict[str, Any],
                                user_gets_position: Optional[str], target_gets_position: Optional[str]) -> Optional[Dict[str, Any]]:
        """Create a specific trade opportunity"""
        
        # Find target player (what user wants)
        target_player = None
        if user_gets_position:
            target_players = [p for p in target_team.roster_data or [] 
                            if p.get('position') == user_gets_position and p.get('status') != 'starter']
            if target_players:
                # Take the best available bench player at that position
                target_player = target_players[0]  # Could be sorted by value
        
        if not target_player:
            return None
        
        # Find suitable offer (what user gives)
        suggested_offer = []
        if target_gets_position:
            # Find user's tradeable players at target's needed position
            user_tradeable = [p for p in user_analysis['tradeable_players'] 
                            if p.get('position') == target_gets_position]
            if user_tradeable:
                suggested_offer.append(user_tradeable[0])
        
        # If no specific position match, try to balance with tradeable assets
        if not suggested_offer:
            # Offer tradeable assets to balance the trade
            for asset in user_analysis['tradeable_players'][:2]:  # Up to 2 players
                suggested_offer.append(asset)
                target_value = self._estimate_player_value(target_player)
                offer_value = sum(self._estimate_player_value(p) for p in suggested_offer)
                
                # Stop when values are roughly balanced
                if offer_value >= target_value * 0.8:
                    break
        
        if not suggested_offer:
            return None
        
        # Calculate trade value and likelihood
        target_value = self._estimate_player_value(target_player)
        offer_value = sum(self._estimate_player_value(p) for p in suggested_offer)
        
        # Determine likelihood based on value fairness and team needs
        likelihood = self._calculate_trade_likelihood(
            target_value, offer_value, user_analysis, target_analysis,
            user_gets_position, target_gets_position
        )
        
        return {
            'target_team': target_team,
            'target_player': target_player,
            'suggested_offer': suggested_offer,
            'target_value': target_value,
            'offer_value': offer_value,
            'likelihood': likelihood,
            'user_gets_position': user_gets_position,
            'target_gets_position': target_gets_position
        }
    
    def _estimate_player_value(self, player: Dict[str, Any]) -> int:
        """Estimate a player's trade value"""
        position = player.get('position', 'UNKNOWN')
        name = player.get('name', '').lower()
        
        # Base value by position
        if position not in self.position_values:
            return 40
        
        position_vals = self.position_values[position]
        
        # Simple heuristic based on player name (in real implementation, use rankings/stats)
        # For now, use a basic scoring system
        if any(star in name for star in ['jackson', 'allen', 'mahomes', 'mccaffrey', 'jefferson', 'adams']):
            return position_vals['tier1']
        elif any(good in name for good in ['jones', 'brown', 'hill', 'evans', 'wilson']):
            return position_vals['tier2']
        elif any(solid in name for solid in ['smith', 'robinson', 'harris', 'higgins']):
            return position_vals['tier3']
        else:
            return position_vals['tier4']
    
    def _calculate_trade_likelihood(self, target_value: int, offer_value: int,
                                  user_analysis: Dict[str, Any], target_analysis: Dict[str, Any],
                                  user_gets_position: Optional[str], target_gets_position: Optional[str]) -> str:
        """Calculate the likelihood of a trade being accepted"""
        
        # Value fairness (most important factor)
        value_ratio = offer_value / max(target_value, 1)
        
        if value_ratio < 0.7:
            return "low"  # Significantly undervalued offer
        elif value_ratio > 1.3:
            return "low"  # Significantly overvalued offer (might seem suspicious)
        
        # Need satisfaction
        need_bonus = 0
        if target_gets_position and target_gets_position in target_analysis['needs']:
            need_bonus += 0.2
        if user_gets_position and user_gets_position in target_analysis['surplus']:
            need_bonus += 0.1
        
        # Calculate final likelihood
        fairness_score = min(value_ratio, 2 - value_ratio)  # Peaks at 1.0
        total_score = fairness_score + need_bonus
        
        if total_score >= 1.1:
            return "high"
        elif total_score >= 0.9:
            return "medium"
        else:
            return "low"
    
    def _score_trade_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and sort trade opportunities by attractiveness"""
        
        for opp in opportunities:
            score = 0
            
            # Value fairness (0-40 points)
            value_ratio = opp['offer_value'] / max(opp['target_value'], 1)
            fairness = min(value_ratio, 2 - value_ratio)  # Peaks at 1.0
            score += fairness * 40
            
            # Likelihood bonus (0-20 points)
            likelihood_scores = {"high": 20, "medium": 10, "low": 0}
            score += likelihood_scores.get(opp['likelihood'], 0)
            
            # Position need bonus (0-20 points)
            if opp['user_gets_position']:
                score += 20
            
            # Player value bonus (0-20 points)
            target_value = opp['target_value']
            if target_value >= 85:
                score += 20
            elif target_value >= 70:
                score += 15
            elif target_value >= 55:
                score += 10
            
            opp['score'] = round(score)
        
        # Sort by score (highest first)
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)
    
    def _create_trade_recommendation(self, db: Session, user_team: ESPNTeam, 
                                   opportunity: Dict[str, Any]) -> Optional[TradeRecommendation]:
        """Create a TradeRecommendation database object from an opportunity"""
        
        target_team = opportunity['target_team']
        target_player = opportunity['target_player']
        suggested_offer = opportunity['suggested_offer']
        
        # Generate rationale
        rationale = self._generate_trade_rationale(opportunity, user_team.team_name, target_team.team_name)
        
        # Create recommendation with 5-day expiration
        recommendation = TradeRecommendation.create_with_expiration(
            days=5,
            user_team_id=user_team.id,
            target_team_id=target_team.id,
            target_player_id=target_player.get('id'),
            target_player_name=target_player.get('name'),
            target_player_position=target_player.get('position'),
            target_player_team=target_player.get('team'),
            suggested_offer=suggested_offer,
            rationale=rationale,
            trade_value=opportunity['score'],
            likelihood=opportunity['likelihood'],
            user_team_impact={
                "position_improved": opportunity.get('user_gets_position'),
                "value_gained": opportunity['target_value'] - opportunity['offer_value']
            },
            target_team_impact={
                "position_improved": opportunity.get('target_gets_position'),
                "value_gained": opportunity['offer_value'] - opportunity['target_value']
            },
            position_analysis={
                "user_needs": opportunity.get('user_gets_position'),
                "target_needs": opportunity.get('target_gets_position'),
                "value_ratio": opportunity['offer_value'] / max(opportunity['target_value'], 1)
            }
        )
        
        db.add(recommendation)
        db.commit()
        
        return recommendation
    
    def _generate_trade_rationale(self, opportunity: Dict[str, Any], user_team_name: str, target_team_name: str) -> str:
        """Generate a human-readable rationale for the trade"""
        
        target_player = opportunity['target_player']
        suggested_offer = opportunity['suggested_offer']
        user_gets_pos = opportunity.get('user_gets_position')
        target_gets_pos = opportunity.get('target_gets_position')
        
        rationale_parts = []
        
        # Main trade description
        if len(suggested_offer) == 1:
            offered_player = suggested_offer[0]['name']
            rationale_parts.append(f"Trade {offered_player} for {target_player['name']}")
        else:
            offered_names = [p['name'] for p in suggested_offer]
            rationale_parts.append(f"Trade {', '.join(offered_names)} for {target_player['name']}")
        
        # Position need explanation
        if user_gets_pos:
            rationale_parts.append(f"{user_team_name} needs help at {user_gets_pos}")
        
        if target_gets_pos:
            rationale_parts.append(f"{target_team_name} needs depth at {target_gets_pos}")
        
        # Value explanation
        likelihood = opportunity['likelihood']
        if likelihood == "high":
            rationale_parts.append("This trade addresses both teams' needs and offers fair value")
        elif likelihood == "medium":
            rationale_parts.append("Solid trade that could benefit both teams")
        else:
            rationale_parts.append("Worth exploring if you believe in the player's upside")
        
        return ". ".join(rationale_parts) + "."


# Singleton instance
trade_analysis_engine = TradeAnalysisEngine()