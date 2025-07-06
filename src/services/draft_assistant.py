"""
Draft Assistant Service for ESPN League Integration

Provides intelligent draft recommendations based on league scoring,
positional needs, and advanced analytics.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
from dataclasses import dataclass

from ..models.espn_league import ESPNLeague, DraftSession, DraftRecommendation
from ..services.ai.claude_client import ai_client

logger = logging.getLogger(__name__)


@dataclass
class PlayerProjection:
    """Player projection with scoring-adjusted values"""
    player_id: int
    name: str
    position: str
    team: str
    projected_points: float
    std_dev: float
    adp: float  # Average Draft Position
    vor: float  # Value Over Replacement
    tier: int
    bye_week: int


@dataclass
class PositionalNeed:
    """Analysis of positional needs for roster construction"""
    position: str
    filled_slots: int
    required_slots: int
    need_level: float  # 0.0 to 1.0
    scarcity_factor: float
    next_tier_dropoff: float


@dataclass
class DraftContext:
    """Complete context for draft recommendations"""
    league: ESPNLeague
    session: DraftSession
    available_players: List[PlayerProjection]
    positional_needs: List[PositionalNeed]
    user_roster: List[Dict[str, Any]]
    historical_patterns: Optional[Dict[str, Any]] = None


class DraftAssistantService:
    """Core service for generating intelligent draft recommendations"""
    
    def __init__(self):
        self.scoring_multipliers = {}
        self.position_rankings = {}
        
    async def generate_recommendations(
        self, 
        session: DraftSession,
        league: ESPNLeague,
        available_players: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive draft recommendations"""
        
        try:
            # Build draft context
            context = await self._build_draft_context(session, league, available_players)
            
            # Calculate player values with league scoring
            scored_players = self._calculate_scoring_adjusted_values(
                context.available_players, 
                league.scoring_settings
            )
            
            # Analyze positional needs
            positional_needs = self._analyze_positional_needs(
                context.user_roster,
                league.roster_positions,
                session.current_round
            )
            
            # Calculate value over replacement
            vor_rankings = self._calculate_value_over_replacement(
                scored_players,
                positional_needs
            )
            
            # Apply draft strategy
            strategic_recommendations = self._apply_draft_strategy(
                vor_rankings,
                positional_needs,
                session,
                league
            )
            
            # Generate AI reasoning
            ai_analysis = await self._generate_ai_reasoning(
                strategic_recommendations,
                context,
                session
            )
            
            return {
                "recommendations": strategic_recommendations,
                "ai_analysis": ai_analysis,
                "positional_needs": positional_needs,
                "context": {
                    "pick_number": session.current_pick,
                    "round": session.current_round,
                    "next_user_pick": session.get_next_pick_number(),
                    "picks_until_turn": session.get_picks_until_user_turn()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating draft recommendations: {e}")
            return self._generate_fallback_recommendations(session, league)
    
    async def _build_draft_context(
        self,
        session: DraftSession,
        league: ESPNLeague,
        available_players: Optional[List[Dict[str, Any]]]
    ) -> DraftContext:
        """Build comprehensive context for draft analysis"""
        
        # Get available players (mock data for now)
        if not available_players:
            available_players = self._get_mock_available_players()
        
        # Convert to PlayerProjection objects
        player_projections = [
            PlayerProjection(
                player_id=p.get('id', 0),
                name=p.get('name', 'Unknown'),
                position=p.get('position', 'UNKNOWN'),
                team=p.get('team', 'UNK'),
                projected_points=p.get('projected_points', 0.0),
                std_dev=p.get('std_dev', 0.0),
                adp=p.get('adp', 999.0),
                vor=0.0,  # Will be calculated
                tier=p.get('tier', 1),
                bye_week=p.get('bye_week', 1)
            )
            for p in available_players
        ]
        
        # Analyze positional needs
        positional_needs = self._analyze_positional_needs(
            session.user_roster or [],
            league.roster_positions or {},
            session.current_round
        )
        
        return DraftContext(
            league=league,
            session=session,
            available_players=player_projections,
            positional_needs=positional_needs,
            user_roster=session.user_roster or []
        )
    
    def _calculate_scoring_adjusted_values(
        self,
        players: List[PlayerProjection],
        scoring_settings: Dict[str, Any]
    ) -> List[PlayerProjection]:
        """Adjust player values based on league scoring system"""
        
        # Extract scoring multipliers
        multipliers = self._extract_scoring_multipliers(scoring_settings)
        
        # Apply scoring adjustments
        for player in players:
            base_points = player.projected_points
            
            # Position-specific adjustments
            if player.position == 'QB':
                # 6pt passing TD leagues boost QB value
                if multipliers.get('passing_tds', 4) >= 6:
                    player.projected_points *= 1.15
                    
            elif player.position in ['RB', 'WR']:
                # PPR adjustments
                ppr_value = multipliers.get('receptions', 0)
                if ppr_value >= 1.0:  # Full PPR
                    if player.position == 'WR':
                        player.projected_points *= 1.08
                    elif player.position == 'RB':
                        player.projected_points *= 1.05
                elif ppr_value >= 0.5:  # Half PPR
                    if player.position == 'WR':
                        player.projected_points *= 1.04
                    elif player.position == 'RB':
                        player.projected_points *= 1.02
        
        return players
    
    def _analyze_positional_needs(
        self,
        user_roster: List[Dict[str, Any]],
        roster_positions: Dict[str, int],
        current_round: int
    ) -> List[PositionalNeed]:
        """Analyze which positions the user needs to fill"""
        
        # Count current roster positions
        filled_positions = {}
        for pick in user_roster:
            pos = pick.get('position', 'UNKNOWN')
            filled_positions[pos] = filled_positions.get(pos, 0) + 1
        
        # Calculate needs for each position
        needs = []
        total_slots = sum(roster_positions.values()) if roster_positions else 16
        
        for position, required in roster_positions.items():
            filled = filled_positions.get(position, 0)
            remaining_slots = max(0, required - filled)
            
            # Calculate need level (0.0 to 1.0)
            if required > 0:
                need_level = remaining_slots / required
            else:
                need_level = 0.0
            
            # Adjust for draft timing
            rounds_remaining = 16 - current_round
            scarcity_factor = self._calculate_positional_scarcity(
                position, 
                current_round,
                rounds_remaining
            )
            
            needs.append(PositionalNeed(
                position=position,
                filled_slots=filled,
                required_slots=required,
                need_level=need_level,
                scarcity_factor=scarcity_factor,
                next_tier_dropoff=0.0  # TODO: Calculate tier analysis
            ))
        
        return sorted(needs, key=lambda x: x.need_level * x.scarcity_factor, reverse=True)
    
    def _calculate_value_over_replacement(
        self,
        players: List[PlayerProjection],
        positional_needs: List[PositionalNeed]
    ) -> List[PlayerProjection]:
        """Calculate value over replacement for each player"""
        
        # Group players by position
        by_position = {}
        for player in players:
            if player.position not in by_position:
                by_position[player.position] = []
            by_position[player.position].append(player)
        
        # Sort each position by projected points
        for position in by_position:
            by_position[position].sort(key=lambda x: x.projected_points, reverse=True)
        
        # Calculate replacement level for each position
        replacement_levels = {}
        for position, pos_players in by_position.items():
            # Replacement level is typically the player at position 24-30
            replacement_index = min(len(pos_players) - 1, 30)
            if replacement_index >= 0:
                replacement_levels[position] = pos_players[replacement_index].projected_points
            else:
                replacement_levels[position] = 0.0
        
        # Calculate VOR for each player
        for player in players:
            replacement_value = replacement_levels.get(player.position, 0.0)
            player.vor = max(0.0, player.projected_points - replacement_value)
        
        return players
    
    def _apply_draft_strategy(
        self,
        players: List[PlayerProjection],
        positional_needs: List[PositionalNeed],
        session: DraftSession,
        league: ESPNLeague
    ) -> List[Dict[str, Any]]:
        """Apply strategic considerations to player rankings"""
        
        # Create recommendations list
        recommendations = []
        
        # Get top players by VOR
        sorted_players = sorted(players, key=lambda x: x.vor, reverse=True)
        
        # Apply strategic filters
        for player in sorted_players[:20]:  # Top 20 by VOR
            
            # Calculate recommendation score
            base_score = player.vor
            
            # Positional need adjustment
            pos_need = next((n for n in positional_needs if n.position == player.position), None)
            if pos_need:
                need_multiplier = 1.0 + (pos_need.need_level * 0.3)
                scarcity_multiplier = 1.0 + (pos_need.scarcity_factor * 0.2)
                base_score *= need_multiplier * scarcity_multiplier
            
            # Round-specific adjustments
            if session.current_round <= 3:
                # Early rounds: prioritize top talent
                if player.tier <= 2:
                    base_score *= 1.1
            elif session.current_round <= 6:
                # Middle rounds: balance need vs value
                pass
            else:
                # Late rounds: fill needs and look for upside
                if pos_need and pos_need.need_level > 0.5:
                    base_score *= 1.15
            
            # Bye week considerations (later rounds)
            if session.current_round > 8:
                # TODO: Check for bye week clustering
                pass
            
            recommendations.append({
                "player_id": player.player_id,
                "name": player.name,
                "position": player.position,
                "team": player.team,
                "projected_points": player.projected_points,
                "vor": player.vor,
                "recommendation_score": base_score,
                "tier": player.tier,
                "adp": player.adp,
                "reasoning": self._generate_player_reasoning(player, pos_need, session)
            })
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_player_reasoning(
        self,
        player: PlayerProjection,
        pos_need: Optional[PositionalNeed],
        session: DraftSession
    ) -> str:
        """Generate reasoning for why this player is recommended"""
        
        reasons = []
        
        # VOR reasoning
        if player.vor > 20:
            reasons.append("Excellent value over replacement")
        elif player.vor > 10:
            reasons.append("Good value over replacement")
        
        # Positional need
        if pos_need and pos_need.need_level > 0.7:
            reasons.append(f"Fills critical {player.position} need")
        elif pos_need and pos_need.need_level > 0.3:
            reasons.append(f"Addresses {player.position} depth")
        
        # Tier considerations
        if player.tier <= 2:
            reasons.append("Top-tier talent")
        elif player.tier <= 4:
            reasons.append("Solid tier player")
        
        # ADP value
        if player.adp > session.current_pick + 10:
            reasons.append("Great value vs ADP")
        elif player.adp > session.current_pick + 5:
            reasons.append("Good value vs ADP")
        
        return "; ".join(reasons) if reasons else "Recommended player"
    
    async def _generate_ai_reasoning(
        self,
        recommendations: List[Dict[str, Any]],
        context: DraftContext,
        session: DraftSession
    ) -> Dict[str, Any]:
        """Generate AI-powered strategic analysis"""
        
        try:
            # Prepare context for AI
            ai_context = {
                "league_info": {
                    "scoring_type": context.league.get_league_type_description(),
                    "team_count": context.league.team_count,
                    "roster_positions": context.league.roster_positions
                },
                "draft_state": {
                    "current_pick": session.current_pick,
                    "round": session.current_round,
                    "user_position": session.user_pick_position,
                    "next_pick": session.get_next_pick_number(),
                    "picks_until_turn": session.get_picks_until_user_turn()
                },
                "roster_analysis": {
                    "current_picks": session.user_roster,
                    "positional_needs": [
                        {
                            "position": need.position,
                            "filled": need.filled_slots,
                            "required": need.required_slots,
                            "need_level": need.need_level
                        }
                        for need in context.positional_needs
                    ]
                },
                "top_recommendations": recommendations[:5]
            }
            
            # Generate AI analysis
            prompt = f"""
            Analyze this draft situation for pick {session.current_pick} in round {session.current_round}.
            
            Provide strategic guidance covering:
            1. Overall draft strategy for this pick
            2. Top 3 player recommendations with reasoning
            3. Positional priorities going forward
            4. Any red flags or considerations
            5. Strategy for next few picks
            
            Keep analysis concise but insightful.
            """
            
            ai_response = await ai_client.chat_completion(
                message=prompt,
                context=ai_context,
                analysis_type="draft_strategy"
            )
            
            return {
                "overall_strategy": ai_response.get("response", "Strategic analysis"),
                "confidence": ai_response.get("confidence", 0.85),
                "key_insights": self._extract_key_insights(recommendations, context),
                "next_pick_strategy": self._generate_next_pick_strategy(session, context)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI reasoning: {e}")
            return {
                "overall_strategy": "Focus on best available player with positional need consideration",
                "confidence": 0.7,
                "key_insights": ["Standard draft strategy recommended"],
                "next_pick_strategy": "Continue building roster depth"
            }
    
    def _extract_key_insights(
        self,
        recommendations: List[Dict[str, Any]],
        context: DraftContext
    ) -> List[str]:
        """Extract key insights from the draft analysis"""
        
        insights = []
        
        # Analyze top recommendation
        if recommendations:
            top_rec = recommendations[0]
            if top_rec["vor"] > 15:
                insights.append(f"Excellent value available at {top_rec['position']}")
        
        # Positional scarcity insights
        urgent_needs = [n for n in context.positional_needs if n.need_level > 0.7]
        if urgent_needs:
            positions = [n.position for n in urgent_needs[:2]]
            insights.append(f"Urgent needs at {', '.join(positions)}")
        
        # Round-specific insights
        if context.session.current_round <= 3:
            insights.append("Early round: prioritize elite talent")
        elif context.session.current_round >= 10:
            insights.append("Late round: fill roster holes and target upside")
        
        return insights
    
    def _generate_next_pick_strategy(
        self,
        session: DraftSession,
        context: DraftContext
    ) -> str:
        """Generate strategy for upcoming picks"""
        
        next_pick = session.get_next_pick_number()
        picks_away = session.get_picks_until_user_turn()
        
        if picks_away <= 3:
            return "Your next pick is soon - consider backup options"
        elif picks_away <= 10:
            return "Monitor position runs and adjust strategy accordingly"
        else:
            return "Long wait until next pick - target players likely to be available"
    
    def _extract_scoring_multipliers(self, scoring_settings: Dict[str, Any]) -> Dict[str, float]:
        """Extract scoring multipliers from ESPN settings"""
        
        if not scoring_settings:
            return {
                'passing_yards': 0.04,
                'passing_tds': 4.0,
                'rushing_yards': 0.1,
                'rushing_tds': 6.0,
                'receiving_yards': 0.1,
                'receiving_tds': 6.0,
                'receptions': 0.0
            }
        
        # ESPN scoring ID mappings
        return {
            'passing_yards': scoring_settings.get('16', {}).get('points', 0.04),
            'passing_tds': scoring_settings.get('4', {}).get('points', 4.0),
            'passing_ints': scoring_settings.get('20', {}).get('points', -2.0),
            'rushing_yards': scoring_settings.get('17', {}).get('points', 0.1),
            'rushing_tds': scoring_settings.get('5', {}).get('points', 6.0),
            'receiving_yards': scoring_settings.get('18', {}).get('points', 0.1),
            'receiving_tds': scoring_settings.get('6', {}).get('points', 6.0),
            'receptions': scoring_settings.get('53', {}).get('points', 0.0),
        }
    
    def _calculate_positional_scarcity(
        self,
        position: str,
        current_round: int,
        rounds_remaining: int
    ) -> float:
        """Calculate positional scarcity factor"""
        
        # Position-specific scarcity curves
        scarcity_curves = {
            'QB': 0.2,   # Less scarce, can wait
            'RB': 0.8,   # Most scarce position
            'WR': 0.6,   # Moderately scarce
            'TE': 0.4,   # Can find value later
            'K': 0.1,    # Draft very late
            'DEF': 0.1   # Draft very late
        }
        
        base_scarcity = scarcity_curves.get(position, 0.5)
        
        # Increase scarcity as draft progresses
        round_multiplier = 1.0 + (current_round / 16.0) * 0.5
        
        return min(1.0, base_scarcity * round_multiplier)
    
    def _get_mock_available_players(self) -> List[Dict[str, Any]]:
        """Generate mock available players for testing"""
        
        mock_players = [
            {
                "id": 1001, "name": "Elite RB1", "position": "RB", "team": "NFL",
                "projected_points": 280.5, "std_dev": 45.2, "adp": 3.2, "tier": 1, "bye_week": 7
            },
            {
                "id": 1002, "name": "Top WR1", "position": "WR", "team": "NFL", 
                "projected_points": 265.8, "std_dev": 38.1, "adp": 4.1, "tier": 1, "bye_week": 9
            },
            {
                "id": 1003, "name": "Elite QB1", "position": "QB", "team": "NFL",
                "projected_points": 285.2, "std_dev": 32.5, "adp": 6.8, "tier": 1, "bye_week": 12
            },
            {
                "id": 1004, "name": "Solid RB2", "position": "RB", "team": "NFL",
                "projected_points": 215.3, "std_dev": 52.8, "adp": 18.5, "tier": 3, "bye_week": 6
            },
            {
                "id": 1005, "name": "Reliable WR2", "position": "WR", "team": "NFL",
                "projected_points": 195.7, "std_dev": 41.2, "adp": 22.1, "tier": 3, "bye_week": 11
            }
        ]
        
        return mock_players
    
    def _generate_fallback_recommendations(
        self,
        session: DraftSession,
        league: ESPNLeague
    ) -> Dict[str, Any]:
        """Generate basic recommendations when main algorithm fails"""
        
        return {
            "recommendations": [
                {
                    "player_id": 9999,
                    "name": "Best Available Player",
                    "position": "FLEX",
                    "team": "NFL",
                    "projected_points": 150.0,
                    "vor": 10.0,
                    "recommendation_score": 85.0,
                    "tier": 2,
                    "adp": session.current_pick,
                    "reasoning": "Fallback recommendation - draft best available"
                }
            ],
            "ai_analysis": {
                "overall_strategy": "Focus on best available player",
                "confidence": 0.5,
                "key_insights": ["System temporarily using simplified recommendations"],
                "next_pick_strategy": "Continue with best available approach"
            },
            "context": {
                "pick_number": session.current_pick,
                "round": session.current_round
            }
        }


# Global service instance
draft_assistant = DraftAssistantService()