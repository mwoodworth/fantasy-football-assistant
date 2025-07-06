"""
Breakout Player Detection System for Fantasy Football Assistant

Advanced machine learning system to identify players likely to have significant 
performance improvements or "breakout" seasons. Uses multiple indicators including:
- Opportunity changes (target share, snap count, role evolution)
- Performance trends and efficiency metrics
- Team situation changes (coaching, scheme, injuries)
- Historical breakout patterns and player development curves
- Advanced metrics and underlying statistics
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import json

logger = logging.getLogger(__name__)


class BreakoutType(Enum):
    """Types of breakout scenarios"""
    OPPORTUNITY_BREAKOUT = "opportunity_breakout"  # Increased role/targets
    EFFICIENCY_BREAKOUT = "efficiency_breakout"   # Better efficiency metrics
    SOPHOMORE_SURGE = "sophomore_surge"           # Second-year player improvement
    VETERAN_RESURGENCE = "veteran_resurgence"     # Older player bounce-back
    SCHEME_FIT = "scheme_fit"                     # New system/coaching fit
    INJURY_OPPORTUNITY = "injury_opportunity"     # Opportunity from teammate injury


class BreakoutLikelihood(Enum):
    """Breakout probability levels"""
    VERY_LOW = "very_low"       # < 10%
    LOW = "low"                 # 10-25%
    MODERATE = "moderate"       # 25-45%
    HIGH = "high"              # 45-70%
    VERY_HIGH = "very_high"    # 70-85%
    ELITE = "elite"            # > 85%


@dataclass
class BreakoutPrediction:
    """Comprehensive breakout prediction for a player"""
    player_id: int
    player_name: str
    position: str
    age: int
    
    # Overall breakout assessment
    breakout_probability: float  # 0-1 probability
    breakout_likelihood: BreakoutLikelihood
    confidence: float
    
    # Breakout type analysis
    breakout_types: Dict[BreakoutType, float]  # Type -> probability
    primary_breakout_type: BreakoutType
    
    # Supporting factors
    opportunity_score: float  # 0-100
    efficiency_trend: float   # -1 to 1
    situation_change_score: float  # 0-100
    
    # Detailed analysis
    key_indicators: List[str]
    supporting_metrics: Dict[str, float]
    risk_factors: List[str]
    
    # Projections
    projected_points_increase: float
    projected_rank_improvement: int
    ceiling_scenario: str
    floor_scenario: str
    
    # Meta information
    prediction_date: datetime
    model_version: str
    historical_comparisons: List[str]


@dataclass
class PlayerProfile:
    """Player profile for breakout analysis"""
    player_id: int
    name: str
    position: str
    age: int
    years_experience: int
    
    # Current season metrics
    games_played: int
    snap_percentage: float
    target_share: float
    usage_rate: float
    points_per_game: float
    
    # Efficiency metrics
    yards_per_target: float
    yards_per_carry: float
    red_zone_usage: float
    air_yards_share: float
    
    # Trend indicators
    recent_performance_trend: float  # Last 4 weeks vs season avg
    opportunity_trend: float         # Snap/target trend
    efficiency_trend: float          # YPT/YPC trend
    
    # Historical data
    career_high_points: float
    last_season_points: float
    breakout_indicators_last_year: int
    
    # Team/situation factors
    team_passing_attempts: int
    team_rushing_attempts: int
    team_pace: float
    coaching_change: bool
    scheme_change: bool
    teammate_injuries: List[str]


class BreakoutIndicatorCalculator:
    """Calculate various breakout indicators for players"""
    
    def __init__(self):
        self.indicator_weights = {
            'opportunity_increase': 0.25,
            'efficiency_improvement': 0.20,
            'age_profile': 0.15,
            'situation_change': 0.15,
            'historical_pattern': 0.15,
            'team_context': 0.10
        }
    
    def calculate_opportunity_indicators(self, profile: PlayerProfile, 
                                       historical_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate opportunity-based breakout indicators"""
        indicators = {}
        
        # Target share growth
        last_year_target_share = historical_data.get('last_year_target_share', profile.target_share)
        target_share_growth = (profile.target_share - last_year_target_share) / max(last_year_target_share, 0.01)
        indicators['target_share_growth'] = min(max(target_share_growth, -1), 2)  # Cap extreme values
        
        # Snap count trend
        snap_trend = profile.opportunity_trend
        indicators['snap_trend'] = snap_trend
        
        # Red zone opportunity
        rz_opportunity = profile.red_zone_usage
        indicators['red_zone_opportunity'] = rz_opportunity
        
        # Depth of target (for receivers)
        if profile.position in ['WR', 'TE']:
            air_yards_trend = profile.air_yards_share - historical_data.get('last_year_air_yards', profile.air_yards_share)
            indicators['air_yards_trend'] = air_yards_trend
        
        # Team volume indicators
        if profile.position == 'RB':
            team_rush_share = profile.usage_rate * profile.team_rushing_attempts / 25  # Normalize
            indicators['team_volume_share'] = team_rush_share
        elif profile.position in ['WR', 'TE']:
            team_target_share = profile.target_share * profile.team_passing_attempts / 35  # Normalize
            indicators['team_volume_share'] = team_target_share
        
        return indicators
    
    def calculate_efficiency_indicators(self, profile: PlayerProfile,
                                      historical_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate efficiency-based breakout indicators"""
        indicators = {}
        
        # Yards per touch efficiency
        if profile.position == 'RB':
            ypc_improvement = profile.yards_per_carry - historical_data.get('last_year_ypc', profile.yards_per_carry)
            indicators['efficiency_improvement'] = ypc_improvement / max(historical_data.get('last_year_ypc', 4.0), 1.0)
        elif profile.position in ['WR', 'TE']:
            ypt_improvement = profile.yards_per_target - historical_data.get('last_year_ypt', profile.yards_per_target)
            indicators['efficiency_improvement'] = ypt_improvement / max(historical_data.get('last_year_ypt', 8.0), 1.0)
        
        # Recent efficiency trend
        indicators['recent_efficiency_trend'] = profile.efficiency_trend
        
        # Touchdown rate (can be volatile but indicates red zone efficiency)
        td_rate = historical_data.get('touchdown_rate', 0.05)
        league_avg_td_rate = 0.06 if profile.position == 'RB' else 0.08
        indicators['td_rate_vs_average'] = (td_rate - league_avg_td_rate) / league_avg_td_rate
        
        # Target quality (for pass catchers)
        if profile.position in ['WR', 'TE']:
            target_quality = profile.air_yards_share / max(profile.target_share, 0.01)
            indicators['target_quality'] = min(target_quality, 3.0)  # Cap extreme values
        
        return indicators
    
    def calculate_age_profile_score(self, profile: PlayerProfile) -> float:
        """Calculate age-based breakout likelihood"""
        # Breakout probability by age for different positions
        age_curves = {
            'RB': {22: 0.3, 23: 0.4, 24: 0.5, 25: 0.3, 26: 0.2, 27: 0.1, 28: 0.05},
            'WR': {22: 0.4, 23: 0.5, 24: 0.6, 25: 0.4, 26: 0.3, 27: 0.2, 28: 0.1, 29: 0.05},
            'TE': {23: 0.3, 24: 0.4, 25: 0.5, 26: 0.4, 27: 0.3, 28: 0.2, 29: 0.1},
            'QB': {23: 0.3, 24: 0.4, 25: 0.5, 26: 0.4, 27: 0.3, 28: 0.3, 29: 0.2, 30: 0.1}
        }
        
        position_curve = age_curves.get(profile.position, age_curves['WR'])
        
        # Find closest age in curve
        closest_age = min(position_curve.keys(), key=lambda x: abs(x - profile.age))
        base_score = position_curve[closest_age]
        
        # Adjust for experience (sometimes more important than age)
        if profile.years_experience <= 2:
            base_score *= 1.2  # Boost for inexperienced players
        elif profile.years_experience >= 8:
            base_score *= 0.6  # Reduce for veterans
        
        return min(base_score, 1.0)
    
    def calculate_situation_change_score(self, profile: PlayerProfile,
                                       team_changes: Dict[str, Any]) -> float:
        """Calculate score based on team/situation changes"""
        score = 0.0
        
        # Coaching change bonus
        if profile.coaching_change:
            score += 0.3
        
        # Scheme change bonus
        if profile.scheme_change:
            score += 0.2
        
        # Teammate injury opportunities
        injury_bonus = len(profile.teammate_injuries) * 0.1
        score += min(injury_bonus, 0.4)  # Cap at 0.4
        
        # Team pace increase
        pace_change = team_changes.get('pace_change', 0)
        if pace_change > 0:
            score += min(pace_change / 10, 0.2)  # More plays = more opportunities
        
        # New quarterback (for pass catchers)
        if profile.position in ['WR', 'TE'] and team_changes.get('qb_change', False):
            qb_quality_change = team_changes.get('qb_quality_change', 0)
            score += qb_quality_change * 0.3
        
        return min(score, 1.0)
    
    def calculate_historical_pattern_score(self, profile: PlayerProfile,
                                         similar_players: List[Dict[str, Any]]) -> float:
        """Calculate score based on historical breakout patterns"""
        if not similar_players:
            return 0.5  # Neutral score if no comparisons
        
        # Calculate breakout rate for similar players
        total_similar = len(similar_players)
        breakout_count = sum(1 for p in similar_players if p.get('had_breakout', False))
        historical_rate = breakout_count / total_similar
        
        # Adjust based on how similar the current player is
        similarity_scores = [p.get('similarity_score', 0.5) for p in similar_players]
        avg_similarity = np.mean(similarity_scores)
        
        # Weight historical rate by similarity
        weighted_score = historical_rate * avg_similarity
        
        return min(weighted_score, 1.0)


class BreakoutDetectionModel:
    """Machine learning model for breakout prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "1.0.0"
        self.last_trained = None
        
        # Load pre-trained model if available
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained breakout detection model"""
        try:
            self.model = joblib.load('models/breakout_detection.pkl')
            self.scaler = joblib.load('models/breakout_scaler.pkl')
            with open('models/breakout_features.json', 'r') as f:
                self.feature_names = json.load(f)
            logger.info("Breakout detection model loaded successfully")
        except FileNotFoundError:
            logger.info("No pre-trained breakout model found, will need training")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize new model with default parameters"""
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced'
        )
        
        self.feature_names = [
            # Opportunity metrics
            'target_share_growth', 'snap_trend', 'red_zone_opportunity',
            'team_volume_share', 'air_yards_trend',
            
            # Efficiency metrics
            'efficiency_improvement', 'recent_efficiency_trend',
            'td_rate_vs_average', 'target_quality',
            
            # Player characteristics
            'age', 'years_experience', 'age_profile_score',
            
            # Situation factors
            'coaching_change', 'scheme_change', 'teammate_injuries_count',
            'pace_change', 'qb_change',
            
            # Historical patterns
            'historical_breakout_rate', 'player_similarity_score',
            
            # Performance metrics
            'points_per_game', 'recent_performance_trend',
            'career_high_ratio', 'last_season_ratio'
        ]
    
    def extract_features(self, profile: PlayerProfile, 
                        indicators: Dict[str, Dict[str, float]],
                        historical_data: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector for breakout prediction"""
        features = []
        
        # Opportunity metrics
        opp_indicators = indicators.get('opportunity', {})
        features.extend([
            opp_indicators.get('target_share_growth', 0),
            opp_indicators.get('snap_trend', 0),
            opp_indicators.get('red_zone_opportunity', 0),
            opp_indicators.get('team_volume_share', 0),
            opp_indicators.get('air_yards_trend', 0)
        ])
        
        # Efficiency metrics
        eff_indicators = indicators.get('efficiency', {})
        features.extend([
            eff_indicators.get('efficiency_improvement', 0),
            eff_indicators.get('recent_efficiency_trend', 0),
            eff_indicators.get('td_rate_vs_average', 0),
            eff_indicators.get('target_quality', 0)
        ])
        
        # Player characteristics
        features.extend([
            profile.age,
            profile.years_experience,
            indicators.get('age_profile_score', 0.5)
        ])
        
        # Situation factors
        features.extend([
            1.0 if profile.coaching_change else 0.0,
            1.0 if profile.scheme_change else 0.0,
            len(profile.teammate_injuries),
            historical_data.get('pace_change', 0),
            1.0 if historical_data.get('qb_change', False) else 0.0
        ])
        
        # Historical patterns
        features.extend([
            indicators.get('historical_breakout_rate', 0.3),
            indicators.get('player_similarity_score', 0.5)
        ])
        
        # Performance metrics
        features.extend([
            profile.points_per_game,
            profile.recent_performance_trend,
            profile.points_per_game / max(profile.career_high_points, 1),
            profile.points_per_game / max(profile.last_season_points, 1)
        ])
        
        return np.array(features, dtype=float)
    
    def predict_breakout(self, features: np.ndarray) -> Tuple[float, float]:
        """Predict breakout probability and confidence"""
        if self.model is None:
            return 0.5, 0.3  # Default values if no model
        
        # Scale features
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Get prediction
        breakout_prob = self.model.predict_proba(features_scaled)[0][1]
        
        # Calculate confidence based on distance from decision boundary
        decision_function = None
        if hasattr(self.model, 'decision_function'):
            decision_function = abs(self.model.decision_function(features_scaled)[0])
            confidence = min(decision_function / 2.0 + 0.5, 1.0)
        else:
            # For Random Forest, use prediction certainty
            confidence = max(self.model.predict_proba(features_scaled)[0]) * 0.8 + 0.2
        
        return breakout_prob, confidence
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_))


class BreakoutDetector:
    """Main breakout detection service"""
    
    def __init__(self):
        self.indicator_calculator = BreakoutIndicatorCalculator()
        self.model = BreakoutDetectionModel()
        self.prediction_cache = {}
        self.cache_duration = timedelta(hours=12)
    
    async def predict_player_breakout(self, player_id: int,
                                    player_data: Dict[str, Any],
                                    historical_data: Optional[Dict[str, Any]] = None,
                                    team_changes: Optional[Dict[str, Any]] = None) -> BreakoutPrediction:
        """Predict breakout potential for a specific player"""
        try:
            # Check cache
            cache_key = f"{player_id}_{hash(str(sorted(player_data.items())))}"
            if cache_key in self.prediction_cache:
                cached_prediction, cache_time = self.prediction_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_prediction
            
            # Create player profile
            profile = self._create_player_profile(player_id, player_data)
            
            # Use default data if not provided
            if historical_data is None:
                historical_data = self._create_default_historical_data(profile)
            if team_changes is None:
                team_changes = self._create_default_team_changes()
            
            # Calculate all indicators
            indicators = await self._calculate_all_indicators(profile, historical_data, team_changes)
            
            # Extract features and predict
            features = self.model.extract_features(profile, indicators, historical_data)
            breakout_prob, confidence = self.model.predict_breakout(features)
            
            # Determine breakout likelihood level
            likelihood = self._classify_breakout_likelihood(breakout_prob)
            
            # Analyze breakout types
            breakout_types = self._analyze_breakout_types(profile, indicators)
            primary_type = max(breakout_types.items(), key=lambda x: x[1])[0]
            
            # Generate supporting analysis
            key_indicators = self._identify_key_indicators(indicators, features)
            supporting_metrics = self._calculate_supporting_metrics(profile, indicators)
            risk_factors = self._identify_risk_factors(profile, indicators)
            
            # Generate projections
            projections = self._generate_projections(profile, breakout_prob, indicators)
            
            # Create prediction
            prediction = BreakoutPrediction(
                player_id=profile.player_id,
                player_name=profile.name,
                position=profile.position,
                age=profile.age,
                breakout_probability=breakout_prob,
                breakout_likelihood=likelihood,
                confidence=confidence,
                breakout_types=breakout_types,
                primary_breakout_type=primary_type,
                opportunity_score=indicators.get('opportunity_score', 50),
                efficiency_trend=indicators.get('efficiency_trend', 0),
                situation_change_score=indicators.get('situation_change_score', 50),
                key_indicators=key_indicators,
                supporting_metrics=supporting_metrics,
                risk_factors=risk_factors,
                projected_points_increase=projections['points_increase'],
                projected_rank_improvement=projections['rank_improvement'],
                ceiling_scenario=projections['ceiling'],
                floor_scenario=projections['floor'],
                prediction_date=datetime.now(),
                model_version=self.model.model_version,
                historical_comparisons=self._find_historical_comparisons(profile)
            )
            
            # Cache prediction
            self.prediction_cache[cache_key] = (prediction, datetime.now())
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting breakout for player {player_id}: {e}")
            return self._create_fallback_prediction(player_id, player_data)
    
    async def get_breakout_candidates(self, player_list: List[Dict[str, Any]],
                                    min_probability: float = 0.4,
                                    max_candidates: int = 20) -> List[BreakoutPrediction]:
        """Get top breakout candidates from a list of players"""
        predictions = []
        
        for player_data in player_list:
            player_id = player_data.get('id', 0)
            prediction = await self.predict_player_breakout(player_id, player_data)
            
            if prediction.breakout_probability >= min_probability:
                predictions.append(prediction)
        
        # Sort by breakout probability and return top candidates
        predictions.sort(key=lambda x: x.breakout_probability, reverse=True)
        return predictions[:max_candidates]
    
    async def _calculate_all_indicators(self, profile: PlayerProfile,
                                      historical_data: Dict[str, Any],
                                      team_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all breakout indicators"""
        indicators = {}
        
        # Opportunity indicators
        opp_indicators = self.indicator_calculator.calculate_opportunity_indicators(profile, historical_data)
        indicators['opportunity'] = opp_indicators
        indicators['opportunity_score'] = np.mean(list(opp_indicators.values())) * 100
        
        # Efficiency indicators
        eff_indicators = self.indicator_calculator.calculate_efficiency_indicators(profile, historical_data)
        indicators['efficiency'] = eff_indicators
        indicators['efficiency_trend'] = eff_indicators.get('recent_efficiency_trend', 0)
        
        # Age profile
        age_score = self.indicator_calculator.calculate_age_profile_score(profile)
        indicators['age_profile_score'] = age_score
        
        # Situation change
        situation_score = self.indicator_calculator.calculate_situation_change_score(profile, team_changes)
        indicators['situation_change_score'] = situation_score * 100
        
        # Historical patterns (mock for now)
        similar_players = []  # Would fetch from database
        historical_score = self.indicator_calculator.calculate_historical_pattern_score(profile, similar_players)
        indicators['historical_breakout_rate'] = historical_score
        indicators['player_similarity_score'] = 0.7  # Mock similarity
        
        return indicators
    
    def _create_player_profile(self, player_id: int, player_data: Dict[str, Any]) -> PlayerProfile:
        """Create PlayerProfile from player data"""
        return PlayerProfile(
            player_id=player_id,
            name=player_data.get('name', f'Player {player_id}'),
            position=player_data.get('position', 'RB'),
            age=player_data.get('age', 24),
            years_experience=player_data.get('years_experience', 2),
            games_played=player_data.get('games_played', 12),
            snap_percentage=player_data.get('snap_percentage', 0.6),
            target_share=player_data.get('target_share', 0.15),
            usage_rate=player_data.get('usage_rate', 0.2),
            points_per_game=player_data.get('points_per_game', 10.0),
            yards_per_target=player_data.get('yards_per_target', 8.0),
            yards_per_carry=player_data.get('yards_per_carry', 4.0),
            red_zone_usage=player_data.get('red_zone_usage', 0.1),
            air_yards_share=player_data.get('air_yards_share', 0.12),
            recent_performance_trend=player_data.get('recent_trend', 0.05),
            opportunity_trend=player_data.get('opportunity_trend', 0.1),
            efficiency_trend=player_data.get('efficiency_trend', 0.05),
            career_high_points=player_data.get('career_high_points', 15.0),
            last_season_points=player_data.get('last_season_points', 8.0),
            breakout_indicators_last_year=player_data.get('breakout_indicators', 2),
            team_passing_attempts=player_data.get('team_pass_attempts', 550),
            team_rushing_attempts=player_data.get('team_rush_attempts', 450),
            team_pace=player_data.get('team_pace', 65.0),
            coaching_change=player_data.get('coaching_change', False),
            scheme_change=player_data.get('scheme_change', False),
            teammate_injuries=player_data.get('teammate_injuries', [])
        )
    
    def _create_default_historical_data(self, profile: PlayerProfile) -> Dict[str, Any]:
        """Create default historical data"""
        return {
            'last_year_target_share': profile.target_share * 0.8,
            'last_year_air_yards': profile.air_yards_share * 0.9,
            'last_year_ypc': profile.yards_per_carry * 0.95,
            'last_year_ypt': profile.yards_per_target * 0.9,
            'touchdown_rate': 0.06,
            'pace_change': 2.0
        }
    
    def _create_default_team_changes(self) -> Dict[str, Any]:
        """Create default team changes"""
        return {
            'pace_change': 0.0,
            'qb_change': False,
            'qb_quality_change': 0.0,
            'offensive_coordinator_change': False
        }
    
    def _classify_breakout_likelihood(self, probability: float) -> BreakoutLikelihood:
        """Convert probability to likelihood level"""
        if probability < 0.1:
            return BreakoutLikelihood.VERY_LOW
        elif probability < 0.25:
            return BreakoutLikelihood.LOW
        elif probability < 0.45:
            return BreakoutLikelihood.MODERATE
        elif probability < 0.7:
            return BreakoutLikelihood.HIGH
        elif probability < 0.85:
            return BreakoutLikelihood.VERY_HIGH
        else:
            return BreakoutLikelihood.ELITE
    
    def _analyze_breakout_types(self, profile: PlayerProfile,
                               indicators: Dict[str, Any]) -> Dict[BreakoutType, float]:
        """Analyze probability of different breakout types"""
        breakout_types = {}
        
        # Opportunity breakout
        opportunity_indicators = indicators.get('opportunity', {})
        opp_score = (
            opportunity_indicators.get('target_share_growth', 0) * 0.4 +
            opportunity_indicators.get('snap_trend', 0) * 0.3 +
            opportunity_indicators.get('team_volume_share', 0) * 0.3
        )
        breakout_types[BreakoutType.OPPORTUNITY_BREAKOUT] = max(0, min(1, opp_score))
        
        # Efficiency breakout
        efficiency_indicators = indicators.get('efficiency', {})
        eff_score = (
            efficiency_indicators.get('efficiency_improvement', 0) * 0.5 +
            efficiency_indicators.get('recent_efficiency_trend', 0) * 0.3 +
            efficiency_indicators.get('td_rate_vs_average', 0) * 0.2
        )
        breakout_types[BreakoutType.EFFICIENCY_BREAKOUT] = max(0, min(1, eff_score))
        
        # Sophomore surge
        if profile.years_experience == 2:
            sophomore_score = 0.6 + indicators.get('age_profile_score', 0) * 0.4
        else:
            sophomore_score = 0.1
        breakout_types[BreakoutType.SOPHOMORE_SURGE] = sophomore_score
        
        # Veteran resurgence
        if profile.age >= 28:
            veteran_score = (indicators.get('situation_change_score', 50) / 100) * 0.7
        else:
            veteran_score = 0.1
        breakout_types[BreakoutType.VETERAN_RESURGENCE] = veteran_score
        
        # Scheme fit
        if profile.coaching_change or profile.scheme_change:
            scheme_score = 0.5 + (indicators.get('situation_change_score', 50) / 200)
        else:
            scheme_score = 0.2
        breakout_types[BreakoutType.SCHEME_FIT] = scheme_score
        
        # Injury opportunity
        injury_score = min(len(profile.teammate_injuries) * 0.3, 0.8)
        breakout_types[BreakoutType.INJURY_OPPORTUNITY] = injury_score
        
        return breakout_types
    
    def _identify_key_indicators(self, indicators: Dict[str, Any],
                                features: np.ndarray) -> List[str]:
        """Identify key indicators supporting breakout prediction"""
        key_indicators = []
        
        # Check opportunity indicators
        opp_indicators = indicators.get('opportunity', {})
        if opp_indicators.get('target_share_growth', 0) > 0.2:
            key_indicators.append("Significant target share increase")
        if opp_indicators.get('snap_trend', 0) > 0.1:
            key_indicators.append("Increasing snap count trend")
        if opp_indicators.get('red_zone_opportunity', 0) > 0.15:
            key_indicators.append("Strong red zone usage")
        
        # Check efficiency indicators
        eff_indicators = indicators.get('efficiency', {})
        if eff_indicators.get('efficiency_improvement', 0) > 0.1:
            key_indicators.append("Improving efficiency metrics")
        if eff_indicators.get('recent_efficiency_trend', 0) > 0.1:
            key_indicators.append("Recent efficiency gains")
        
        # Age and experience factors
        if indicators.get('age_profile_score', 0) > 0.4:
            key_indicators.append("Prime breakout age profile")
        
        # Situation changes
        if indicators.get('situation_change_score', 0) > 60:
            key_indicators.append("Favorable situation changes")
        
        return key_indicators[:5]  # Top 5 indicators
    
    def _calculate_supporting_metrics(self, profile: PlayerProfile,
                                    indicators: Dict[str, Any]) -> Dict[str, float]:
        """Calculate supporting metrics for breakout prediction"""
        return {
            'opportunity_score': indicators.get('opportunity_score', 50),
            'efficiency_trend': indicators.get('efficiency_trend', 0),
            'age_factor': indicators.get('age_profile_score', 0.5),
            'situation_change': indicators.get('situation_change_score', 50) / 100,
            'current_ppg': profile.points_per_game,
            'upside_ratio': profile.career_high_points / max(profile.points_per_game, 1),
            'recent_trend': profile.recent_performance_trend
        }
    
    def _identify_risk_factors(self, profile: PlayerProfile,
                              indicators: Dict[str, Any]) -> List[str]:
        """Identify risk factors that could prevent breakout"""
        risk_factors = []
        
        # Age-related risks
        if profile.age >= 30:
            risk_factors.append("Advanced age may limit upside")
        
        # Opportunity risks
        if indicators.get('opportunity_score', 50) < 30:
            risk_factors.append("Limited opportunity for increased role")
        
        # Efficiency concerns
        if indicators.get('efficiency_trend', 0) < -0.1:
            risk_factors.append("Declining efficiency metrics")
        
        # Team context risks
        if profile.team_pace < 60:
            risk_factors.append("Slow team pace limits opportunities")
        
        # Competition risks
        if len(profile.teammate_injuries) == 0:
            risk_factors.append("No clear injury opportunities")
        
        # Historical performance
        if profile.points_per_game >= profile.career_high_points * 0.9:
            risk_factors.append("Already near career-high performance")
        
        return risk_factors[:4]  # Top 4 risk factors
    
    def _generate_projections(self, profile: PlayerProfile,
                            breakout_prob: float,
                            indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance projections based on breakout analysis"""
        base_ppg = profile.points_per_game
        
        # Calculate potential points increase
        max_increase = (profile.career_high_points - base_ppg) * 1.2  # Allow for new career high
        expected_increase = max_increase * breakout_prob
        
        # Rank improvement estimation (rough)
        points_per_rank = 0.5  # Rough estimate of points difference per ranking position
        rank_improvement = int(expected_increase / points_per_rank)
        
        # Scenario projections
        ceiling_multiplier = 1 + (breakout_prob * 0.8)  # Up to 80% increase in ceiling scenario
        floor_multiplier = max(0.8, 1 + (breakout_prob * 0.2))  # At least 20% of breakout potential
        
        return {
            'points_increase': expected_increase,
            'rank_improvement': rank_improvement,
            'ceiling': f"{base_ppg * ceiling_multiplier:.1f} PPG (Top {max(1, 24 - rank_improvement * 2)} finish)",
            'floor': f"{base_ppg * floor_multiplier:.1f} PPG (Similar to current production)"
        }
    
    def _find_historical_comparisons(self, profile: PlayerProfile) -> List[str]:
        """Find historical player comparisons for context"""
        # Mock historical comparisons - would use actual database
        comparisons = [
            f"Similar to {profile.position} players aged {profile.age} with {profile.years_experience} years experience",
            f"Comparable opportunity profile to breakout candidates from 2019-2022",
            f"Efficiency metrics align with successful {profile.position} breakouts"
        ]
        return comparisons[:3]
    
    def _create_fallback_prediction(self, player_id: int,
                                   player_data: Dict[str, Any]) -> BreakoutPrediction:
        """Create fallback prediction when analysis fails"""
        return BreakoutPrediction(
            player_id=player_id,
            player_name=player_data.get('name', f'Player {player_id}'),
            position=player_data.get('position', 'UNKNOWN'),
            age=player_data.get('age', 25),
            breakout_probability=0.3,
            breakout_likelihood=BreakoutLikelihood.MODERATE,
            confidence=0.4,
            breakout_types={bt: 0.3 for bt in BreakoutType},
            primary_breakout_type=BreakoutType.OPPORTUNITY_BREAKOUT,
            opportunity_score=50.0,
            efficiency_trend=0.0,
            situation_change_score=50.0,
            key_indicators=["Analysis temporarily unavailable"],
            supporting_metrics={},
            risk_factors=["Limited data for assessment"],
            projected_points_increase=2.0,
            projected_rank_improvement=5,
            ceiling_scenario="Moderate upside potential",
            floor_scenario="Current production level",
            prediction_date=datetime.now(),
            model_version="fallback",
            historical_comparisons=["Comparison data unavailable"]
        )


# Global breakout detector instance
breakout_detector = BreakoutDetector()