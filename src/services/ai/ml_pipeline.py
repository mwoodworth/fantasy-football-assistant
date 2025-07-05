"""
Machine Learning Pipeline for Fantasy Football Assistant

Handles player performance prediction, breakout analysis, injury risk assessment,
and other ML-powered fantasy football insights.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import pickle
import logging
from datetime import datetime, timedelta
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, accuracy_score, roc_auc_score
import xgboost as xgb

logger = logging.getLogger(__name__)


class MLPipeline:
    """Machine learning pipeline for fantasy football predictions"""
    
    def __init__(self):
        """Initialize ML pipeline with default models"""
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_metrics = {}
        
        # Define model configurations
        self.model_configs = {
            "points_prediction": {
                "model": RandomForestRegressor(n_estimators=100, random_state=42),
                "type": "regression",
                "target": "fantasy_points"
            },
            "boom_bust_classifier": {
                "model": GradientBoostingClassifier(n_estimators=100, random_state=42),
                "type": "classification",
                "target": "boom_game"  # >20% above season average
            },
            "injury_risk": {
                "model": LogisticRegression(random_state=42),
                "type": "classification", 
                "target": "injury_next_week"
            },
            "breakout_predictor": {
                "model": xgb.XGBClassifier(random_state=42),
                "type": "classification",
                "target": "breakout_candidate"
            }
        }
        
        # Feature definitions
        self.feature_definitions = self._get_feature_definitions()
        
        # Model storage path
        self.model_path = Path("models")
        self.model_path.mkdir(exist_ok=True)
    
    def _get_feature_definitions(self) -> Dict[str, List[str]]:
        """Define features for each model type"""
        return {
            "basic_stats": [
                "games_played", "snaps_per_game", "snap_percentage",
                "targets_per_game", "carries_per_game", "red_zone_touches",
                "goal_line_carries", "target_share", "air_yards_per_target"
            ],
            "performance_metrics": [
                "avg_points_last_4", "avg_points_last_2", "season_avg_points",
                "points_variance", "consistency_score", "ceiling_games",
                "floor_games", "boom_percentage", "bust_percentage"
            ],
            "team_context": [
                "team_pace", "team_pass_rate", "team_run_rate", 
                "red_zone_efficiency", "offensive_line_rank", "team_scoring_avg",
                "team_total_plays", "team_time_of_possession"
            ],
            "matchup_factors": [
                "opp_def_rank_vs_pos", "opp_points_allowed_vs_pos",
                "opp_yards_allowed_vs_pos", "opp_def_dvoa_vs_pos",
                "home_away_indicator", "divisional_game", "prime_time_game"
            ],
            "external_factors": [
                "weather_temperature", "weather_wind_speed", "weather_precipitation",
                "vegas_implied_points", "vegas_spread", "rest_days",
                "days_since_injury", "age", "years_experience"
            ],
            "advanced_metrics": [
                "air_yards_share", "wopr", "racr", "target_quality",
                "goal_line_share", "two_minute_drill_usage", "situation_rate",
                "pressure_rate_allowed", "yards_after_contact"
            ]
        }
    
    def prepare_features(self, player_data: Dict[str, Any], week_context: Dict[str, Any]) -> np.ndarray:
        """
        Prepare feature vector for a player
        
        Args:
            player_data: Player statistics and information
            week_context: Context for the specific week (opponent, weather, etc.)
            
        Returns:
            Feature vector for model prediction
        """
        features = []
        
        # Basic stats features
        for feature in self.feature_definitions["basic_stats"]:
            features.append(player_data.get(feature, 0))
        
        # Performance metrics
        for feature in self.feature_definitions["performance_metrics"]:
            features.append(player_data.get(feature, 0))
        
        # Team context
        for feature in self.feature_definitions["team_context"]:
            features.append(player_data.get(feature, 0))
        
        # Matchup factors
        for feature in self.feature_definitions["matchup_factors"]:
            features.append(week_context.get(feature, 0))
        
        # External factors
        for feature in self.feature_definitions["external_factors"]:
            features.append(week_context.get(feature, 0))
        
        # Advanced metrics
        for feature in self.feature_definitions["advanced_metrics"]:
            features.append(player_data.get(feature, 0))
        
        return np.array(features).reshape(1, -1)
    
    def predict_player_points(
        self, 
        player_data: Dict[str, Any], 
        week_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict fantasy points for a player
        
        Args:
            player_data: Player statistics and context
            week_context: Week-specific factors
            
        Returns:
            Prediction with confidence intervals
        """
        if "points_prediction" not in self.models:
            logger.warning("Points prediction model not trained")
            return {"prediction": 0, "confidence": 0, "error": "model_not_trained"}
        
        try:
            # Prepare features
            features = self.prepare_features(player_data, week_context)
            
            # Scale features if scaler exists
            if "points_prediction" in self.scalers:
                features = self.scalers["points_prediction"].transform(features)
            
            # Make prediction
            model = self.models["points_prediction"]
            prediction = model.predict(features)[0]
            
            # Calculate prediction intervals (using tree-based uncertainty)
            if hasattr(model, "estimators_"):
                tree_predictions = [tree.predict(features)[0] for tree in model.estimators_]
                std_dev = np.std(tree_predictions)
                confidence_interval = {
                    "lower": prediction - 1.96 * std_dev,
                    "upper": prediction + 1.96 * std_dev
                }
            else:
                confidence_interval = {
                    "lower": prediction * 0.8,
                    "upper": prediction * 1.2
                }
            
            # Calculate confidence based on model metrics
            confidence = self._calculate_prediction_confidence(
                prediction, player_data, "points_prediction"
            )
            
            return {
                "prediction": round(prediction, 2),
                "confidence": confidence,
                "confidence_interval": confidence_interval,
                "model_accuracy": self.model_metrics.get("points_prediction", {}).get("mae", 0)
            }
            
        except Exception as e:
            logger.error(f"Error predicting player points: {e}")
            return {"prediction": 0, "confidence": 0, "error": str(e)}
    
    def predict_boom_bust_probability(
        self, 
        player_data: Dict[str, Any], 
        week_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict probability of boom/bust game
        
        Args:
            player_data: Player statistics
            week_context: Week context
            
        Returns:
            Boom/bust probabilities
        """
        if "boom_bust_classifier" not in self.models:
            return {"boom_prob": 0.5, "bust_prob": 0.5, "error": "model_not_trained"}
        
        try:
            features = self.prepare_features(player_data, week_context)
            
            if "boom_bust_classifier" in self.scalers:
                features = self.scalers["boom_bust_classifier"].transform(features)
            
            model = self.models["boom_bust_classifier"]
            probabilities = model.predict_proba(features)[0]
            
            return {
                "boom_probability": round(probabilities[1], 3),
                "bust_probability": round(probabilities[0], 3),
                "prediction": "boom" if probabilities[1] > 0.5 else "bust",
                "confidence": max(probabilities),
                "model_accuracy": self.model_metrics.get("boom_bust_classifier", {}).get("accuracy", 0)
            }
            
        except Exception as e:
            logger.error(f"Error predicting boom/bust: {e}")
            return {"boom_prob": 0.5, "bust_prob": 0.5, "error": str(e)}
    
    def assess_injury_risk(
        self, 
        player_data: Dict[str, Any], 
        health_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess injury risk for a player
        
        Args:
            player_data: Player data including injury history
            health_context: Current health status and factors
            
        Returns:
            Injury risk assessment
        """
        if "injury_risk" not in self.models:
            return {"risk_level": "unknown", "probability": 0.5, "error": "model_not_trained"}
        
        try:
            # Combine player data with health context
            combined_data = {**player_data, **health_context}
            features = self.prepare_features(combined_data, {})
            
            if "injury_risk" in self.scalers:
                features = self.scalers["injury_risk"].transform(features)
            
            model = self.models["injury_risk"]
            probability = model.predict_proba(features)[0][1]  # Probability of injury
            
            # Categorize risk level
            if probability < 0.2:
                risk_level = "low"
            elif probability < 0.4:
                risk_level = "moderate"
            elif probability < 0.6:
                risk_level = "elevated"
            else:
                risk_level = "high"
            
            return {
                "injury_probability": round(probability, 3),
                "risk_level": risk_level,
                "recommendation": self._get_injury_risk_recommendation(risk_level),
                "factors": self._get_top_injury_risk_factors(combined_data),
                "model_accuracy": self.model_metrics.get("injury_risk", {}).get("auc", 0)
            }
            
        except Exception as e:
            logger.error(f"Error assessing injury risk: {e}")
            return {"risk_level": "unknown", "probability": 0.5, "error": str(e)}
    
    def identify_breakout_candidates(
        self, 
        players_data: List[Dict[str, Any]], 
        min_probability: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Identify players with high breakout potential
        
        Args:
            players_data: List of player data
            min_probability: Minimum probability threshold
            
        Returns:
            List of breakout candidates with probabilities
        """
        if "breakout_predictor" not in self.models:
            return []
        
        breakout_candidates = []
        
        for player_data in players_data:
            try:
                features = self.prepare_features(player_data, {})
                
                if "breakout_predictor" in self.scalers:
                    features = self.scalers["breakout_predictor"].transform(features)
                
                model = self.models["breakout_predictor"]
                probability = model.predict_proba(features)[0][1]
                
                if probability >= min_probability:
                    breakout_candidates.append({
                        "player_id": player_data.get("player_id"),
                        "player_name": player_data.get("name"),
                        "position": player_data.get("position"),
                        "team": player_data.get("team"),
                        "breakout_probability": round(probability, 3),
                        "key_factors": self._get_breakout_factors(player_data),
                        "confidence": probability
                    })
                    
            except Exception as e:
                logger.error(f"Error evaluating breakout for player {player_data.get('name')}: {e}")
                continue
        
        # Sort by probability
        breakout_candidates.sort(key=lambda x: x["breakout_probability"], reverse=True)
        return breakout_candidates
    
    def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train all ML models on historical data
        
        Args:
            training_data: DataFrame with features and targets
            
        Returns:
            Training results and metrics
        """
        results = {}
        
        for model_name, config in self.model_configs.items():
            try:
                logger.info(f"Training {model_name} model...")
                
                # Prepare data
                X, y = self._prepare_training_data(training_data, config["target"])
                
                if len(X) == 0:
                    logger.warning(f"No training data available for {model_name}")
                    continue
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                model = config["model"]
                model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                if config["type"] == "regression":
                    y_pred = model.predict(X_test_scaled)
                    mae = mean_absolute_error(y_test, y_pred)
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error')
                    
                    metrics = {
                        "mae": mae,
                        "cv_mae": -cv_scores.mean(),
                        "cv_std": cv_scores.std()
                    }
                else:
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                    
                    accuracy = accuracy_score(y_test, y_pred)
                    auc = roc_auc_score(y_test, y_pred_proba)
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
                    
                    metrics = {
                        "accuracy": accuracy,
                        "auc": auc,
                        "cv_accuracy": cv_scores.mean(),
                        "cv_std": cv_scores.std()
                    }
                
                # Store model and scaler
                self.models[model_name] = model
                self.scalers[model_name] = scaler
                self.model_metrics[model_name] = metrics
                
                # Feature importance
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = model.feature_importances_
                
                results[model_name] = {
                    "status": "success",
                    "metrics": metrics,
                    "training_samples": len(X_train),
                    "test_samples": len(X_test)
                }
                
                logger.info(f"{model_name} trained successfully - Metrics: {metrics}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                results[model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def save_models(self, model_path: Optional[str] = None) -> bool:
        """Save trained models to disk"""
        save_path = Path(model_path) if model_path else self.model_path
        save_path.mkdir(exist_ok=True)
        
        try:
            # Save models
            for name, model in self.models.items():
                joblib.dump(model, save_path / f"{name}_model.pkl")
            
            # Save scalers
            for name, scaler in self.scalers.items():
                joblib.dump(scaler, save_path / f"{name}_scaler.pkl")
            
            # Save metadata
            metadata = {
                "model_metrics": self.model_metrics,
                "feature_importance": {k: v.tolist() if hasattr(v, 'tolist') else v 
                                     for k, v in self.feature_importance.items()},
                "last_trained": datetime.now().isoformat()
            }
            
            with open(save_path / "model_metadata.json", "w") as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Models saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def load_models(self, model_path: Optional[str] = None) -> bool:
        """Load trained models from disk"""
        load_path = Path(model_path) if model_path else self.model_path
        
        try:
            # Load models
            for model_name in self.model_configs.keys():
                model_file = load_path / f"{model_name}_model.pkl"
                if model_file.exists():
                    self.models[model_name] = joblib.load(model_file)
                
                scaler_file = load_path / f"{model_name}_scaler.pkl"
                if scaler_file.exists():
                    self.scalers[model_name] = joblib.load(scaler_file)
            
            # Load metadata
            metadata_file = load_path / "model_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    import json
                    metadata = json.load(f)
                    self.model_metrics = metadata.get("model_metrics", {})
                    self.feature_importance = metadata.get("feature_importance", {})
            
            logger.info(f"Models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def _prepare_training_data(self, data: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for training"""
        # Get all feature columns
        all_features = []
        for feature_group in self.feature_definitions.values():
            all_features.extend(feature_group)
        
        # Filter for available features
        available_features = [f for f in all_features if f in data.columns]
        
        if target_col not in data.columns:
            logger.warning(f"Target column {target_col} not found in data")
            return np.array([]), np.array([])
        
        # Remove rows with missing target
        data_clean = data.dropna(subset=[target_col])
        
        # Fill missing features with 0
        X = data_clean[available_features].fillna(0).values
        y = data_clean[target_col].values
        
        return X, y
    
    def _calculate_prediction_confidence(self, prediction: float, player_data: Dict[str, Any], model_name: str) -> float:
        """Calculate confidence in prediction based on various factors"""
        base_confidence = 0.7
        
        # Adjust based on model accuracy
        model_accuracy = self.model_metrics.get(model_name, {}).get("mae", 10)
        if model_accuracy < 5:
            base_confidence += 0.2
        elif model_accuracy > 15:
            base_confidence -= 0.2
        
        # Adjust based on player consistency
        consistency = player_data.get("consistency_score", 0.5)
        base_confidence += (consistency - 0.5) * 0.2
        
        # Adjust based on sample size
        games_played = player_data.get("games_played", 0)
        if games_played < 4:
            base_confidence -= 0.2
        elif games_played > 12:
            base_confidence += 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _get_injury_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on injury risk level"""
        recommendations = {
            "low": "Player appears healthy and safe to start",
            "moderate": "Monitor injury reports, consider having backup options",
            "elevated": "Higher injury risk - consider safer alternatives if available",
            "high": "Significant injury risk - avoid if possible or handcuff with backup"
        }
        return recommendations.get(risk_level, "Monitor injury status")
    
    def _get_top_injury_risk_factors(self, player_data: Dict[str, Any]) -> List[str]:
        """Identify top factors contributing to injury risk"""
        risk_factors = []
        
        if player_data.get("age", 0) > 30:
            risk_factors.append("Advanced age (>30)")
        
        if player_data.get("days_since_injury", 999) < 14:
            risk_factors.append("Recent injury history")
        
        if player_data.get("games_played", 16) < 12:
            risk_factors.append("Missed games this season")
        
        if player_data.get("snap_percentage", 100) > 85:
            risk_factors.append("High snap count/usage")
        
        return risk_factors[:3]  # Return top 3 factors
    
    def _get_breakout_factors(self, player_data: Dict[str, Any]) -> List[str]:
        """Identify factors indicating breakout potential"""
        factors = []
        
        if player_data.get("target_share", 0) > 0.2:
            factors.append("High target share")
        
        if player_data.get("red_zone_touches", 0) > 2:
            factors.append("Red zone opportunity")
        
        if player_data.get("avg_points_last_4", 0) > player_data.get("season_avg_points", 0):
            factors.append("Recent performance uptick")
        
        if player_data.get("age", 30) < 25:
            factors.append("Young with upside")
        
        return factors


# Global ML pipeline instance
ml_pipeline = MLPipeline()