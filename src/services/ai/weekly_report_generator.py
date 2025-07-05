"""
Automated Weekly Report Generator for Fantasy Football Assistant

Generates comprehensive weekly reports combining AI insights, ML predictions,
sentiment analysis, and strategic recommendations for fantasy teams.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json

from .claude_client import ai_client
from .ml_pipeline import ml_pipeline
from .sentiment_analyzer import sentiment_analyzer
from .recommendation_engine import recommendation_engine
from .insights_engine import insights_engine

logger = logging.getLogger(__name__)


@dataclass
class WeeklyMatchup:
    """Individual player matchup analysis"""
    player_id: int
    player_name: str
    position: str
    opponent: str
    matchup_rating: str  # "excellent", "good", "average", "poor", "terrible"
    matchup_score: float  # 0-10 scale
    key_factors: List[str]
    start_recommendation: str  # "must_start", "start", "consider", "sit", "avoid"


@dataclass
class WeeklyPlayerAnalysis:
    """Complete weekly analysis for a player"""
    player_id: int
    player_name: str
    position: str
    team: str
    
    # Projections
    projected_points: float
    projection_range: Dict[str, float]  # floor, ceiling
    confidence: float
    
    # Analysis components
    matchup: WeeklyMatchup
    sentiment_analysis: Any  # SentimentAnalysis object
    ml_predictions: Dict[str, Any]
    
    # Recommendations
    start_sit_recommendation: str
    reasoning: List[str]
    risk_factors: List[str]
    upside_factors: List[str]


@dataclass
class WeeklyTeamReport:
    """Comprehensive weekly team report"""
    team_id: int
    user_id: int
    week: int
    generated_at: datetime
    
    # Executive summary
    executive_summary: str
    key_insights: List[str]
    week_outlook: str
    
    # Player analyses
    starting_lineup: List[WeeklyPlayerAnalysis]
    bench_considerations: List[WeeklyPlayerAnalysis]
    
    # Strategic elements
    lineup_score: float  # 0-100
    projected_total: float
    confidence_level: str
    risk_assessment: str
    
    # Actionable items
    recommendations: List[Dict[str, Any]]
    waiver_targets: List[Dict[str, Any]]
    trade_considerations: List[Dict[str, Any]]
    
    # Market intelligence
    opponent_analysis: Dict[str, Any]
    league_trends: Dict[str, Any]
    
    # Performance tracking
    last_week_recap: Optional[Dict[str, Any]] = None
    season_trajectory: Optional[Dict[str, Any]] = None


class WeeklyReportGenerator:
    """Advanced weekly report generator with AI integration"""
    
    def __init__(self):
        """Initialize the weekly report generator"""
        self.ai_client = ai_client
        self.ml_pipeline = ml_pipeline
        self.sentiment_analyzer = sentiment_analyzer
        self.recommendation_engine = recommendation_engine
        self.insights_engine = insights_engine
        
        # Report cache
        self.report_cache: Dict[str, WeeklyTeamReport] = {}
        self.cache_duration = timedelta(hours=4)
    
    async def generate_weekly_report(
        self,
        team_id: int,
        user_id: int,
        week: int,
        team_context: Dict[str, Any],
        league_context: Dict[str, Any],
        include_analysis_details: bool = True
    ) -> WeeklyTeamReport:
        """
        Generate comprehensive weekly report for a fantasy team
        
        Args:
            team_id: Fantasy team ID
            user_id: User ID
            week: NFL week number
            team_context: Current team roster and situation
            league_context: League settings and context
            include_analysis_details: Include detailed player analysis
            
        Returns:
            Complete weekly team report
        """
        try:
            cache_key = f"{team_id}_{week}"
            
            # Check cache first
            if cache_key in self.report_cache:
                cached_report = self.report_cache[cache_key]
                if datetime.now() - cached_report.generated_at < self.cache_duration:
                    logger.info(f"Returning cached weekly report for team {team_id}, week {week}")
                    return cached_report
            
            logger.info(f"Generating weekly report for team {team_id}, week {week}")
            
            # 1. Analyze all roster players
            roster = team_context.get("roster", [])
            player_analyses = await self._analyze_all_players(roster, week, league_context)
            
            # 2. Determine optimal lineup
            starting_lineup, bench_considerations = await self._optimize_lineup(
                player_analyses, league_context
            )
            
            # 3. Generate comprehensive recommendations
            recommendations = await recommendation_engine.generate_comprehensive_recommendations(
                user_id=user_id,
                team_context=team_context,
                league_context=league_context,
                current_week=week
            )
            
            # 4. Analyze opponents and league trends
            opponent_analysis = await self._analyze_weekly_opponents(team_context, week)
            league_trends = await self._analyze_league_trends(league_context, week)
            
            # 5. Generate AI insights and summary
            executive_summary = await self._generate_executive_summary(
                starting_lineup, recommendations, week, team_context
            )
            
            key_insights = await self._extract_key_insights(
                player_analyses, recommendations, opponent_analysis
            )
            
            week_outlook = await self._generate_week_outlook(
                starting_lineup, opponent_analysis, league_trends
            )
            
            # 6. Calculate team metrics
            lineup_score = self._calculate_lineup_score(starting_lineup)
            projected_total = sum(p.projected_points for p in starting_lineup)
            confidence_level = self._calculate_confidence_level(starting_lineup)
            risk_assessment = self._assess_team_risk(starting_lineup, recommendations)
            
            # 7. Get performance tracking data
            last_week_recap = await self._generate_last_week_recap(team_id, week - 1)
            season_trajectory = await self._analyze_season_trajectory(team_context, week)
            
            # 8. Extract actionable recommendations
            formatted_recommendations = self._format_recommendations(recommendations.recommendations)
            waiver_targets = self._extract_waiver_targets(recommendations.recommendations)
            trade_considerations = self._extract_trade_considerations(recommendations.recommendations)
            
            # Create the comprehensive report
            report = WeeklyTeamReport(
                team_id=team_id,
                user_id=user_id,
                week=week,
                generated_at=datetime.now(),
                executive_summary=executive_summary,
                key_insights=key_insights,
                week_outlook=week_outlook,
                starting_lineup=starting_lineup,
                bench_considerations=bench_considerations,
                lineup_score=lineup_score,
                projected_total=projected_total,
                confidence_level=confidence_level,
                risk_assessment=risk_assessment,
                recommendations=formatted_recommendations,
                waiver_targets=waiver_targets,
                trade_considerations=trade_considerations,
                opponent_analysis=opponent_analysis,
                league_trends=league_trends,
                last_week_recap=last_week_recap,
                season_trajectory=season_trajectory
            )
            
            # Cache the report
            self.report_cache[cache_key] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating weekly report for team {team_id}: {e}")
            return self._create_fallback_report(team_id, user_id, week, team_context)
    
    async def _analyze_all_players(
        self,
        roster: List[Dict[str, Any]],
        week: int,
        league_context: Dict[str, Any]
    ) -> List[WeeklyPlayerAnalysis]:
        """Analyze all players on the roster"""
        analyses = []
        
        for player in roster:
            try:
                analysis = await self._analyze_single_player(player, week, league_context)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing player {player.get('name', 'unknown')}: {e}")
                # Create fallback analysis
                analyses.append(self._create_fallback_player_analysis(player, week))
        
        return analyses
    
    async def _analyze_single_player(
        self,
        player: Dict[str, Any],
        week: int,
        league_context: Dict[str, Any]
    ) -> WeeklyPlayerAnalysis:
        """Comprehensive analysis of a single player"""
        player_id = player.get("id", 0)
        player_name = player.get("name", "Unknown Player")
        position = player.get("position", "UNKNOWN")
        team = player.get("team", "UNKNOWN")
        
        # 1. Get ML predictions
        ml_predictions = {
            "points": ml_pipeline.predict_player_points(player, {"week": week}),
            "boom_bust": ml_pipeline.predict_boom_bust_probability(player, {"week": week}),
            "injury_risk": ml_pipeline.assess_injury_risk(player, {"week": week})
        }
        
        # 2. Get sentiment analysis
        sentiment = await sentiment_analyzer.analyze_player_sentiment(
            player_id, player_name, time_range_hours=72
        )
        
        # 3. Analyze matchup
        matchup = await self._analyze_player_matchup(player, week)
        
        # 4. Generate projections
        base_projection = player.get("projected_points", 10.0)
        projection_range = {
            "floor": base_projection * 0.7,
            "ceiling": base_projection * 1.4
        }
        
        # 5. Generate start/sit recommendation
        start_sit_rec, reasoning, risk_factors, upside_factors = await self._generate_start_sit_analysis(
            player, ml_predictions, sentiment, matchup, league_context
        )
        
        # 6. Calculate confidence
        confidence = self._calculate_player_confidence(ml_predictions, sentiment, matchup)
        
        return WeeklyPlayerAnalysis(
            player_id=player_id,
            player_name=player_name,
            position=position,
            team=team,
            projected_points=base_projection,
            projection_range=projection_range,
            confidence=confidence,
            matchup=matchup,
            sentiment_analysis=sentiment,
            ml_predictions=ml_predictions,
            start_sit_recommendation=start_sit_rec,
            reasoning=reasoning,
            risk_factors=risk_factors,
            upside_factors=upside_factors
        )
    
    async def _analyze_player_matchup(
        self,
        player: Dict[str, Any],
        week: int
    ) -> WeeklyMatchup:
        """Analyze player's weekly matchup"""
        # Mock matchup analysis - in production, integrate with actual matchup data
        position = player.get("position", "UNKNOWN")
        opponent = "vs CHI"  # Would be dynamic
        
        # Simple matchup scoring logic
        matchup_factors = {
            "defense_rank": 15,  # Would be actual opponent defense rank
            "points_allowed": 12.5,  # Average points allowed to position
            "pace": "medium",
            "weather": "dome"
        }
        
        # Calculate matchup score (0-10)
        base_score = 5.0
        if matchup_factors["defense_rank"] > 20:
            base_score += 2.0
        elif matchup_factors["defense_rank"] < 10:
            base_score -= 1.5
        
        if matchup_factors["points_allowed"] > 15:
            base_score += 1.5
        elif matchup_factors["points_allowed"] < 8:
            base_score -= 2.0
        
        matchup_score = max(0, min(10, base_score))
        
        # Convert to rating
        if matchup_score >= 8:
            rating = "excellent"
            start_rec = "must_start"
        elif matchup_score >= 6:
            rating = "good"
            start_rec = "start"
        elif matchup_score >= 4:
            rating = "average"
            start_rec = "consider"
        elif matchup_score >= 2:
            rating = "poor"
            start_rec = "sit"
        else:
            rating = "terrible"
            start_rec = "avoid"
        
        key_factors = [
            f"Opponent ranks #{matchup_factors['defense_rank']} vs {position}",
            f"Allows {matchup_factors['points_allowed']} PPG to {position}",
            f"{matchup_factors['pace'].title()} pace offense",
            f"Weather: {matchup_factors['weather']}"
        ]
        
        return WeeklyMatchup(
            player_id=player.get("id", 0),
            player_name=player.get("name", "Unknown"),
            position=position,
            opponent=opponent,
            matchup_rating=rating,
            matchup_score=matchup_score,
            key_factors=key_factors,
            start_recommendation=start_rec
        )
    
    async def _generate_start_sit_analysis(
        self,
        player: Dict[str, Any],
        ml_predictions: Dict[str, Any],
        sentiment: Any,
        matchup: WeeklyMatchup,
        league_context: Dict[str, Any]
    ) -> tuple:
        """Generate comprehensive start/sit analysis"""
        # Start with matchup recommendation as base
        start_sit_rec = matchup.start_recommendation
        
        reasoning = []
        risk_factors = []
        upside_factors = []
        
        # Factor in ML predictions
        points_pred = ml_predictions.get("points", {})
        boom_bust = ml_predictions.get("boom_bust", {})
        
        if points_pred.get("prediction", 0) > 15:
            reasoning.append(f"High projection ({points_pred.get('prediction', 0):.1f} points)")
            upside_factors.append("Strong statistical projection")
        elif points_pred.get("prediction", 0) < 8:
            reasoning.append(f"Low projection ({points_pred.get('prediction', 0):.1f} points)")
            risk_factors.append("Below-average projection")
        
        # Factor in sentiment
        if sentiment.fantasy_impact.value in ["major_positive", "minor_positive"]:
            reasoning.append("Positive news sentiment")
            upside_factors.append("Recent positive developments")
        elif sentiment.fantasy_impact.value in ["major_negative", "minor_negative"]:
            reasoning.append("Negative news sentiment")
            risk_factors.append("Concerning recent news")
        
        # Factor in matchup
        reasoning.append(f"{matchup.matchup_rating.title()} matchup ({matchup.opponent})")
        if matchup.matchup_score >= 7:
            upside_factors.append("Favorable opponent matchup")
        elif matchup.matchup_score <= 3:
            risk_factors.append("Difficult opponent matchup")
        
        # Boom/bust considerations
        boom_prob = boom_bust.get("boom_probability", 0.5)
        if boom_prob > 0.7:
            upside_factors.append("High ceiling potential")
        elif boom_prob < 0.3:
            risk_factors.append("Limited upside potential")
        
        # Injury risk
        injury_risk = ml_predictions.get("injury_risk", {})
        if injury_risk.get("risk_level") in ["elevated", "high"]:
            risk_factors.append("Elevated injury risk")
        
        return start_sit_rec, reasoning, risk_factors, upside_factors
    
    def _calculate_player_confidence(
        self,
        ml_predictions: Dict[str, Any],
        sentiment: Any,
        matchup: WeeklyMatchup
    ) -> float:
        """Calculate confidence level for player analysis"""
        base_confidence = 0.5
        
        # ML model confidence
        points_confidence = ml_predictions.get("points", {}).get("confidence", 0.5)
        base_confidence += (points_confidence - 0.5) * 0.3
        
        # Sentiment confidence
        sentiment_confidence = sentiment.confidence
        base_confidence += (sentiment_confidence - 0.5) * 0.2
        
        # Matchup clarity
        if matchup.matchup_score >= 8 or matchup.matchup_score <= 2:
            base_confidence += 0.2  # Clear good or bad matchup
        
        return max(0.0, min(1.0, base_confidence))
    
    async def _optimize_lineup(
        self,
        player_analyses: List[WeeklyPlayerAnalysis],
        league_context: Dict[str, Any]
    ) -> tuple:
        """Optimize lineup based on projections and analysis"""
        # Sort by projected points for now - could be more sophisticated
        sorted_players = sorted(player_analyses, key=lambda x: x.projected_points, reverse=True)
        
        # Mock lineup positions - would be based on league settings
        lineup_requirements = {
            "QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1
        }
        
        starting_lineup = []
        bench_considerations = []
        
        # Simple lineup optimization - take highest projected at each position
        for position, count in lineup_requirements.items():
            if position == "FLEX":
                # FLEX can be RB, WR, or TE
                eligible = [p for p in sorted_players 
                          if p.position in ["RB", "WR", "TE"] and p not in starting_lineup]
            else:
                eligible = [p for p in sorted_players 
                          if p.position == position and p not in starting_lineup]
            
            for _ in range(min(count, len(eligible))):
                if eligible:
                    starting_lineup.append(eligible.pop(0))
        
        # Rest go to bench considerations
        bench_considerations = [p for p in sorted_players if p not in starting_lineup]
        
        return starting_lineup, bench_considerations[:5]  # Top 5 bench players
    
    async def _analyze_weekly_opponents(
        self,
        team_context: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """Analyze weekly opponents for lineup decisions"""
        return {
            "this_week_opponent": {
                "team_name": "League Rival",
                "projected_points": 125.8,
                "strength": "Strong at RB, weak at WR",
                "key_players": ["Star Player 1", "Star Player 2"],
                "weakness_to_exploit": "Vulnerable to high-ceiling WRs"
            },
            "matchup_analysis": "Competitive matchup requiring ceiling plays",
            "game_theory": "Consider high-upside players over safe floor options"
        }
    
    async def _analyze_league_trends(
        self,
        league_context: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """Analyze league-wide trends and insights"""
        return {
            "scoring_trends": {
                "avg_points_this_week": 115.2,
                "trend": "slightly_above_average",
                "top_performers": ["Position trends", "Breakout players"]
            },
            "waiver_activity": {
                "most_added": ["Player A", "Player B", "Player C"],
                "trending_positions": ["RB", "WR"],
                "activity_level": "high"
            },
            "trade_market": {
                "activity": "moderate",
                "hot_commodities": ["Elite RBs", "Consistent WRs"],
                "market_trends": "Premium on playoff-ready players"
            }
        }
    
    async def _generate_executive_summary(
        self,
        starting_lineup: List[WeeklyPlayerAnalysis],
        recommendations: Any,
        week: int,
        team_context: Dict[str, Any]
    ) -> str:
        """Generate AI-powered executive summary"""
        summary_prompt = f"""
        Generate a concise executive summary for this fantasy football team's Week {week} outlook:
        
        Starting Lineup ({len(starting_lineup)} players):
        {[f"{p.player_name} ({p.position}): {p.projected_points:.1f} pts, {p.start_sit_recommendation}" for p in starting_lineup[:5]]}
        
        Team Record: {team_context.get('record', {}).get('wins', 0)}-{team_context.get('record', {}).get('losses', 0)}
        
        Top Recommendations: {len(recommendations.recommendations)} total
        
        Provide a 2-3 sentence summary focusing on:
        1. Overall team outlook for this week
        2. Key strengths/concerns
        3. Main strategic focus
        """
        
        try:
            result = await ai_client.chat_completion(
                message=summary_prompt,
                context={"week": week, "lineup": starting_lineup},
                analysis_type="weekly_summary"
            )
            return result.get("response", f"Week {week} outlook: Team positioned for competitive performance with strategic optimization opportunities.")
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return f"Week {week} outlook: Comprehensive analysis complete with {len(starting_lineup)} optimized starters and strategic recommendations."
    
    async def _extract_key_insights(
        self,
        player_analyses: List[WeeklyPlayerAnalysis],
        recommendations: Any,
        opponent_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract key insights from all analyses"""
        insights = []
        
        # Player insights
        high_confidence_players = [p for p in player_analyses if p.confidence > 0.8]
        if high_confidence_players:
            insights.append(f"High confidence in {len(high_confidence_players)} player(s) this week")
        
        # Matchup insights
        excellent_matchups = [p for p in player_analyses if p.matchup.matchup_rating == "excellent"]
        if excellent_matchups:
            insights.append(f"Excellent matchups: {', '.join(p.player_name for p in excellent_matchups[:3])}")
        
        # Sentiment insights
        positive_sentiment = [p for p in player_analyses 
                            if p.sentiment_analysis.fantasy_impact.value in ["major_positive", "minor_positive"]]
        if positive_sentiment:
            insights.append(f"Positive news sentiment for {len(positive_sentiment)} player(s)")
        
        # Recommendation insights
        high_priority_recs = [r for r in recommendations.recommendations if r.priority >= 8]
        if high_priority_recs:
            insights.append(f"{len(high_priority_recs)} high-priority action items identified")
        
        # Opponent analysis
        if opponent_analysis.get("weakness_to_exploit"):
            insights.append(f"Opponent weakness: {opponent_analysis['weakness_to_exploit']}")
        
        return insights[:5]  # Top 5 insights
    
    async def _generate_week_outlook(
        self,
        starting_lineup: List[WeeklyPlayerAnalysis],
        opponent_analysis: Dict[str, Any],
        league_trends: Dict[str, Any]
    ) -> str:
        """Generate week outlook assessment"""
        total_projection = sum(p.projected_points for p in starting_lineup)
        avg_confidence = sum(p.confidence for p in starting_lineup) / len(starting_lineup) if starting_lineup else 0
        
        outlook_prompt = f"""
        Provide a week outlook for this fantasy team:
        
        Total Projected Points: {total_projection:.1f}
        Average Confidence: {avg_confidence:.2f}
        Starting Lineup: {len(starting_lineup)} players
        
        Opponent: Projects {opponent_analysis.get('this_week_opponent', {}).get('projected_points', 120)} points
        League Average: {league_trends.get('scoring_trends', {}).get('avg_points_this_week', 115)} points
        
        Provide outlook in 2-3 sentences covering competitiveness and key factors.
        """
        
        try:
            result = await ai_client.chat_completion(
                message=outlook_prompt,
                context={"projection": total_projection, "confidence": avg_confidence},
                analysis_type="week_outlook"
            )
            return result.get("response", f"Projected for {total_projection:.1f} points with {avg_confidence:.0%} confidence. Competitive outlook for the week.")
        except Exception as e:
            logger.error(f"Error generating week outlook: {e}")
            return f"Projected for {total_projection:.1f} points. Team outlook appears competitive for the week."
    
    def _calculate_lineup_score(self, starting_lineup: List[WeeklyPlayerAnalysis]) -> float:
        """Calculate overall lineup score (0-100)"""
        if not starting_lineup:
            return 0.0
        
        # Factors: projections, confidence, matchups
        projection_score = min(100, sum(p.projected_points for p in starting_lineup) / 1.5)
        confidence_score = (sum(p.confidence for p in starting_lineup) / len(starting_lineup)) * 100
        matchup_score = (sum(p.matchup.matchup_score for p in starting_lineup) / len(starting_lineup)) * 10
        
        # Weighted average
        overall_score = (projection_score * 0.5 + confidence_score * 0.3 + matchup_score * 0.2)
        return round(min(100, max(0, overall_score)), 1)
    
    def _calculate_confidence_level(self, starting_lineup: List[WeeklyPlayerAnalysis]) -> str:
        """Calculate overall confidence level"""
        if not starting_lineup:
            return "unknown"
        
        avg_confidence = sum(p.confidence for p in starting_lineup) / len(starting_lineup)
        
        if avg_confidence >= 0.8:
            return "very_high"
        elif avg_confidence >= 0.65:
            return "high"
        elif avg_confidence >= 0.5:
            return "medium"
        elif avg_confidence >= 0.35:
            return "low"
        else:
            return "very_low"
    
    def _assess_team_risk(
        self,
        starting_lineup: List[WeeklyPlayerAnalysis],
        recommendations: Any
    ) -> str:
        """Assess overall team risk level"""
        risk_factors = 0
        total_players = len(starting_lineup)
        
        for player in starting_lineup:
            # Count risk factors
            if player.matchup.matchup_score <= 3:
                risk_factors += 1
            if player.sentiment_analysis.fantasy_impact.value in ["major_negative", "minor_negative"]:
                risk_factors += 1
            if len(player.risk_factors) > 2:
                risk_factors += 1
        
        risk_ratio = risk_factors / (total_players * 2) if total_players > 0 else 0
        
        if risk_ratio <= 0.2:
            return "low"
        elif risk_ratio <= 0.4:
            return "moderate"
        elif risk_ratio <= 0.6:
            return "elevated"
        else:
            return "high"
    
    def _format_recommendations(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Format recommendations for the report"""
        formatted = []
        for rec in recommendations[:5]:  # Top 5
            formatted.append({
                "title": rec.title,
                "type": rec.type.value,
                "action": rec.action,
                "priority": rec.priority,
                "confidence": rec.confidence.value,
                "expected_impact": rec.expected_impact,
                "reasoning": rec.reasoning[:2]  # Top 2 reasons
            })
        return formatted
    
    def _extract_waiver_targets(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Extract waiver wire targets from recommendations"""
        waiver_recs = [r for r in recommendations if r.type.value == "waiver_wire"]
        return [{
            "player": rec.title.replace("Waiver Wire Target: ", ""),
            "reasoning": rec.reasoning[0] if rec.reasoning else "Strategic addition",
            "priority": rec.priority
        } for rec in waiver_recs[:3]]
    
    def _extract_trade_considerations(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Extract trade considerations from recommendations"""
        trade_recs = [r for r in recommendations if r.type.value == "trade_opportunity"]
        return [{
            "opportunity": rec.title,
            "action": rec.action,
            "confidence": rec.confidence.value,
            "impact": rec.expected_impact
        } for rec in trade_recs[:2]]
    
    async def _generate_last_week_recap(self, team_id: int, last_week: int) -> Optional[Dict[str, Any]]:
        """Generate recap of last week's performance"""
        if last_week < 1:
            return None
        
        # Mock last week data - would be from database
        return {
            "week": last_week,
            "actual_points": 118.5,
            "projected_points": 115.2,
            "accuracy": "+3.3 vs projection",
            "top_performer": "Josh Allen (28.5 pts)",
            "disappointment": "Player X (4.2 pts)",
            "key_decisions": "Started correct players at 7/9 positions",
            "lessons_learned": ["Trust projections over matchups", "Monitor injury reports closer"]
        }
    
    async def _analyze_season_trajectory(self, team_context: Dict[str, Any], week: int) -> Dict[str, Any]:
        """Analyze season-long trajectory and trends"""
        record = team_context.get("record", {"wins": 6, "losses": 6})
        
        return {
            "current_record": f"{record.get('wins', 0)}-{record.get('losses', 0)}",
            "playoff_probability": 0.65,
            "trajectory": "improving",
            "key_stats": {
                "avg_points_for": 112.5,
                "avg_points_against": 108.2,
                "consistency": "above_average"
            },
            "outlook": "Strong positioning for playoff push",
            "critical_weeks": [week, week + 1, week + 2]
        }
    
    def _create_fallback_player_analysis(self, player: Dict[str, Any], week: int) -> WeeklyPlayerAnalysis:
        """Create fallback analysis when detailed analysis fails"""
        from .sentiment_analyzer import SentimentScore, FantasyImpact, SentimentAnalysis
        
        # Create minimal sentiment analysis
        fallback_sentiment = SentimentAnalysis(
            player_id=player.get("id", 0),
            player_name=player.get("name", "Unknown"),
            overall_sentiment=SentimentScore.NEUTRAL,
            sentiment_score=0.0,
            fantasy_impact=FantasyImpact.NEUTRAL,
            impact_score=0.0,
            news_articles=[],
            key_themes=[],
            recommendation="No recent news available",
            confidence=0.0,
            last_updated=datetime.now()
        )
        
        # Create basic matchup
        matchup = WeeklyMatchup(
            player_id=player.get("id", 0),
            player_name=player.get("name", "Unknown"),
            position=player.get("position", "UNKNOWN"),
            opponent="vs TBD",
            matchup_rating="average",
            matchup_score=5.0,
            key_factors=["Matchup analysis pending"],
            start_recommendation="consider"
        )
        
        return WeeklyPlayerAnalysis(
            player_id=player.get("id", 0),
            player_name=player.get("name", "Unknown Player"),
            position=player.get("position", "UNKNOWN"),
            team=player.get("team", "UNKNOWN"),
            projected_points=player.get("projected_points", 8.0),
            projection_range={"floor": 5.0, "ceiling": 12.0},
            confidence=0.5,
            matchup=matchup,
            sentiment_analysis=fallback_sentiment,
            ml_predictions={"points": {"prediction": 8.0, "confidence": 0.5}},
            start_sit_recommendation="consider",
            reasoning=["Standard projection"],
            risk_factors=["Limited data available"],
            upside_factors=["Baseline upside potential"]
        )
    
    def _create_fallback_report(
        self,
        team_id: int,
        user_id: int,
        week: int,
        team_context: Dict[str, Any]
    ) -> WeeklyTeamReport:
        """Create fallback report when main generation fails"""
        return WeeklyTeamReport(
            team_id=team_id,
            user_id=user_id,
            week=week,
            generated_at=datetime.now(),
            executive_summary=f"Week {week} report generated with limited data. Check individual player projections.",
            key_insights=["Report generation encountered issues", "Basic analysis available", "Review player statuses manually"],
            week_outlook="Standard competitive outlook expected for the week.",
            starting_lineup=[],
            bench_considerations=[],
            lineup_score=50.0,
            projected_total=100.0,
            confidence_level="low",
            risk_assessment="unknown",
            recommendations=[],
            waiver_targets=[],
            trade_considerations=[],
            opponent_analysis={"status": "analysis_pending"},
            league_trends={"status": "data_unavailable"}
        )


# Global weekly report generator instance
weekly_report_generator = WeeklyReportGenerator()