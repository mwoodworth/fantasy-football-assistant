"""
Advanced Analytics Dashboard Service for Fantasy Football Assistant

Provides comprehensive analytics, visualizations, and data insights for fantasy football
teams, players, and league-wide trends with real-time updates and historical analysis.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalyticsTimeframe(Enum):
    """Time periods for analytics data"""
    CURRENT_WEEK = "current_week"
    LAST_4_WEEKS = "last_4_weeks"
    SEASON = "season"
    LAST_SEASON = "last_season"
    CAREER = "career"


class MetricType(Enum):
    """Types of analytics metrics"""
    POINTS = "points"
    CONSISTENCY = "consistency"
    EFFICIENCY = "efficiency"
    OPPORTUNITY = "opportunity"
    TREND = "trend"
    COMPARISON = "comparison"


@dataclass
class PlayerMetrics:
    """Comprehensive player metrics for analytics"""
    player_id: int
    player_name: str
    position: str
    
    # Performance metrics
    avg_points: float
    total_points: float
    games_played: int
    points_per_game: float
    
    # Consistency metrics
    consistency_score: float  # 0-100
    floor: float
    ceiling: float
    boom_rate: float  # % games above 20% avg
    bust_rate: float  # % games below 50% avg
    
    # Efficiency metrics
    points_per_opportunity: float
    target_share: float
    red_zone_share: float
    snap_percentage: float
    
    # Trend metrics
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # -1.0 to 1.0
    recent_performance: float  # Last 4 weeks avg
    
    # Rankings
    position_rank: int
    overall_rank: int
    
    # Time period
    timeframe: AnalyticsTimeframe


@dataclass
class TeamAnalytics:
    """Team-level analytics and performance metrics"""
    team_id: int
    team_name: str
    
    # Overall performance
    total_points: float
    avg_points_per_week: float
    rank_in_league: int
    win_percentage: float
    
    # Positional strength
    position_strengths: Dict[str, float]  # Position -> strength score
    weakest_positions: List[str]
    strongest_positions: List[str]
    
    # Trends
    scoring_trend: str  # "improving", "declining", "stable"
    playoff_probability: float
    championship_probability: float
    
    # Efficiency metrics
    lineup_efficiency: float  # % of optimal lineup points achieved
    bench_strength: float
    roster_balance: float
    
    # Historical performance
    best_week: Dict[str, Any]
    worst_week: Dict[str, Any]
    streak: Dict[str, Any]  # Current win/loss streak


@dataclass
class LeagueAnalytics:
    """League-wide analytics and trends"""
    league_id: str
    
    # Scoring statistics
    avg_team_score: float
    highest_scoring_team: str
    lowest_scoring_team: str
    scoring_distribution: Dict[str, float]
    
    # Player statistics
    top_performers: List[Dict[str, Any]]
    breakout_players: List[Dict[str, Any]]
    declining_players: List[Dict[str, Any]]
    
    # Position trends
    position_scarcity: Dict[str, float]
    position_values: Dict[str, float]
    
    # Market trends
    most_traded_players: List[Dict[str, Any]]
    waiver_wire_trends: List[Dict[str, Any]]
    trade_volume: int
    
    # Competitive metrics
    parity_index: float  # 0-1, higher means more competitive
    playoff_race_teams: List[str]


@dataclass
class CustomMetric:
    """User-defined custom analytics metric"""
    metric_id: str
    name: str
    description: str
    formula: str  # Mathematical formula for calculation
    components: List[str]  # Base stats used
    value: float
    trend: float  # Change over time
    benchmark: float  # League average or target


class AnalyticsDashboard:
    """Advanced analytics dashboard for comprehensive fantasy football insights"""
    
    def __init__(self):
        """Initialize the analytics dashboard"""
        self.analytics_cache: Dict[str, Any] = {}
        self.cache_duration = timedelta(minutes=30)
        self.custom_metrics: Dict[str, CustomMetric] = {}
    
    async def get_player_analytics(
        self,
        player_id: int,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.SEASON,
        comparison_players: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a player
        
        Args:
            player_id: Player to analyze
            timeframe: Time period for analysis
            comparison_players: Optional players to compare against
            
        Returns:
            Complete analytics package for the player
        """
        try:
            cache_key = f"player_{player_id}_{timeframe.value}"
            
            # Check cache
            if cache_key in self.analytics_cache:
                cached_data = self.analytics_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
            
            # Generate player metrics
            metrics = await self._calculate_player_metrics(player_id, timeframe)
            
            # Generate visualizations data
            performance_chart = await self._generate_performance_chart_data(player_id, timeframe)
            consistency_chart = await self._generate_consistency_chart_data(player_id, timeframe)
            opportunity_chart = await self._generate_opportunity_chart_data(player_id, timeframe)
            
            # Generate comparisons if requested
            comparisons = None
            if comparison_players:
                comparisons = await self._generate_player_comparisons(
                    player_id, comparison_players, timeframe
                )
            
            # Generate insights
            insights = await self._generate_player_insights(metrics, timeframe)
            
            # Compile analytics
            analytics = {
                "player_id": player_id,
                "timeframe": timeframe.value,
                "metrics": self._serialize_player_metrics(metrics),
                "charts": {
                    "performance": performance_chart,
                    "consistency": consistency_chart,
                    "opportunity": opportunity_chart
                },
                "comparisons": comparisons,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache results
            self.analytics_cache[cache_key] = {
                'data': analytics,
                'timestamp': datetime.now()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating player analytics for {player_id}: {e}")
            return self._create_error_response("player_analytics", str(e))
    
    async def get_team_analytics(
        self,
        team_id: int,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.SEASON,
        include_projections: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive team analytics
        
        Args:
            team_id: Team to analyze
            timeframe: Time period for analysis
            include_projections: Include future projections
            
        Returns:
            Complete team analytics package
        """
        try:
            cache_key = f"team_{team_id}_{timeframe.value}"
            
            # Check cache
            if cache_key in self.analytics_cache:
                cached_data = self.analytics_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
            
            # Calculate team analytics
            team_metrics = await self._calculate_team_analytics(team_id, timeframe)
            
            # Generate team charts
            scoring_trend_chart = await self._generate_scoring_trend_chart(team_id, timeframe)
            position_strength_chart = await self._generate_position_strength_chart(team_id)
            efficiency_chart = await self._generate_efficiency_chart(team_id, timeframe)
            
            # Generate projections if requested
            projections = None
            if include_projections:
                projections = await self._generate_team_projections(team_id)
            
            # Generate insights
            insights = await self._generate_team_insights(team_metrics)
            
            # Compile analytics
            analytics = {
                "team_id": team_id,
                "timeframe": timeframe.value,
                "metrics": self._serialize_team_analytics(team_metrics),
                "charts": {
                    "scoring_trend": scoring_trend_chart,
                    "position_strength": position_strength_chart,
                    "efficiency": efficiency_chart
                },
                "projections": projections,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache results
            self.analytics_cache[cache_key] = {
                'data': analytics,
                'timestamp': datetime.now()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating team analytics for {team_id}: {e}")
            return self._create_error_response("team_analytics", str(e))
    
    async def get_league_analytics(
        self,
        league_id: str,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.SEASON
    ) -> Dict[str, Any]:
        """
        Get comprehensive league-wide analytics
        
        Args:
            league_id: League to analyze
            timeframe: Time period for analysis
            
        Returns:
            Complete league analytics package
        """
        try:
            cache_key = f"league_{league_id}_{timeframe.value}"
            
            # Check cache
            if cache_key in self.analytics_cache:
                cached_data = self.analytics_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
            
            # Calculate league analytics
            league_metrics = await self._calculate_league_analytics(league_id, timeframe)
            
            # Generate league charts
            scoring_distribution_chart = await self._generate_scoring_distribution_chart(league_id)
            position_value_chart = await self._generate_position_value_chart(league_id)
            parity_chart = await self._generate_parity_chart(league_id, timeframe)
            
            # Generate market analysis
            market_analysis = await self._generate_market_analysis(league_id)
            
            # Generate insights
            insights = await self._generate_league_insights(league_metrics)
            
            # Compile analytics
            analytics = {
                "league_id": league_id,
                "timeframe": timeframe.value,
                "metrics": self._serialize_league_analytics(league_metrics),
                "charts": {
                    "scoring_distribution": scoring_distribution_chart,
                    "position_values": position_value_chart,
                    "parity": parity_chart
                },
                "market_analysis": market_analysis,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache results
            self.analytics_cache[cache_key] = {
                'data': analytics,
                'timestamp': datetime.now()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating league analytics for {league_id}: {e}")
            return self._create_error_response("league_analytics", str(e))
    
    async def create_custom_metric(
        self,
        user_id: int,
        name: str,
        description: str,
        formula: str,
        components: List[str]
    ) -> CustomMetric:
        """
        Create a custom analytics metric
        
        Args:
            user_id: User creating the metric
            name: Metric name
            description: Metric description
            formula: Mathematical formula
            components: Base stats used
            
        Returns:
            Created custom metric
        """
        try:
            metric_id = f"{user_id}_{name.lower().replace(' ', '_')}"
            
            # Validate formula
            if not self._validate_metric_formula(formula, components):
                raise ValueError("Invalid metric formula or components")
            
            # Create metric
            custom_metric = CustomMetric(
                metric_id=metric_id,
                name=name,
                description=description,
                formula=formula,
                components=components,
                value=0.0,
                trend=0.0,
                benchmark=0.0
            )
            
            # Store metric
            self.custom_metrics[metric_id] = custom_metric
            
            logger.info(f"Created custom metric {metric_id} for user {user_id}")
            return custom_metric
            
        except Exception as e:
            logger.error(f"Error creating custom metric: {e}")
            raise
    
    async def get_real_time_updates(
        self,
        entity_type: str,  # "player", "team", "league"
        entity_id: Any,
        update_interval: int = 60  # seconds
    ) -> Dict[str, Any]:
        """
        Get real-time analytics updates
        
        Args:
            entity_type: Type of entity to track
            entity_id: ID of the entity
            update_interval: Update frequency in seconds
            
        Returns:
            Real-time analytics updates
        """
        try:
            # Get current metrics
            current_metrics = await self._get_current_metrics(entity_type, entity_id)
            
            # Get previous metrics for comparison
            previous_metrics = await self._get_previous_metrics(entity_type, entity_id)
            
            # Calculate changes
            changes = self._calculate_metric_changes(current_metrics, previous_metrics)
            
            # Generate alerts if significant changes
            alerts = self._generate_alerts(changes, entity_type, entity_id)
            
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "current_metrics": current_metrics,
                "changes": changes,
                "alerts": alerts,
                "next_update": (datetime.now() + timedelta(seconds=update_interval)).isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time updates: {e}")
            return self._create_error_response("real_time_updates", str(e))
    
    async def export_analytics(
        self,
        analytics_data: Dict[str, Any],
        format: str = "json"  # "json", "csv", "pdf"
    ) -> Dict[str, Any]:
        """
        Export analytics data in various formats
        
        Args:
            analytics_data: Analytics to export
            format: Export format
            
        Returns:
            Export information
        """
        try:
            if format == "json":
                export_data = json.dumps(analytics_data, indent=2)
                filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            elif format == "csv":
                export_data = self._convert_to_csv(analytics_data)
                filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif format == "pdf":
                # Would require PDF generation library
                export_data = "PDF export not yet implemented"
                filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return {
                "success": True,
                "format": format,
                "filename": filename,
                "data": export_data,
                "size": len(export_data),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return self._create_error_response("export_analytics", str(e))
    
    # Private calculation methods
    async def _calculate_player_metrics(
        self,
        player_id: int,
        timeframe: AnalyticsTimeframe
    ) -> PlayerMetrics:
        """Calculate comprehensive player metrics"""
        # Mock implementation - would integrate with database
        mock_data = {
            "avg_points": 15.5,
            "total_points": 186.0,
            "games_played": 12,
            "points_per_game": 15.5,
            "consistency_score": 72.5,
            "floor": 8.2,
            "ceiling": 28.4,
            "boom_rate": 0.25,
            "bust_rate": 0.08
        }
        
        return PlayerMetrics(
            player_id=player_id,
            player_name=f"Player {player_id}",
            position="RB",
            avg_points=mock_data["avg_points"],
            total_points=mock_data["total_points"],
            games_played=mock_data["games_played"],
            points_per_game=mock_data["points_per_game"],
            consistency_score=mock_data["consistency_score"],
            floor=mock_data["floor"],
            ceiling=mock_data["ceiling"],
            boom_rate=mock_data["boom_rate"],
            bust_rate=mock_data["bust_rate"],
            points_per_opportunity=1.2,
            target_share=0.18,
            red_zone_share=0.22,
            snap_percentage=0.85,
            trend_direction="up",
            trend_strength=0.4,
            recent_performance=17.2,
            position_rank=8,
            overall_rank=15,
            timeframe=timeframe
        )
    
    async def _calculate_team_analytics(
        self,
        team_id: int,
        timeframe: AnalyticsTimeframe
    ) -> TeamAnalytics:
        """Calculate comprehensive team analytics"""
        return TeamAnalytics(
            team_id=team_id,
            team_name=f"Team {team_id}",
            total_points=1450.5,
            avg_points_per_week=120.9,
            rank_in_league=3,
            win_percentage=0.667,
            position_strengths={"RB": 0.85, "WR": 0.72, "QB": 0.90, "TE": 0.45},
            weakest_positions=["TE", "K"],
            strongest_positions=["QB", "RB"],
            scoring_trend="improving",
            playoff_probability=0.85,
            championship_probability=0.22,
            lineup_efficiency=0.88,
            bench_strength=65.5,
            roster_balance=0.75,
            best_week={"week": 5, "points": 145.2},
            worst_week={"week": 9, "points": 92.4},
            streak={"type": "win", "count": 3}
        )
    
    async def _calculate_league_analytics(
        self,
        league_id: str,
        timeframe: AnalyticsTimeframe
    ) -> LeagueAnalytics:
        """Calculate comprehensive league analytics"""
        return LeagueAnalytics(
            league_id=league_id,
            avg_team_score=115.5,
            highest_scoring_team="Team Alpha",
            lowest_scoring_team="Team Omega",
            scoring_distribution={"100-110": 0.2, "110-120": 0.35, "120-130": 0.3, "130+": 0.15},
            top_performers=[
                {"player": "Player A", "points": 22.5},
                {"player": "Player B", "points": 20.1}
            ],
            breakout_players=[
                {"player": "Rookie RB", "improvement": "+45%"}
            ],
            declining_players=[
                {"player": "Veteran WR", "decline": "-22%"}
            ],
            position_scarcity={"RB": 0.8, "WR": 0.4, "TE": 0.9},
            position_values={"RB": 1.2, "WR": 1.0, "TE": 0.8},
            most_traded_players=[
                {"player": "Player X", "trades": 3}
            ],
            waiver_wire_trends=[
                {"player": "Sleeper WR", "adds": 45}
            ],
            trade_volume=28,
            parity_index=0.75,
            playoff_race_teams=["Team A", "Team B", "Team C", "Team D"]
        )
    
    async def _generate_performance_chart_data(
        self,
        player_id: int,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate performance chart data"""
        # Mock implementation - would use real data
        weeks = list(range(1, 13))
        points = [12.5, 18.2, 22.1, 8.5, 15.3, 19.8, 14.2, 25.5, 11.2, 16.8, 20.1, 18.9]
        
        return {
            "type": "line",
            "title": "Weekly Performance",
            "x_axis": {"label": "Week", "data": weeks},
            "y_axis": {"label": "Fantasy Points", "data": points},
            "average_line": sum(points) / len(points),
            "trend_line": self._calculate_trend_line(points)
        }
    
    async def _generate_consistency_chart_data(
        self,
        player_id: int,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate consistency chart data"""
        return {
            "type": "box_plot",
            "title": "Point Distribution",
            "median": 16.5,
            "q1": 12.8,
            "q3": 19.7,
            "min": 8.5,
            "max": 25.5,
            "outliers": []
        }
    
    async def _generate_opportunity_chart_data(
        self,
        player_id: int,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate opportunity share chart data"""
        return {
            "type": "stacked_bar",
            "title": "Usage Breakdown",
            "categories": ["Targets", "Carries", "Red Zone", "Goal Line"],
            "data": {
                "week_1": [8, 12, 3, 1],
                "week_2": [10, 14, 4, 2],
                "week_3": [7, 15, 2, 1],
                "week_4": [9, 11, 3, 0]
            }
        }
    
    async def _generate_player_comparisons(
        self,
        player_id: int,
        comparison_players: List[int],
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate player comparison data"""
        return {
            "type": "radar",
            "title": "Player Comparison",
            "categories": ["Points", "Consistency", "Ceiling", "Floor", "Opportunity"],
            "players": {
                f"Player {player_id}": [85, 72, 90, 65, 78],
                f"Player {comparison_players[0]}": [78, 85, 75, 80, 70]
            }
        }
    
    async def _generate_player_insights(
        self,
        metrics: PlayerMetrics,
        timeframe: AnalyticsTimeframe
    ) -> List[str]:
        """Generate AI-powered player insights"""
        insights = []
        
        if metrics.trend_strength > 0.3:
            insights.append(f"Trending up with {metrics.trend_strength*100:.0f}% improvement")
        
        if metrics.consistency_score > 80:
            insights.append(f"Elite consistency rating of {metrics.consistency_score:.0f}")
        
        if metrics.boom_rate > 0.3:
            insights.append(f"High ceiling player with {metrics.boom_rate*100:.0f}% boom rate")
        
        if metrics.red_zone_share > 0.25:
            insights.append(f"Red zone specialist with {metrics.red_zone_share*100:.0f}% share")
        
        return insights
    
    def _calculate_trend_line(self, data: List[float]) -> List[float]:
        """Calculate trend line for data points"""
        x = np.arange(len(data))
        y = np.array(data)
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        return [float(p(i)) for i in x]
    
    def _validate_metric_formula(self, formula: str, components: List[str]) -> bool:
        """Validate custom metric formula"""
        # Basic validation - would be more comprehensive
        for component in components:
            if component not in formula:
                return False
        return True
    
    def _serialize_player_metrics(self, metrics: PlayerMetrics) -> Dict[str, Any]:
        """Serialize player metrics for JSON response"""
        return {
            "player_id": metrics.player_id,
            "player_name": metrics.player_name,
            "position": metrics.position,
            "performance": {
                "avg_points": metrics.avg_points,
                "total_points": metrics.total_points,
                "games_played": metrics.games_played,
                "points_per_game": metrics.points_per_game
            },
            "consistency": {
                "score": metrics.consistency_score,
                "floor": metrics.floor,
                "ceiling": metrics.ceiling,
                "boom_rate": metrics.boom_rate,
                "bust_rate": metrics.bust_rate
            },
            "efficiency": {
                "points_per_opportunity": metrics.points_per_opportunity,
                "target_share": metrics.target_share,
                "red_zone_share": metrics.red_zone_share,
                "snap_percentage": metrics.snap_percentage
            },
            "trends": {
                "direction": metrics.trend_direction,
                "strength": metrics.trend_strength,
                "recent_performance": metrics.recent_performance
            },
            "rankings": {
                "position_rank": metrics.position_rank,
                "overall_rank": metrics.overall_rank
            },
            "timeframe": metrics.timeframe.value
        }
    
    def _serialize_team_analytics(self, analytics: TeamAnalytics) -> Dict[str, Any]:
        """Serialize team analytics for JSON response"""
        return {
            "team_id": analytics.team_id,
            "team_name": analytics.team_name,
            "performance": {
                "total_points": analytics.total_points,
                "avg_points_per_week": analytics.avg_points_per_week,
                "rank_in_league": analytics.rank_in_league,
                "win_percentage": analytics.win_percentage
            },
            "strengths": {
                "position_strengths": analytics.position_strengths,
                "weakest_positions": analytics.weakest_positions,
                "strongest_positions": analytics.strongest_positions
            },
            "outlook": {
                "scoring_trend": analytics.scoring_trend,
                "playoff_probability": analytics.playoff_probability,
                "championship_probability": analytics.championship_probability
            },
            "efficiency": {
                "lineup_efficiency": analytics.lineup_efficiency,
                "bench_strength": analytics.bench_strength,
                "roster_balance": analytics.roster_balance
            },
            "history": {
                "best_week": analytics.best_week,
                "worst_week": analytics.worst_week,
                "streak": analytics.streak
            }
        }
    
    def _serialize_league_analytics(self, analytics: LeagueAnalytics) -> Dict[str, Any]:
        """Serialize league analytics for JSON response"""
        return {
            "league_id": analytics.league_id,
            "scoring": {
                "avg_team_score": analytics.avg_team_score,
                "highest_scoring_team": analytics.highest_scoring_team,
                "lowest_scoring_team": analytics.lowest_scoring_team,
                "distribution": analytics.scoring_distribution
            },
            "players": {
                "top_performers": analytics.top_performers,
                "breakout_players": analytics.breakout_players,
                "declining_players": analytics.declining_players
            },
            "market": {
                "position_scarcity": analytics.position_scarcity,
                "position_values": analytics.position_values,
                "most_traded": analytics.most_traded_players,
                "waiver_trends": analytics.waiver_wire_trends,
                "trade_volume": analytics.trade_volume
            },
            "competition": {
                "parity_index": analytics.parity_index,
                "playoff_race": analytics.playoff_race_teams
            }
        }
    
    def _create_error_response(self, analytics_type: str, error: str) -> Dict[str, Any]:
        """Create error response for failed analytics"""
        return {
            "error": True,
            "analytics_type": analytics_type,
            "message": f"Failed to generate {analytics_type}",
            "details": error,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_current_metrics(self, entity_type: str, entity_id: Any) -> Dict[str, Any]:
        """Get current metrics for real-time updates"""
        # Mock implementation
        return {
            "points": 125.5,
            "rank": 3,
            "trend": "up",
            "last_update": datetime.now().isoformat()
        }
    
    async def _get_previous_metrics(self, entity_type: str, entity_id: Any) -> Dict[str, Any]:
        """Get previous metrics for comparison"""
        # Mock implementation
        return {
            "points": 118.2,
            "rank": 4,
            "trend": "stable",
            "last_update": (datetime.now() - timedelta(hours=1)).isoformat()
        }
    
    def _calculate_metric_changes(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate changes between metric snapshots"""
        return {
            "points_change": current.get("points", 0) - previous.get("points", 0),
            "rank_change": previous.get("rank", 0) - current.get("rank", 0),
            "trend_change": current.get("trend") != previous.get("trend")
        }
    
    def _generate_alerts(
        self,
        changes: Dict[str, Any],
        entity_type: str,
        entity_id: Any
    ) -> List[Dict[str, Any]]:
        """Generate alerts for significant changes"""
        alerts = []
        
        if abs(changes.get("points_change", 0)) > 10:
            alerts.append({
                "type": "significant_change",
                "message": f"Large points change: {changes['points_change']:+.1f}",
                "severity": "high"
            })
        
        if changes.get("rank_change", 0) > 2:
            alerts.append({
                "type": "rank_improvement",
                "message": f"Rank improved by {changes['rank_change']} positions",
                "severity": "medium"
            })
        
        return alerts
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert analytics data to CSV format"""
        # Simplified implementation
        csv_lines = []
        csv_lines.append("Metric,Value")
        
        def flatten_dict(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flat_data = flatten_dict(data)
        for key, value in flat_data.items():
            csv_lines.append(f"{key},{value}")
        
        return "\n".join(csv_lines)
    
    async def _generate_scoring_trend_chart(
        self,
        team_id: int,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate team scoring trend chart"""
        weeks = list(range(1, 13))
        scores = [115.2, 122.5, 108.9, 131.2, 145.2, 112.8, 125.5, 118.9, 92.4, 128.7, 135.2, 127.8]
        
        return {
            "type": "area",
            "title": "Weekly Scoring Trend",
            "x_axis": {"label": "Week", "data": weeks},
            "y_axis": {"label": "Team Points", "data": scores},
            "average": sum(scores) / len(scores),
            "trend": "improving"
        }
    
    async def _generate_position_strength_chart(self, team_id: int) -> Dict[str, Any]:
        """Generate position strength radar chart"""
        return {
            "type": "radar",
            "title": "Position Strength Analysis",
            "categories": ["QB", "RB", "WR", "TE", "K", "DST"],
            "data": [90, 85, 72, 45, 60, 75],
            "league_average": [70, 70, 70, 70, 70, 70]
        }
    
    async def _generate_efficiency_chart(
        self,
        team_id: int,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate lineup efficiency chart"""
        return {
            "type": "gauge",
            "title": "Lineup Efficiency",
            "value": 88,
            "max": 100,
            "thresholds": {
                "poor": 60,
                "average": 75,
                "good": 85,
                "excellent": 95
            }
        }
    
    async def _generate_team_projections(self, team_id: int) -> Dict[str, Any]:
        """Generate team projections"""
        return {
            "next_week": {
                "projected_points": 125.5,
                "confidence_interval": [110.2, 140.8],
                "win_probability": 0.62
            },
            "playoff_outlook": {
                "make_playoffs": 0.85,
                "win_championship": 0.22,
                "projected_seed": 3
            },
            "rest_of_season": {
                "projected_wins": 10,
                "projected_losses": 6,
                "projected_rank": 3
            }
        }
    
    async def _generate_team_insights(self, metrics: TeamAnalytics) -> List[str]:
        """Generate team insights"""
        insights = []
        
        if metrics.playoff_probability > 0.8:
            insights.append(f"Strong playoff position with {metrics.playoff_probability*100:.0f}% probability")
        
        if metrics.lineup_efficiency > 0.85:
            insights.append(f"Excellent lineup management at {metrics.lineup_efficiency*100:.0f}% efficiency")
        
        if metrics.weakest_positions:
            insights.append(f"Consider upgrades at {', '.join(metrics.weakest_positions)}")
        
        return insights
    
    async def _generate_scoring_distribution_chart(self, league_id: str) -> Dict[str, Any]:
        """Generate league scoring distribution"""
        return {
            "type": "histogram",
            "title": "League Scoring Distribution",
            "bins": ["90-100", "100-110", "110-120", "120-130", "130-140", "140+"],
            "frequencies": [5, 12, 25, 20, 10, 3],
            "average": 118.5,
            "median": 117.2
        }
    
    async def _generate_position_value_chart(self, league_id: str) -> Dict[str, Any]:
        """Generate position value chart"""
        return {
            "type": "bar",
            "title": "Position Value Index",
            "positions": ["QB", "RB", "WR", "TE", "K", "DST"],
            "values": [0.95, 1.20, 1.00, 0.80, 0.60, 0.70],
            "description": "Value relative to replacement level"
        }
    
    async def _generate_parity_chart(
        self,
        league_id: str,
        timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Generate league parity chart"""
        return {
            "type": "scatter",
            "title": "League Parity Analysis",
            "x_axis": {"label": "Wins", "data": [10, 9, 8, 8, 7, 7, 6, 5, 4, 3, 2, 1]},
            "y_axis": {"label": "Points For", "data": [1450, 1420, 1400, 1395, 1380, 1375, 1350, 1320, 1290, 1250, 1200, 1150]},
            "parity_score": 0.75,
            "correlation": 0.82
        }
    
    async def _generate_market_analysis(self, league_id: str) -> Dict[str, Any]:
        """Generate market analysis"""
        return {
            "trade_trends": {
                "volume": 28,
                "trend": "increasing",
                "hot_positions": ["RB", "WR"],
                "most_active_teams": ["Team A", "Team C"]
            },
            "waiver_analysis": {
                "total_moves": 145,
                "avg_per_team": 12.1,
                "most_added_position": "RB",
                "breakout_pickups": ["Player X", "Player Y"]
            },
            "market_efficiency": {
                "score": 0.72,
                "undervalued_players": ["Player A", "Player B"],
                "overvalued_players": ["Player C", "Player D"]
            }
        }
    
    async def _generate_league_insights(self, metrics: LeagueAnalytics) -> List[str]:
        """Generate league insights"""
        insights = []
        
        if metrics.parity_index > 0.7:
            insights.append(f"Highly competitive league with {metrics.parity_index:.2f} parity index")
        
        if metrics.trade_volume > 25:
            insights.append(f"Active trade market with {metrics.trade_volume} trades")
        
        position_scarcity = max(metrics.position_scarcity.items(), key=lambda x: x[1])
        insights.append(f"{position_scarcity[0]} is the scarcest position (scarcity: {position_scarcity[1]:.2f})")
        
        return insights


# Global analytics dashboard instance
analytics_dashboard = AnalyticsDashboard()