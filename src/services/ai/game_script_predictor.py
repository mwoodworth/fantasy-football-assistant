"""
Game Script Prediction System for Fantasy Football Assistant

Predicts how NFL games will unfold (game script) and the impact on fantasy player performance.
Game script refers to the flow and strategy of a game based on:
- Score differential and game flow
- Team tendencies and pace
- Weather and situational factors
- Coaching strategies and adjustments
- Player utilization changes based on game state
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
import json

logger = logging.getLogger(__name__)


class GameScript(Enum):
    """Types of game scripts"""
    BLOWOUT_FAVORABLE = "blowout_favorable"      # Team winning big, run-heavy late
    BLOWOUT_UNFAVORABLE = "blowout_unfavorable"  # Team losing big, pass-heavy catchup
    COMPETITIVE = "competitive"                   # Close game, balanced approach
    GRIND_IT_OUT = "grind_it_out"                # Low-scoring, run-heavy game
    SHOOTOUT = "shootout"                        # High-scoring, pass-heavy game
    WEATHER_IMPACTED = "weather_impacted"        # Weather forces conservative game plan
    DEFENSIVE_STRUGGLE = "defensive_struggle"     # Low-scoring defensive battle


class GamePace(Enum):
    """Game pace classifications"""
    VERY_SLOW = "very_slow"    # < 55 plays per team
    SLOW = "slow"              # 55-60 plays per team
    AVERAGE = "average"        # 60-67 plays per team
    FAST = "fast"              # 67-72 plays per team
    VERY_FAST = "very_fast"    # > 72 plays per team


@dataclass
class GameContext:
    """Game context and environment factors"""
    home_team: str
    away_team: str
    week: int
    
    # Vegas information
    point_spread: float  # Positive = home team favored
    total_points: float  # Over/under
    home_implied_score: float
    away_implied_score: float
    
    # Weather conditions
    temperature: int
    wind_speed: int
    precipitation_chance: float
    field_conditions: str
    
    # Game importance
    playoff_implications: bool
    division_game: bool
    prime_time: bool
    
    # Team contexts
    home_team_record: Tuple[int, int]
    away_team_record: Tuple[int, int]
    rest_days_home: int
    rest_days_away: int


@dataclass
class TeamTendencies:
    """Team offensive and defensive tendencies"""
    team_name: str
    
    # Offensive tendencies
    avg_plays_per_game: float
    pass_rate_neutral: float  # Pass rate in neutral game script
    pass_rate_trailing: float  # Pass rate when trailing
    pass_rate_leading: float   # Pass rate when leading
    red_zone_pass_rate: float
    
    # Pace and timing
    seconds_per_play: float
    no_huddle_frequency: float
    
    # Situational usage
    rb_usage_leading: float    # RB usage when leading
    rb_usage_trailing: float   # RB usage when trailing
    target_distribution: Dict[str, float]  # WR1, WR2, TE, RB targets
    
    # Defensive tendencies
    points_allowed_per_game: float
    plays_allowed_per_game: float
    pass_defense_rank: int
    run_defense_rank: int


@dataclass
class GameScriptPrediction:
    """Predicted game script and its implications"""
    home_team: str
    away_team: str
    
    # Game flow predictions
    predicted_script: GameScript
    script_confidence: float
    predicted_pace: GamePace
    
    # Score and pace projections
    predicted_home_score: float
    predicted_away_score: float
    predicted_total_plays_home: int
    predicted_total_plays_away: int
    
    # Game flow timeline
    quarter_scripts: List[GameScript]  # Script for each quarter
    key_turning_points: List[str]
    
    # Fantasy implications
    pass_heavy_team: str  # Which team will be more pass heavy
    run_heavy_team: str   # Which team will be more run heavy
    garbage_time_likely: bool
    defensive_scores_likely: bool
    
    # Player impact factors
    player_impact_modifiers: Dict[str, Dict[str, float]]  # team -> position -> modifier
    
    # Prediction metadata
    prediction_date: datetime
    confidence_factors: List[str]
    risk_factors: List[str]


class GameScriptCalculator:
    """Calculate game script indicators and probabilities"""
    
    def __init__(self):
        self.script_weights = {
            'point_spread': 0.3,
            'total_points': 0.2,
            'team_tendencies': 0.2,
            'weather_impact': 0.15,
            'situational_factors': 0.15
        }
    
    def calculate_script_probabilities(self, game_context: GameContext,
                                     home_tendencies: TeamTendencies,
                                     away_tendencies: TeamTendencies) -> Dict[GameScript, float]:
        """Calculate probability for each game script type"""
        probabilities = {}
        
        # Base probabilities
        for script in GameScript:
            probabilities[script] = 0.1  # Base 10% for each script
        
        # Adjust based on point spread
        spread_impact = self._analyze_spread_impact(game_context.point_spread, game_context.total_points)
        for script, impact in spread_impact.items():
            probabilities[script] += impact
        
        # Adjust based on total points
        total_impact = self._analyze_total_points_impact(game_context.total_points)
        for script, impact in total_impact.items():
            probabilities[script] += impact
        
        # Adjust based on weather
        weather_impact = self._analyze_weather_impact(game_context)
        for script, impact in weather_impact.items():
            probabilities[script] += impact
        
        # Adjust based on team tendencies
        tendency_impact = self._analyze_team_tendencies(home_tendencies, away_tendencies)
        for script, impact in tendency_impact.items():
            probabilities[script] += impact
        
        # Normalize probabilities
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {script: prob / total_prob for script, prob in probabilities.items()}
        
        return probabilities
    
    def _analyze_spread_impact(self, spread: float, total: float) -> Dict[GameScript, float]:
        """Analyze impact of point spread on game script"""
        impact = {}
        
        abs_spread = abs(spread)
        
        if abs_spread >= 10:  # Large spread
            impact[GameScript.BLOWOUT_FAVORABLE] = 0.3
            impact[GameScript.BLOWOUT_UNFAVORABLE] = 0.3
            impact[GameScript.COMPETITIVE] = -0.2
        elif abs_spread >= 6:  # Medium spread
            impact[GameScript.COMPETITIVE] = 0.2
            impact[GameScript.BLOWOUT_FAVORABLE] = 0.1
            impact[GameScript.BLOWOUT_UNFAVORABLE] = 0.1
        else:  # Small spread
            impact[GameScript.COMPETITIVE] = 0.4
            impact[GameScript.BLOWOUT_FAVORABLE] = -0.1
            impact[GameScript.BLOWOUT_UNFAVORABLE] = -0.1
        
        return impact
    
    def _analyze_total_points_impact(self, total: float) -> Dict[GameScript, float]:
        """Analyze impact of total points on game script"""
        impact = {}
        
        if total >= 50:  # High total
            impact[GameScript.SHOOTOUT] = 0.3
            impact[GameScript.DEFENSIVE_STRUGGLE] = -0.2
            impact[GameScript.GRIND_IT_OUT] = -0.1
        elif total <= 42:  # Low total
            impact[GameScript.DEFENSIVE_STRUGGLE] = 0.2
            impact[GameScript.GRIND_IT_OUT] = 0.2
            impact[GameScript.SHOOTOUT] = -0.3
        else:  # Average total
            impact[GameScript.COMPETITIVE] = 0.1
        
        return impact
    
    def _analyze_weather_impact(self, game_context: GameContext) -> Dict[GameScript, float]:
        """Analyze weather impact on game script"""
        impact = {}
        
        # Wind impact
        if game_context.wind_speed >= 20:
            impact[GameScript.WEATHER_IMPACTED] = 0.3
            impact[GameScript.GRIND_IT_OUT] = 0.2
            impact[GameScript.SHOOTOUT] = -0.2
        
        # Precipitation impact
        if game_context.precipitation_chance >= 0.7:
            impact[GameScript.WEATHER_IMPACTED] = 0.2
            impact[GameScript.GRIND_IT_OUT] = 0.2
            impact[GameScript.SHOOTOUT] = -0.2
        
        # Temperature impact
        if game_context.temperature <= 20 or game_context.temperature >= 90:
            impact[GameScript.WEATHER_IMPACTED] = 0.1
            impact[GameScript.GRIND_IT_OUT] = 0.1
        
        return impact
    
    def _analyze_team_tendencies(self, home_tendencies: TeamTendencies,
                                away_tendencies: TeamTendencies) -> Dict[GameScript, float]:
        """Analyze team tendencies impact on game script"""
        impact = {}
        
        # Average pace
        avg_pace = (home_tendencies.seconds_per_play + away_tendencies.seconds_per_play) / 2
        
        if avg_pace <= 24:  # Fast pace
            impact[GameScript.SHOOTOUT] = 0.2
            impact[GameScript.GRIND_IT_OUT] = -0.1
        elif avg_pace >= 28:  # Slow pace
            impact[GameScript.GRIND_IT_OUT] = 0.2
            impact[GameScript.SHOOTOUT] = -0.1
        
        # Defensive strength
        avg_def_rank = (home_tendencies.pass_defense_rank + away_tendencies.pass_defense_rank) / 2
        
        if avg_def_rank <= 10:  # Strong defenses
            impact[GameScript.DEFENSIVE_STRUGGLE] = 0.2
            impact[GameScript.SHOOTOUT] = -0.2
        elif avg_def_rank >= 25:  # Weak defenses
            impact[GameScript.SHOOTOUT] = 0.2
            impact[GameScript.DEFENSIVE_STRUGGLE] = -0.1
        
        return impact
    
    def predict_pace(self, game_context: GameContext,
                    home_tendencies: TeamTendencies,
                    away_tendencies: TeamTendencies,
                    predicted_script: GameScript) -> GamePace:
        """Predict game pace based on context and script"""
        # Base pace from team tendencies
        base_plays = (home_tendencies.avg_plays_per_game + away_tendencies.avg_plays_per_game) / 2
        
        # Adjust based on script
        script_adjustments = {
            GameScript.SHOOTOUT: 1.15,
            GameScript.COMPETITIVE: 1.05,
            GameScript.BLOWOUT_FAVORABLE: 0.95,
            GameScript.BLOWOUT_UNFAVORABLE: 1.10,
            GameScript.GRIND_IT_OUT: 0.85,
            GameScript.WEATHER_IMPACTED: 0.80,
            GameScript.DEFENSIVE_STRUGGLE: 0.90
        }
        
        adjusted_plays = base_plays * script_adjustments.get(predicted_script, 1.0)
        
        # Classify pace
        if adjusted_plays < 55:
            return GamePace.VERY_SLOW
        elif adjusted_plays < 60:
            return GamePace.SLOW
        elif adjusted_plays < 67:
            return GamePace.AVERAGE
        elif adjusted_plays < 72:
            return GamePace.FAST
        else:
            return GamePace.VERY_FAST
    
    def calculate_player_impact_modifiers(self, predicted_script: GameScript,
                                        home_team: str, away_team: str,
                                        game_context: GameContext) -> Dict[str, Dict[str, float]]:
        """Calculate how game script affects different player types"""
        modifiers = {
            home_team: {'QB': 1.0, 'RB': 1.0, 'WR': 1.0, 'TE': 1.0, 'K': 1.0, 'DST': 1.0},
            away_team: {'QB': 1.0, 'RB': 1.0, 'WR': 1.0, 'TE': 1.0, 'K': 1.0, 'DST': 1.0}
        }
        
        # Determine favored/underdog teams
        if game_context.point_spread > 0:  # Home team favored
            favored_team, underdog_team = home_team, away_team
        else:
            favored_team, underdog_team = away_team, home_team
        
        # Apply script-specific modifiers
        if predicted_script == GameScript.BLOWOUT_FAVORABLE:
            # Favored team runs more, underdog passes more
            modifiers[favored_team]['RB'] = 1.3
            modifiers[favored_team]['QB'] = 0.8
            modifiers[favored_team]['WR'] = 0.9
            modifiers[underdog_team]['QB'] = 1.2
            modifiers[underdog_team]['WR'] = 1.2
            modifiers[underdog_team]['RB'] = 0.7
            
        elif predicted_script == GameScript.SHOOTOUT:
            # Both teams pass more
            for team in [home_team, away_team]:
                modifiers[team]['QB'] = 1.3
                modifiers[team]['WR'] = 1.2
                modifiers[team]['TE'] = 1.1
                modifiers[team]['RB'] = 0.8
                
        elif predicted_script == GameScript.GRIND_IT_OUT:
            # Both teams run more
            for team in [home_team, away_team]:
                modifiers[team]['RB'] = 1.3
                modifiers[team]['QB'] = 0.8
                modifiers[team]['WR'] = 0.9
                modifiers[team]['TE'] = 1.1  # Check downs and run blocking
                
        elif predicted_script == GameScript.WEATHER_IMPACTED:
            # Conservative game plan
            for team in [home_team, away_team]:
                modifiers[team]['RB'] = 1.2
                modifiers[team]['QB'] = 0.7
                modifiers[team]['WR'] = 0.8
                modifiers[team]['TE'] = 1.1
                modifiers[team]['K'] = 0.8  # Longer kicks affected by weather
                
        elif predicted_script == GameScript.DEFENSIVE_STRUGGLE:
            # Lower scoring, fewer opportunities
            for team in [home_team, away_team]:
                for position in ['QB', 'RB', 'WR', 'TE']:
                    modifiers[team][position] = 0.9
                modifiers[team]['DST'] = 1.3  # More defensive opportunities
        
        return modifiers


class GameScriptModel:
    """Machine learning model for game script prediction"""
    
    def __init__(self):
        self.script_classifier = None
        self.score_predictor = None
        self.plays_predictor = None
        self.scaler = StandardScaler()
        self.model_version = "1.0.0"
        
        # Load pre-trained models if available
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained game script models"""
        try:
            self.script_classifier = joblib.load('models/game_script_classifier.pkl')
            self.score_predictor = joblib.load('models/game_score_predictor.pkl')
            self.plays_predictor = joblib.load('models/game_plays_predictor.pkl')
            self.scaler = joblib.load('models/game_script_scaler.pkl')
            logger.info("Game script models loaded successfully")
        except FileNotFoundError:
            logger.info("No pre-trained game script models found, using rule-based approach")
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize new models with default parameters"""
        self.script_classifier = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        self.score_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        
        self.plays_predictor = LinearRegression()
    
    def extract_features(self, game_context: GameContext,
                        home_tendencies: TeamTendencies,
                        away_tendencies: TeamTendencies) -> np.ndarray:
        """Extract features for ML models"""
        features = [
            # Vegas information
            game_context.point_spread,
            game_context.total_points,
            game_context.home_implied_score,
            game_context.away_implied_score,
            
            # Weather features
            game_context.temperature,
            game_context.wind_speed,
            game_context.precipitation_chance,
            1.0 if game_context.field_conditions in ['poor', 'terrible'] else 0.0,
            
            # Game importance
            1.0 if game_context.playoff_implications else 0.0,
            1.0 if game_context.division_game else 0.0,
            1.0 if game_context.prime_time else 0.0,
            
            # Team records (win percentage)
            home_tendencies.team_name == "home",  # Placeholder for team strength
            away_tendencies.team_name == "away",
            
            # Rest factors
            game_context.rest_days_home,
            game_context.rest_days_away,
            
            # Team tendencies - offense
            home_tendencies.avg_plays_per_game,
            away_tendencies.avg_plays_per_game,
            home_tendencies.pass_rate_neutral,
            away_tendencies.pass_rate_neutral,
            home_tendencies.seconds_per_play,
            away_tendencies.seconds_per_play,
            
            # Team tendencies - defense
            home_tendencies.points_allowed_per_game,
            away_tendencies.points_allowed_per_game,
            home_tendencies.pass_defense_rank,
            away_tendencies.pass_defense_rank,
            home_tendencies.run_defense_rank,
            away_tendencies.run_defense_rank,
            
            # Derived features
            abs(game_context.point_spread),  # Spread magnitude
            (home_tendencies.avg_plays_per_game + away_tendencies.avg_plays_per_game) / 2,  # Average pace
            abs(home_tendencies.pass_rate_neutral - away_tendencies.pass_rate_neutral),  # Pass rate difference
        ]
        
        return np.array(features, dtype=float)
    
    def predict_game_script(self, features: np.ndarray) -> Tuple[GameScript, float]:
        """Predict game script using ML model or rules"""
        if self.script_classifier is None:
            # Fall back to rule-based prediction
            return GameScript.COMPETITIVE, 0.6
        
        try:
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Get prediction
            script_probs = self.script_classifier.predict_proba(features_scaled)[0]
            script_classes = self.script_classifier.classes_
            
            # Find most likely script
            max_prob_idx = np.argmax(script_probs)
            predicted_script = GameScript(script_classes[max_prob_idx])
            confidence = script_probs[max_prob_idx]
            
            return predicted_script, confidence
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return GameScript.COMPETITIVE, 0.5
    
    def predict_scores(self, features: np.ndarray) -> Tuple[float, float]:
        """Predict final scores for both teams"""
        if self.score_predictor is None:
            # Fall back to implied scores from Vegas
            return 24.0, 21.0  # Default scores
        
        try:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Predict total points and split based on spread
            total_predicted = self.score_predictor.predict(features_scaled)[0]
            
            # Use Vegas implied scores as base
            home_score = total_predicted * 0.52  # Slight home field advantage
            away_score = total_predicted * 0.48
            
            return home_score, away_score
            
        except Exception as e:
            logger.error(f"Error predicting scores: {e}")
            return 24.0, 21.0
    
    def predict_total_plays(self, features: np.ndarray) -> Tuple[int, int]:
        """Predict total plays for both teams"""
        if self.plays_predictor is None:
            return 65, 63  # Default play counts
        
        try:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            total_plays = self.plays_predictor.predict(features_scaled)[0]
            
            # Split based on game script and pace
            home_plays = int(total_plays * 0.51)  # Slight home advantage
            away_plays = int(total_plays * 0.49)
            
            return home_plays, away_plays
            
        except Exception as e:
            logger.error(f"Error predicting plays: {e}")
            return 65, 63


class GameScriptPredictor:
    """Main game script prediction service"""
    
    def __init__(self):
        self.calculator = GameScriptCalculator()
        self.model = GameScriptModel()
        self.prediction_cache = {}
        self.cache_duration = timedelta(hours=24)
    
    async def predict_game_script(self, game_context: GameContext,
                                home_tendencies: TeamTendencies,
                                away_tendencies: TeamTendencies) -> GameScriptPrediction:
        """Predict comprehensive game script for a specific game"""
        try:
            # Check cache
            cache_key = f"{game_context.home_team}_{game_context.away_team}_{game_context.week}"
            if cache_key in self.prediction_cache:
                cached_prediction, cache_time = self.prediction_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_prediction
            
            logger.info(f"Predicting game script for {game_context.away_team} @ {game_context.home_team}")
            
            # Calculate script probabilities
            script_probs = self.calculator.calculate_script_probabilities(
                game_context, home_tendencies, away_tendencies
            )
            
            # Get most likely script
            predicted_script = max(script_probs.items(), key=lambda x: x[1])[0]
            script_confidence = script_probs[predicted_script]
            
            # Predict pace
            predicted_pace = self.calculator.predict_pace(
                game_context, home_tendencies, away_tendencies, predicted_script
            )
            
            # Use ML models for enhanced predictions
            features = self.model.extract_features(game_context, home_tendencies, away_tendencies)
            
            # Get ML predictions
            ml_script, ml_confidence = self.model.predict_game_script(features)
            home_score, away_score = self.model.predict_scores(features)
            home_plays, away_plays = self.model.predict_total_plays(features)
            
            # Blend rule-based and ML predictions
            if script_confidence < 0.6:  # Use ML if rule-based confidence is low
                predicted_script = ml_script
                script_confidence = (script_confidence + ml_confidence) / 2
            
            # Generate quarter-by-quarter script
            quarter_scripts = self._generate_quarter_scripts(predicted_script, game_context)
            
            # Identify key factors and risks
            confidence_factors = self._identify_confidence_factors(game_context, script_probs)
            risk_factors = self._identify_risk_factors(game_context, predicted_script)
            
            # Calculate player impact modifiers
            player_modifiers = self.calculator.calculate_player_impact_modifiers(
                predicted_script, game_context.home_team, game_context.away_team, game_context
            )
            
            # Determine game flow characteristics
            pass_heavy_team, run_heavy_team = self._determine_team_tendencies(
                predicted_script, game_context
            )
            
            # Create prediction
            prediction = GameScriptPrediction(
                home_team=game_context.home_team,
                away_team=game_context.away_team,
                predicted_script=predicted_script,
                script_confidence=script_confidence,
                predicted_pace=predicted_pace,
                predicted_home_score=home_score,
                predicted_away_score=away_score,
                predicted_total_plays_home=home_plays,
                predicted_total_plays_away=away_plays,
                quarter_scripts=quarter_scripts,
                key_turning_points=self._identify_turning_points(predicted_script),
                pass_heavy_team=pass_heavy_team,
                run_heavy_team=run_heavy_team,
                garbage_time_likely=self._assess_garbage_time_likelihood(predicted_script, game_context),
                defensive_scores_likely=self._assess_defensive_score_likelihood(predicted_script),
                player_impact_modifiers=player_modifiers,
                prediction_date=datetime.now(),
                confidence_factors=confidence_factors,
                risk_factors=risk_factors
            )
            
            # Cache prediction
            self.prediction_cache[cache_key] = (prediction, datetime.now())
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting game script: {e}")
            return self._create_fallback_prediction(game_context)
    
    async def predict_multiple_games(self, games: List[Dict[str, Any]]) -> List[GameScriptPrediction]:
        """Predict game scripts for multiple games"""
        predictions = []
        
        for game_data in games:
            try:
                # Create game context from data
                game_context = self._create_game_context_from_data(game_data)
                home_tendencies = self._create_team_tendencies_from_data(game_data, "home")
                away_tendencies = self._create_team_tendencies_from_data(game_data, "away")
                
                prediction = await self.predict_game_script(game_context, home_tendencies, away_tendencies)
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error predicting game script for game: {e}")
                continue
        
        return predictions
    
    def _generate_quarter_scripts(self, overall_script: GameScript,
                                 game_context: GameContext) -> List[GameScript]:
        """Generate likely script for each quarter"""
        quarters = [GameScript.COMPETITIVE] * 4  # Default to competitive
        
        if overall_script == GameScript.BLOWOUT_FAVORABLE:
            quarters = [GameScript.COMPETITIVE, GameScript.COMPETITIVE, 
                       GameScript.BLOWOUT_FAVORABLE, GameScript.BLOWOUT_FAVORABLE]
        elif overall_script == GameScript.SHOOTOUT:
            quarters = [GameScript.SHOOTOUT] * 4
        elif overall_script == GameScript.GRIND_IT_OUT:
            quarters = [GameScript.GRIND_IT_OUT] * 4
        elif overall_script == GameScript.WEATHER_IMPACTED:
            quarters = [GameScript.WEATHER_IMPACTED] * 4
        
        return quarters
    
    def _identify_confidence_factors(self, game_context: GameContext,
                                   script_probs: Dict[GameScript, float]) -> List[str]:
        """Identify factors that increase confidence in prediction"""
        factors = []
        
        # High spread confidence
        if abs(game_context.point_spread) >= 7:
            factors.append("Clear favorite established by betting markets")
        
        # Weather confidence
        if game_context.wind_speed >= 15 or game_context.precipitation_chance >= 0.6:
            factors.append("Weather conditions will impact game plan")
        
        # High total confidence
        if game_context.total_points >= 48 or game_context.total_points <= 42:
            factors.append("Clear pace expectation from betting total")
        
        # Dominant script probability
        max_prob = max(script_probs.values())
        if max_prob >= 0.4:
            factors.append("Strong convergence on most likely script")
        
        return factors
    
    def _identify_risk_factors(self, game_context: GameContext,
                             predicted_script: GameScript) -> List[str]:
        """Identify factors that could disrupt predicted script"""
        risks = []
        
        # Injury risks
        if game_context.week >= 14:
            risks.append("Late season injury risk could change game plan")
        
        # Weather unpredictability
        if game_context.wind_speed >= 10:
            risks.append("Wind conditions could change during game")
        
        # Close spread uncertainty
        if abs(game_context.point_spread) <= 3:
            risks.append("Close spread makes game flow unpredictable")
        
        # Division game chaos
        if game_context.division_game:
            risks.append("Division game rivalries can lead to unexpected game flow")
        
        # Prime time adjustments
        if game_context.prime_time:
            risks.append("Prime time games often have different rhythm and pace")
        
        return risks
    
    def _determine_team_tendencies(self, script: GameScript,
                                 game_context: GameContext) -> Tuple[str, str]:
        """Determine which team will be more pass/run heavy"""
        if script in [GameScript.BLOWOUT_FAVORABLE, GameScript.BLOWOUT_UNFAVORABLE]:
            if game_context.point_spread > 0:  # Home favored
                return game_context.away_team, game_context.home_team  # Away pass, home run
            else:
                return game_context.home_team, game_context.away_team  # Home pass, away run
        elif script == GameScript.SHOOTOUT:
            return "both", "neither"
        elif script in [GameScript.GRIND_IT_OUT, GameScript.WEATHER_IMPACTED]:
            return "neither", "both"
        else:
            return "neutral", "neutral"
    
    def _identify_turning_points(self, script: GameScript) -> List[str]:
        """Identify key turning points that could affect the script"""
        turning_points = []
        
        if script == GameScript.COMPETITIVE:
            turning_points = [
                "First team to score could dictate early pace",
                "Halftime adjustments may change second half approach",
                "Fourth quarter lead changes will impact play calling"
            ]
        elif script == GameScript.BLOWOUT_FAVORABLE:
            turning_points = [
                "Early two-score lead will trigger conservative approach",
                "Garbage time may begin in fourth quarter"
            ]
        elif script == GameScript.SHOOTOUT:
            turning_points = [
                "Neither defense will be able to slow down opposing offense",
                "Teams will abandon running game early"
            ]
        
        return turning_points
    
    def _assess_garbage_time_likelihood(self, script: GameScript,
                                      game_context: GameContext) -> bool:
        """Assess likelihood of garbage time affecting player usage"""
        if script in [GameScript.BLOWOUT_FAVORABLE, GameScript.BLOWOUT_UNFAVORABLE]:
            return abs(game_context.point_spread) >= 7
        return False
    
    def _assess_defensive_score_likelihood(self, script: GameScript) -> bool:
        """Assess likelihood of defensive/special teams scores"""
        return script in [GameScript.DEFENSIVE_STRUGGLE, GameScript.WEATHER_IMPACTED]
    
    def _create_game_context_from_data(self, game_data: Dict[str, Any]) -> GameContext:
        """Create GameContext from game data"""
        return GameContext(
            home_team=game_data.get('home_team', 'HOME'),
            away_team=game_data.get('away_team', 'AWAY'),
            week=game_data.get('week', 1),
            point_spread=game_data.get('spread', 0.0),
            total_points=game_data.get('total', 45.0),
            home_implied_score=game_data.get('home_implied', 22.5),
            away_implied_score=game_data.get('away_implied', 22.5),
            temperature=game_data.get('temperature', 70),
            wind_speed=game_data.get('wind', 5),
            precipitation_chance=game_data.get('precipitation', 0.0),
            field_conditions=game_data.get('field_conditions', 'good'),
            playoff_implications=game_data.get('playoff_implications', False),
            division_game=game_data.get('division_game', False),
            prime_time=game_data.get('prime_time', False),
            home_team_record=(8, 8),
            away_team_record=(8, 8),
            rest_days_home=game_data.get('rest_home', 7),
            rest_days_away=game_data.get('rest_away', 7)
        )
    
    def _create_team_tendencies_from_data(self, game_data: Dict[str, Any], team_type: str) -> TeamTendencies:
        """Create TeamTendencies from game data"""
        prefix = f"{team_type}_"
        
        return TeamTendencies(
            team_name=game_data.get(f'{prefix}team', team_type.upper()),
            avg_plays_per_game=game_data.get(f'{prefix}avg_plays', 65.0),
            pass_rate_neutral=game_data.get(f'{prefix}pass_rate', 0.6),
            pass_rate_trailing=game_data.get(f'{prefix}pass_rate_trailing', 0.7),
            pass_rate_leading=game_data.get(f'{prefix}pass_rate_leading', 0.5),
            red_zone_pass_rate=game_data.get(f'{prefix}rz_pass_rate', 0.6),
            seconds_per_play=game_data.get(f'{prefix}pace', 26.0),
            no_huddle_frequency=game_data.get(f'{prefix}no_huddle', 0.1),
            rb_usage_leading=game_data.get(f'{prefix}rb_leading', 0.4),
            rb_usage_trailing=game_data.get(f'{prefix}rb_trailing', 0.2),
            target_distribution={'WR1': 0.25, 'WR2': 0.15, 'TE': 0.15, 'RB': 0.15},
            points_allowed_per_game=game_data.get(f'{prefix}points_allowed', 23.0),
            plays_allowed_per_game=game_data.get(f'{prefix}plays_allowed', 65.0),
            pass_defense_rank=game_data.get(f'{prefix}pass_def_rank', 16),
            run_defense_rank=game_data.get(f'{prefix}run_def_rank', 16)
        )
    
    def _create_fallback_prediction(self, game_context: GameContext) -> GameScriptPrediction:
        """Create fallback prediction when main prediction fails"""
        return GameScriptPrediction(
            home_team=game_context.home_team,
            away_team=game_context.away_team,
            predicted_script=GameScript.COMPETITIVE,
            script_confidence=0.5,
            predicted_pace=GamePace.AVERAGE,
            predicted_home_score=24.0,
            predicted_away_score=21.0,
            predicted_total_plays_home=65,
            predicted_total_plays_away=63,
            quarter_scripts=[GameScript.COMPETITIVE] * 4,
            key_turning_points=["Game flow unpredictable"],
            pass_heavy_team="neutral",
            run_heavy_team="neutral",
            garbage_time_likely=False,
            defensive_scores_likely=False,
            player_impact_modifiers={
                game_context.home_team: {'QB': 1.0, 'RB': 1.0, 'WR': 1.0, 'TE': 1.0, 'K': 1.0, 'DST': 1.0},
                game_context.away_team: {'QB': 1.0, 'RB': 1.0, 'WR': 1.0, 'TE': 1.0, 'K': 1.0, 'DST': 1.0}
            },
            prediction_date=datetime.now(),
            confidence_factors=["Fallback prediction due to system error"],
            risk_factors=["Prediction accuracy may be limited"]
        )


# Global game script predictor instance
game_script_predictor = GameScriptPredictor()