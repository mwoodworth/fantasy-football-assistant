"""
Advanced Injury Prediction Model for Fantasy Football Assistant

Uses machine learning to predict injury risk based on multiple factors including:
- Player workload and usage patterns
- Historical injury data and recovery times
- Physical metrics and player age
- Game conditions and opponent factors
- Biomechanical risk indicators
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
from sklearn.model_selection import train_test_split
import joblib
import json

logger = logging.getLogger(__name__)


class InjuryRiskLevel(Enum):
    """Injury risk classification levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class InjuryType(Enum):
    """Types of injuries to predict"""
    SOFT_TISSUE = "soft_tissue"  # Hamstring, groin, calf
    JOINT = "joint"  # Knee, ankle, shoulder
    IMPACT = "impact"  # Concussion, bruises
    OVERUSE = "overuse"  # Stress fractures, tendinitis
    CONTACT = "contact"  # Breaks, sprains from hits
    GENERAL = "general"  # Overall injury risk


@dataclass
class InjuryPrediction:
    """Comprehensive injury prediction result"""
    player_id: int
    player_name: str
    position: str
    
    # Overall risk assessment
    overall_risk_level: InjuryRiskLevel
    overall_risk_score: float  # 0-1 probability
    confidence: float
    
    # Risk by injury type
    injury_type_risks: Dict[InjuryType, float]
    
    # Contributing factors
    risk_factors: List[str]
    protective_factors: List[str]
    
    # Recommendations
    recommendations: List[str]
    monitoring_points: List[str]
    
    # Prediction metadata
    prediction_date: datetime
    model_version: str
    data_freshness: str


@dataclass
class PlayerInjuryProfile:
    """Player's injury history and risk profile"""
    player_id: int
    
    # Historical data
    injury_history: List[Dict[str, Any]]
    games_missed_last_season: int
    career_games_missed: int
    
    # Physical profile
    age: int
    position: str
    height: float
    weight: float
    years_experience: int
    
    # Current season metrics
    snap_percentage: float
    usage_rate: float
    workload_trend: str  # "increasing", "stable", "decreasing"
    
    # Risk indicators
    recent_injuries: List[Dict[str, Any]]
    recovery_history: Dict[str, float]  # injury_type -> avg_recovery_days
    
    # External factors
    team_medical_staff_rating: float
    playing_surface_preference: str
    weather_sensitivity: float


class InjuryFeatureExtractor:
    """Extract features for injury prediction models"""
    
    def __init__(self):
        self.feature_names = [
            # Player demographics
            'age', 'position_encoded', 'height', 'weight', 'bmi',
            'years_experience', 'career_games_missed_rate',
            
            # Usage and workload
            'snap_percentage', 'usage_rate', 'touches_per_game',
            'workload_trend_encoded', 'workload_change_rate',
            'consecutive_games_high_usage',
            
            # Performance indicators
            'recent_performance_decline', 'speed_change',
            'efficiency_change', 'target_share_change',
            
            # Injury history
            'injuries_last_season', 'days_since_last_injury',
            'injury_frequency', 'avg_recovery_time',
            'injury_type_history_encoded',
            
            # Game context
            'opponent_defense_rank', 'game_importance',
            'weather_risk_score', 'playing_surface_risk',
            'travel_fatigue_score',
            
            # Team factors
            'team_medical_rating', 'coaching_staff_experience',
            'team_injury_rate', 'practice_intensity',
            
            # Biomechanical risk
            'position_injury_rate', 'play_style_risk',
            'contact_exposure', 'cutting_frequency'
        ]
    
    def extract_features(self, player_profile: PlayerInjuryProfile, 
                        game_context: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector for injury prediction"""
        features = []
        
        # Player demographics
        features.extend([
            player_profile.age,
            self._encode_position(player_profile.position),
            player_profile.height,
            player_profile.weight,
            self._calculate_bmi(player_profile.height, player_profile.weight),
            player_profile.years_experience,
            self._calculate_career_miss_rate(player_profile)
        ])
        
        # Usage and workload
        features.extend([
            player_profile.snap_percentage,
            player_profile.usage_rate,
            game_context.get('touches_per_game', 15.0),
            self._encode_workload_trend(player_profile.workload_trend),
            self._calculate_workload_change(player_profile),
            game_context.get('consecutive_high_usage_games', 0)
        ])
        
        # Performance indicators
        features.extend([
            game_context.get('performance_decline', 0.0),
            game_context.get('speed_change', 0.0),
            game_context.get('efficiency_change', 0.0),
            game_context.get('target_share_change', 0.0)
        ])
        
        # Injury history
        features.extend([
            len([inj for inj in player_profile.recent_injuries if inj.get('season') == 'current']),
            self._days_since_last_injury(player_profile),
            self._calculate_injury_frequency(player_profile),
            self._calculate_avg_recovery_time(player_profile),
            self._encode_injury_history(player_profile)
        ])
        
        # Game context
        features.extend([
            game_context.get('opponent_defense_rank', 16),
            game_context.get('game_importance', 5.0),
            game_context.get('weather_risk', 0.0),
            game_context.get('surface_risk', 0.0),
            game_context.get('travel_fatigue', 0.0)
        ])
        
        # Team factors
        features.extend([
            player_profile.team_medical_staff_rating,
            game_context.get('coaching_experience', 5.0),
            game_context.get('team_injury_rate', 0.15),
            game_context.get('practice_intensity', 5.0)
        ])
        
        # Biomechanical risk
        features.extend([
            self._get_position_injury_rate(player_profile.position),
            self._calculate_play_style_risk(player_profile, game_context),
            self._calculate_contact_exposure(player_profile.position),
            self._calculate_cutting_frequency(player_profile.position)
        ])
        
        return np.array(features, dtype=float)
    
    def _encode_position(self, position: str) -> float:
        """Encode position with injury risk weighting"""
        position_risk = {
            'RB': 0.9, 'WR': 0.6, 'TE': 0.7, 'QB': 0.4,
            'K': 0.1, 'DST': 0.5
        }
        return position_risk.get(position, 0.5)
    
    def _calculate_bmi(self, height: float, weight: float) -> float:
        """Calculate BMI from height and weight"""
        if height <= 0 or weight <= 0:
            return 25.0  # Default BMI
        height_m = height * 0.0254  # inches to meters
        return weight * 0.453592 / (height_m ** 2)  # pounds to kg
    
    def _calculate_career_miss_rate(self, profile: PlayerInjuryProfile) -> float:
        """Calculate career games missed rate"""
        if profile.years_experience <= 0:
            return 0.0
        total_possible_games = profile.years_experience * 17  # Assuming 17 game seasons
        return profile.career_games_missed / max(total_possible_games, 1)
    
    def _encode_workload_trend(self, trend: str) -> float:
        """Encode workload trend"""
        trend_encoding = {
            'increasing': 1.0,
            'stable': 0.0,
            'decreasing': -1.0
        }
        return trend_encoding.get(trend, 0.0)
    
    def _calculate_workload_change(self, profile: PlayerInjuryProfile) -> float:
        """Calculate recent workload change rate"""
        # Mock calculation - would use actual usage data
        if profile.workload_trend == 'increasing':
            return 0.15
        elif profile.workload_trend == 'decreasing':
            return -0.1
        return 0.0
    
    def _days_since_last_injury(self, profile: PlayerInjuryProfile) -> float:
        """Calculate days since last injury"""
        if not profile.recent_injuries:
            return 365.0  # No recent injuries
        
        last_injury = max(profile.recent_injuries, 
                         key=lambda x: x.get('date', datetime.min))
        days_since = (datetime.now() - last_injury.get('date', datetime.now())).days
        return min(days_since, 365.0)
    
    def _calculate_injury_frequency(self, profile: PlayerInjuryProfile) -> float:
        """Calculate injury frequency (injuries per season)"""
        if profile.years_experience <= 0:
            return 0.0
        return len(profile.injury_history) / profile.years_experience
    
    def _calculate_avg_recovery_time(self, profile: PlayerInjuryProfile) -> float:
        """Calculate average recovery time from injuries"""
        if not profile.recovery_history:
            return 14.0  # Default 2 weeks
        return np.mean(list(profile.recovery_history.values()))
    
    def _encode_injury_history(self, profile: PlayerInjuryProfile) -> float:
        """Encode injury type history"""
        # Weighted score based on injury type severity
        severity_weights = {
            'soft_tissue': 0.6,
            'joint': 0.9,
            'impact': 0.4,
            'overuse': 0.7,
            'contact': 0.8
        }
        
        if not profile.injury_history:
            return 0.0
        
        total_weight = sum(severity_weights.get(inj.get('type', 'general'), 0.5) 
                          for inj in profile.injury_history)
        return total_weight / len(profile.injury_history)
    
    def _get_position_injury_rate(self, position: str) -> float:
        """Get historical injury rate for position"""
        position_rates = {
            'RB': 0.35, 'WR': 0.25, 'TE': 0.28, 'QB': 0.18,
            'K': 0.05, 'DST': 0.20
        }
        return position_rates.get(position, 0.25)
    
    def _calculate_play_style_risk(self, profile: PlayerInjuryProfile, 
                                  context: Dict[str, Any]) -> float:
        """Calculate play style injury risk"""
        # Mock calculation based on position and usage
        base_risk = self._encode_position(profile.position)
        usage_multiplier = min(profile.usage_rate / 0.2, 2.0)  # Cap at 2x
        return base_risk * usage_multiplier
    
    def _calculate_contact_exposure(self, position: str) -> float:
        """Calculate contact exposure by position"""
        contact_levels = {
            'RB': 0.9, 'TE': 0.7, 'WR': 0.5, 'QB': 0.3,
            'K': 0.1, 'DST': 0.8
        }
        return contact_levels.get(position, 0.5)
    
    def _calculate_cutting_frequency(self, position: str) -> float:
        """Calculate cutting/agility demand by position"""
        cutting_levels = {
            'RB': 0.9, 'WR': 0.8, 'TE': 0.6, 'QB': 0.4,
            'K': 0.1, 'DST': 0.7
        }
        return cutting_levels.get(position, 0.5)


class InjuryPredictionModel:
    """Advanced injury prediction ML model"""
    
    def __init__(self):
        self.feature_extractor = InjuryFeatureExtractor()
        self.scaler = StandardScaler()
        
        # Model ensemble
        self.overall_risk_model = None  # RandomForestClassifier
        self.injury_type_models = {}  # Dict[InjuryType, model]
        self.severity_model = None  # GradientBoostingRegressor
        
        # Model metadata
        self.model_version = "1.0.0"
        self.last_trained = None
        self.training_samples = 0
        
        # Load pre-trained models if available
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            self.overall_risk_model = joblib.load('models/injury_overall_risk.pkl')
            self.scaler = joblib.load('models/injury_scaler.pkl')
            
            # Load injury type models
            for injury_type in InjuryType:
                try:
                    model = joblib.load(f'models/injury_{injury_type.value}.pkl')
                    self.injury_type_models[injury_type] = model
                except FileNotFoundError:
                    logger.warning(f"Model for {injury_type.value} not found")
            
            self.severity_model = joblib.load('models/injury_severity.pkl')
            logger.info("Injury prediction models loaded successfully")
            
        except FileNotFoundError:
            logger.info("No pre-trained injury models found, will create new ones")
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize new models with default parameters"""
        # Overall risk classifier
        self.overall_risk_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced'
        )
        
        # Injury type specific models
        for injury_type in InjuryType:
            self.injury_type_models[injury_type] = LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            )
        
        # Severity regression model
        self.severity_model = GradientBoostingRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        
        logger.info("New injury prediction models initialized")
    
    def train_models(self, training_data: pd.DataFrame):
        """Train all injury prediction models"""
        logger.info("Starting injury prediction model training")
        
        # Extract features and targets
        X = np.array([self.feature_extractor.extract_features(
            self._create_player_profile(row), 
            self._create_game_context(row)
        ) for _, row in training_data.iterrows()])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train overall risk model
        y_overall = training_data['injury_occurred'].astype(int)
        self.overall_risk_model.fit(X_scaled, y_overall)
        
        # Train injury type models
        for injury_type in InjuryType:
            if f'injury_{injury_type.value}' in training_data.columns:
                y_type = training_data[f'injury_{injury_type.value}'].astype(int)
                self.injury_type_models[injury_type].fit(X_scaled, y_type)
        
        # Train severity model
        if 'injury_severity' in training_data.columns:
            y_severity = training_data['injury_severity']
            self.severity_model.fit(X_scaled, y_severity)
        
        # Update metadata
        self.last_trained = datetime.now()
        self.training_samples = len(training_data)
        
        # Save models
        self._save_models()
        
        logger.info(f"Injury prediction models trained on {len(training_data)} samples")
    
    def predict_injury_risk(self, player_profile: PlayerInjuryProfile,
                           game_context: Dict[str, Any]) -> InjuryPrediction:
        """Predict comprehensive injury risk for a player"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(player_profile, game_context)
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Overall risk prediction
            overall_risk_prob = self.overall_risk_model.predict_proba(features_scaled)[0]
            overall_risk_score = overall_risk_prob[1]  # Probability of injury
            overall_risk_level = self._classify_risk_level(overall_risk_score)
            
            # Injury type predictions
            injury_type_risks = {}
            for injury_type, model in self.injury_type_models.items():
                try:
                    type_prob = model.predict_proba(features_scaled)[0]
                    injury_type_risks[injury_type] = type_prob[1]
                except Exception as e:
                    logger.warning(f"Error predicting {injury_type.value}: {e}")
                    injury_type_risks[injury_type] = 0.0
            
            # Generate risk factors and recommendations
            risk_factors = self._identify_risk_factors(features, player_profile, game_context)
            protective_factors = self._identify_protective_factors(features, player_profile)
            recommendations = self._generate_recommendations(overall_risk_level, risk_factors)
            monitoring_points = self._generate_monitoring_points(injury_type_risks, player_profile)
            
            # Calculate confidence
            confidence = self._calculate_prediction_confidence(features, overall_risk_score)
            
            return InjuryPrediction(
                player_id=player_profile.player_id,
                player_name=f"Player {player_profile.player_id}",  # Would fetch actual name
                position=player_profile.position,
                overall_risk_level=overall_risk_level,
                overall_risk_score=overall_risk_score,
                confidence=confidence,
                injury_type_risks=injury_type_risks,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                recommendations=recommendations,
                monitoring_points=monitoring_points,
                prediction_date=datetime.now(),
                model_version=self.model_version,
                data_freshness="current"
            )
            
        except Exception as e:
            logger.error(f"Error predicting injury risk for player {player_profile.player_id}: {e}")
            return self._create_fallback_prediction(player_profile)
    
    def _classify_risk_level(self, risk_score: float) -> InjuryRiskLevel:
        """Convert risk score to risk level"""
        if risk_score < 0.1:
            return InjuryRiskLevel.VERY_LOW
        elif risk_score < 0.2:
            return InjuryRiskLevel.LOW
        elif risk_score < 0.35:
            return InjuryRiskLevel.MODERATE
        elif risk_score < 0.5:
            return InjuryRiskLevel.ELEVATED
        elif risk_score < 0.7:
            return InjuryRiskLevel.HIGH
        else:
            return InjuryRiskLevel.CRITICAL
    
    def _identify_risk_factors(self, features: np.ndarray, 
                              profile: PlayerInjuryProfile, 
                              context: Dict[str, Any]) -> List[str]:
        """Identify key risk factors for injury"""
        risk_factors = []
        
        # Age factor
        if profile.age > 30:
            risk_factors.append("Advanced age increases injury susceptibility")
        
        # Usage factor
        if profile.usage_rate > 0.25:
            risk_factors.append("High usage rate elevates injury risk")
        
        # Injury history
        if len(profile.recent_injuries) > 0:
            risk_factors.append("Recent injury history indicates vulnerability")
        
        # Workload trend
        if profile.workload_trend == "increasing":
            risk_factors.append("Increasing workload raises injury probability")
        
        # Position risk
        if profile.position in ['RB', 'TE']:
            risk_factors.append("Position involves high contact exposure")
        
        # Game context
        if context.get('weather_risk', 0) > 0.5:
            risk_factors.append("Adverse weather conditions increase risk")
        
        return risk_factors[:5]  # Top 5 factors
    
    def _identify_protective_factors(self, features: np.ndarray,
                                   profile: PlayerInjuryProfile) -> List[str]:
        """Identify protective factors against injury"""
        protective_factors = []
        
        # Youth
        if profile.age < 26:
            protective_factors.append("Younger age provides injury resilience")
        
        # Medical staff
        if profile.team_medical_staff_rating > 0.8:
            protective_factors.append("Excellent medical staff support")
        
        # Recovery history
        if profile.recovery_history and np.mean(list(profile.recovery_history.values())) < 10:
            protective_factors.append("History of quick injury recovery")
        
        # Usage management
        if profile.usage_rate < 0.2:
            protective_factors.append("Managed workload reduces injury risk")
        
        # No recent injuries
        if not profile.recent_injuries:
            protective_factors.append("Clean recent injury history")
        
        return protective_factors[:3]  # Top 3 factors
    
    def _generate_recommendations(self, risk_level: InjuryRiskLevel,
                                 risk_factors: List[str]) -> List[str]:
        """Generate injury prevention recommendations"""
        recommendations = []
        
        if risk_level in [InjuryRiskLevel.HIGH, InjuryRiskLevel.CRITICAL]:
            recommendations.extend([
                "Consider reduced practice participation",
                "Increase recovery and treatment time",
                "Monitor closely for early injury signs"
            ])
        elif risk_level == InjuryRiskLevel.ELEVATED:
            recommendations.extend([
                "Implement additional warm-up routines",
                "Consider load management strategies",
                "Enhanced injury prevention protocols"
            ])
        else:
            recommendations.append("Continue standard injury prevention practices")
        
        # Risk factor specific recommendations
        if "High usage rate" in ' '.join(risk_factors):
            recommendations.append("Consider reducing snap count in blowout games")
        
        if "Recent injury history" in ' '.join(risk_factors):
            recommendations.append("Focus on strengthening previously injured areas")
        
        return recommendations[:4]  # Top 4 recommendations
    
    def _generate_monitoring_points(self, injury_type_risks: Dict[InjuryType, float],
                                   profile: PlayerInjuryProfile) -> List[str]:
        """Generate key monitoring points"""
        monitoring_points = []
        
        # Monitor highest risk injury types
        sorted_risks = sorted(injury_type_risks.items(), key=lambda x: x[1], reverse=True)
        
        for injury_type, risk in sorted_risks[:2]:
            if risk > 0.3:
                monitoring_points.append(f"Monitor for {injury_type.value.replace('_', ' ')} injury signs")
        
        # Position-specific monitoring
        if profile.position == 'RB':
            monitoring_points.append("Watch for signs of lower body fatigue")
        elif profile.position == 'WR':
            monitoring_points.append("Monitor ankle and knee stability")
        elif profile.position == 'QB':
            monitoring_points.append("Track throwing arm and shoulder health")
        
        return monitoring_points[:3]  # Top 3 monitoring points
    
    def _calculate_prediction_confidence(self, features: np.ndarray, 
                                        risk_score: float) -> float:
        """Calculate confidence in prediction"""
        # Base confidence on feature completeness and model certainty
        base_confidence = 0.7
        
        # Adjust for extreme predictions (more confident)
        if risk_score < 0.1 or risk_score > 0.8:
            base_confidence += 0.2
        
        # Adjust for moderate predictions (less confident)
        if 0.4 <= risk_score <= 0.6:
            base_confidence -= 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _create_player_profile(self, data_row) -> PlayerInjuryProfile:
        """Create player profile from training data row"""
        # Mock implementation - would extract from actual data
        return PlayerInjuryProfile(
            player_id=data_row.get('player_id', 0),
            injury_history=[],
            games_missed_last_season=data_row.get('games_missed_last_season', 0),
            career_games_missed=data_row.get('career_games_missed', 0),
            age=data_row.get('age', 25),
            position=data_row.get('position', 'RB'),
            height=data_row.get('height', 72.0),
            weight=data_row.get('weight', 200.0),
            years_experience=data_row.get('years_experience', 3),
            snap_percentage=data_row.get('snap_percentage', 0.6),
            usage_rate=data_row.get('usage_rate', 0.2),
            workload_trend=data_row.get('workload_trend', 'stable'),
            recent_injuries=[],
            recovery_history={},
            team_medical_staff_rating=data_row.get('medical_rating', 0.8),
            playing_surface_preference='grass',
            weather_sensitivity=0.0
        )
    
    def _create_game_context(self, data_row) -> Dict[str, Any]:
        """Create game context from training data row"""
        return {
            'touches_per_game': data_row.get('touches_per_game', 15.0),
            'opponent_defense_rank': data_row.get('opponent_def_rank', 16),
            'weather_risk': data_row.get('weather_risk', 0.0),
            'game_importance': data_row.get('game_importance', 5.0),
            'travel_fatigue': data_row.get('travel_fatigue', 0.0)
        }
    
    def _create_fallback_prediction(self, profile: PlayerInjuryProfile) -> InjuryPrediction:
        """Create fallback prediction when model fails"""
        return InjuryPrediction(
            player_id=profile.player_id,
            player_name=f"Player {profile.player_id}",
            position=profile.position,
            overall_risk_level=InjuryRiskLevel.MODERATE,
            overall_risk_score=0.25,
            confidence=0.3,
            injury_type_risks={injury_type: 0.2 for injury_type in InjuryType},
            risk_factors=["Limited data available for prediction"],
            protective_factors=["Standard injury prevention practices"],
            recommendations=["Continue monitoring player health"],
            monitoring_points=["Watch for any signs of discomfort"],
            prediction_date=datetime.now(),
            model_version=self.model_version,
            data_freshness="limited"
        )
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.overall_risk_model, 'models/injury_overall_risk.pkl')
            joblib.dump(self.scaler, 'models/injury_scaler.pkl')
            
            for injury_type, model in self.injury_type_models.items():
                joblib.dump(model, f'models/injury_{injury_type.value}.pkl')
            
            joblib.dump(self.severity_model, 'models/injury_severity.pkl')
            
            logger.info("Injury prediction models saved successfully")
        except Exception as e:
            logger.error(f"Error saving injury models: {e}")


class InjuryPredictor:
    """Main injury prediction service"""
    
    def __init__(self):
        self.model = InjuryPredictionModel()
        self.prediction_cache = {}
        self.cache_duration = timedelta(hours=6)
    
    async def predict_player_injury_risk(self, player_id: int, 
                                       player_data: Dict[str, Any],
                                       game_context: Optional[Dict[str, Any]] = None) -> InjuryPrediction:
        """Predict injury risk for a specific player"""
        try:
            # Check cache first
            cache_key = f"{player_id}_{hash(str(sorted(player_data.items())))}"
            if cache_key in self.prediction_cache:
                cached_prediction, cache_time = self.prediction_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_prediction
            
            # Create player profile
            player_profile = self._create_player_profile_from_data(player_id, player_data)
            
            # Use provided game context or create default
            if game_context is None:
                game_context = self._create_default_game_context()
            
            # Get prediction
            prediction = self.model.predict_injury_risk(player_profile, game_context)
            
            # Cache result
            self.prediction_cache[cache_key] = (prediction, datetime.now())
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting injury risk for player {player_id}: {e}")
            return self._create_default_prediction(player_id, player_data)
    
    async def predict_team_injury_risks(self, team_roster: List[Dict[str, Any]],
                                       game_context: Optional[Dict[str, Any]] = None) -> List[InjuryPrediction]:
        """Predict injury risks for entire team roster"""
        predictions = []
        
        for player_data in team_roster:
            player_id = player_data.get('id', 0)
            prediction = await self.predict_player_injury_risk(player_id, player_data, game_context)
            predictions.append(prediction)
        
        return predictions
    
    async def get_high_risk_players(self, team_roster: List[Dict[str, Any]],
                                   risk_threshold: float = 0.4) -> List[InjuryPrediction]:
        """Get players with high injury risk"""
        all_predictions = await self.predict_team_injury_risks(team_roster)
        return [pred for pred in all_predictions if pred.overall_risk_score >= risk_threshold]
    
    def _create_player_profile_from_data(self, player_id: int, 
                                        player_data: Dict[str, Any]) -> PlayerInjuryProfile:
        """Create PlayerInjuryProfile from player data"""
        return PlayerInjuryProfile(
            player_id=player_id,
            injury_history=player_data.get('injury_history', []),
            games_missed_last_season=player_data.get('games_missed_last_season', 0),
            career_games_missed=player_data.get('career_games_missed', 0),
            age=player_data.get('age', 25),
            position=player_data.get('position', 'RB'),
            height=player_data.get('height', 72.0),
            weight=player_data.get('weight', 200.0),
            years_experience=player_data.get('years_experience', 3),
            snap_percentage=player_data.get('snap_percentage', 0.6),
            usage_rate=player_data.get('usage_rate', 0.2),
            workload_trend=player_data.get('workload_trend', 'stable'),
            recent_injuries=player_data.get('recent_injuries', []),
            recovery_history=player_data.get('recovery_history', {}),
            team_medical_staff_rating=player_data.get('team_medical_rating', 0.8),
            playing_surface_preference=player_data.get('surface_preference', 'grass'),
            weather_sensitivity=player_data.get('weather_sensitivity', 0.0)
        )
    
    def _create_default_game_context(self) -> Dict[str, Any]:
        """Create default game context"""
        return {
            'touches_per_game': 15.0,
            'opponent_defense_rank': 16,
            'weather_risk': 0.0,
            'game_importance': 5.0,
            'travel_fatigue': 0.0,
            'surface_risk': 0.0,
            'practice_intensity': 5.0
        }
    
    def _create_default_prediction(self, player_id: int, 
                                  player_data: Dict[str, Any]) -> InjuryPrediction:
        """Create default prediction when system fails"""
        return InjuryPrediction(
            player_id=player_id,
            player_name=player_data.get('name', f'Player {player_id}'),
            position=player_data.get('position', 'UNKNOWN'),
            overall_risk_level=InjuryRiskLevel.MODERATE,
            overall_risk_score=0.25,
            confidence=0.3,
            injury_type_risks={injury_type: 0.2 for injury_type in InjuryType},
            risk_factors=["Assessment temporarily unavailable"],
            protective_factors=["Standard injury prevention"],
            recommendations=["Monitor player status"],
            monitoring_points=["Check for injury updates"],
            prediction_date=datetime.now(),
            model_version="fallback",
            data_freshness="unavailable"
        )


# Global injury predictor instance
injury_predictor = InjuryPredictor()