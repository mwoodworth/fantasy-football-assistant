"""
Training Script for Injury Prediction Models

Trains and validates injury prediction models using collected historical data.
Includes model evaluation, hyperparameter tuning, and performance metrics.
"""

import asyncio
import os
import logging
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    precision_recall_curve, mean_squared_error, mean_absolute_error
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from .injury_data_collector import collect_and_prepare_injury_training_data, InjuryType
from .injury_predictor import InjuryPredictionModel

logger = logging.getLogger(__name__)


class InjuryModelTrainer:
    """Complete training pipeline for injury prediction models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.performance_metrics = {}
        
        # Ensure models directory exists
        os.makedirs('models', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
    
    async def train_all_models(self, retrain: bool = False) -> Dict[str, Any]:
        """Train all injury prediction models"""
        logger.info("Starting comprehensive injury model training")
        
        # Collect and prepare training data
        training_data = await self._prepare_training_data(retrain)
        
        # Split data
        X_train, X_test, y_train, y_test = self._split_data(training_data)
        
        # Train models
        results = {}
        
        # 1. Overall injury risk model
        logger.info("Training overall injury risk model")
        overall_results = await self._train_overall_risk_model(X_train, X_test, y_train, y_test)
        results['overall_risk'] = overall_results
        
        # 2. Injury type models
        logger.info("Training injury type models")
        type_results = await self._train_injury_type_models(training_data, X_train, X_test)
        results['injury_types'] = type_results
        
        # 3. Severity prediction model
        logger.info("Training injury severity model")
        severity_results = await self._train_severity_model(training_data, X_train, X_test)
        results['severity'] = severity_results
        
        # Generate comprehensive report
        self._generate_training_report(results)
        
        logger.info("All injury models trained successfully")
        return results
    
    async def _prepare_training_data(self, retrain: bool = False) -> pd.DataFrame:
        """Prepare training data for model training"""
        data_path = "data/injury_training_data.csv"
        
        if retrain or not os.path.exists(data_path):
            logger.info("Collecting new training data")
            training_data = await collect_and_prepare_injury_training_data()
        else:
            logger.info("Loading existing training data")
            training_data = pd.read_csv(data_path)
        
        logger.info(f"Training data shape: {training_data.shape}")
        logger.info(f"Injury rate: {training_data['injury_occurred'].mean():.3f}")
        
        return training_data
    
    def _split_data(self, training_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split data into training and testing sets"""
        # Define feature columns (exclude target variables)
        feature_columns = [col for col in training_data.columns 
                          if not col.startswith('injury_') and col not in ['player_id', 'position']]
        
        X = training_data[feature_columns]
        y = training_data['injury_occurred']
        
        # Stratified split to maintain injury rate
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Training injury rate: {y_train.mean():.3f}")
        logger.info(f"Test injury rate: {y_test.mean():.3f}")
        
        return X_train, X_test, y_train, y_test
    
    async def _train_overall_risk_model(self, X_train: pd.DataFrame, X_test: pd.DataFrame,
                                       y_train: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
        """Train the overall injury risk model"""
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Hyperparameter tuning for RandomForest
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [5, 10, 15],
            'min_samples_leaf': [2, 5, 10],
            'class_weight': ['balanced', 'balanced_subsample']
        }
        
        # Grid search with cross-validation
        rf = RandomForestClassifier(random_state=42)
        grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='roc_auc', n_jobs=-1)
        grid_search.fit(X_train_scaled, y_train)
        
        # Best model
        best_model = grid_search.best_estimator_
        
        # Predictions
        y_pred = best_model.predict(X_test_scaled)
        y_pred_proba = best_model.predict_proba(X_test_scaled)[:, 1]
        
        # Evaluation metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Cross-validation scores
        cv_scores = cross_val_score(best_model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
        
        # Feature importance
        feature_importance = dict(zip(X_train.columns, best_model.feature_importances_))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Save model and scaler
        joblib.dump(best_model, 'models/injury_overall_risk.pkl')
        joblib.dump(scaler, 'models/injury_scaler.pkl')
        
        results = {
            'model': best_model,
            'scaler': scaler,
            'best_params': grid_search.best_params_,
            'auc_score': auc_score,
            'cv_scores': cv_scores,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': feature_importance,
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
        
        logger.info(f"Overall risk model - AUC: {auc_score:.3f}, CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return results
    
    async def _train_injury_type_models(self, training_data: pd.DataFrame,
                                       X_train: pd.DataFrame, X_test: pd.DataFrame) -> Dict[str, Any]:
        """Train models for specific injury types"""
        type_results = {}
        
        # Feature columns
        feature_columns = [col for col in training_data.columns 
                          if not col.startswith('injury_') and col not in ['player_id', 'position']]
        
        for injury_type in InjuryType:
            type_column = f'injury_type_{injury_type.value}'
            
            if type_column in training_data.columns:
                logger.info(f"Training model for {injury_type.value}")
                
                # Get injury type data
                y_type = training_data[type_column]
                y_type_train = y_type[X_train.index]
                y_type_test = y_type[X_test.index]
                
                # Skip if insufficient positive examples
                if y_type_train.sum() < 10:
                    logger.warning(f"Insufficient data for {injury_type.value} ({y_type_train.sum()} cases)")
                    continue
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train logistic regression model
                model = LogisticRegression(
                    random_state=42,
                    class_weight='balanced',
                    max_iter=1000
                )
                model.fit(X_train_scaled, y_type_train)
                
                # Predictions
                y_pred = model.predict(X_test_scaled)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
                
                # Evaluation
                auc_score = roc_auc_score(y_type_test, y_pred_proba) if y_type_test.sum() > 0 else 0.0
                
                # Save model
                joblib.dump(model, f'models/injury_{injury_type.value}.pkl')
                
                type_results[injury_type.value] = {
                    'model': model,
                    'scaler': scaler,
                    'auc_score': auc_score,
                    'positive_cases': int(y_type_train.sum()),
                    'classification_report': classification_report(y_type_test, y_pred, output_dict=True, zero_division=0)
                }
                
                logger.info(f"{injury_type.value} model - AUC: {auc_score:.3f}, Cases: {y_type_train.sum()}")
        
        return type_results
    
    async def _train_severity_model(self, training_data: pd.DataFrame,
                                   X_train: pd.DataFrame, X_test: pd.DataFrame) -> Dict[str, Any]:
        """Train injury severity prediction model"""
        # Only train on injured players
        injured_mask = training_data['injury_occurred'] == 1
        injured_data = training_data[injured_mask]
        
        if len(injured_data) < 50:
            logger.warning("Insufficient injury data for severity model")
            return {}
        
        # Features and target
        feature_columns = [col for col in training_data.columns 
                          if not col.startswith('injury_') and col not in ['player_id', 'position']]
        
        X_injured = injured_data[feature_columns]
        y_severity = injured_data['injury_severity']
        
        # Split injured data
        X_sev_train, X_sev_test, y_sev_train, y_sev_test = train_test_split(
            X_injured, y_severity, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_sev_train_scaled = scaler.fit_transform(X_sev_train)
        X_sev_test_scaled = scaler.transform(X_sev_test)
        
        # Train gradient boosting regressor
        model = GradientBoostingRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_sev_train_scaled, y_sev_train)
        
        # Predictions
        y_pred = model.predict(X_sev_test_scaled)
        
        # Evaluation
        mse = mean_squared_error(y_sev_test, y_pred)
        mae = mean_absolute_error(y_sev_test, y_pred)
        r2_score = model.score(X_sev_test_scaled, y_sev_test)
        
        # Save model
        joblib.dump(model, 'models/injury_severity.pkl')
        
        results = {
            'model': model,
            'scaler': scaler,
            'mse': mse,
            'mae': mae,
            'r2_score': r2_score,
            'training_samples': len(X_sev_train)
        }
        
        logger.info(f"Severity model - MAE: {mae:.3f}, R²: {r2_score:.3f}")
        
        return results
    
    def _generate_training_report(self, results: Dict[str, Any]):
        """Generate comprehensive training report"""
        report_path = f"reports/injury_model_training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write("INJURY PREDICTION MODEL TRAINING REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall Risk Model
            if 'overall_risk' in results:
                overall = results['overall_risk']
                f.write("OVERALL INJURY RISK MODEL\n")
                f.write("-" * 30 + "\n")
                f.write(f"AUC Score: {overall['auc_score']:.3f}\n")
                f.write(f"Cross-validation: {overall['cv_mean']:.3f} ± {overall['cv_std']:.3f}\n")
                f.write(f"Best Parameters: {overall['best_params']}\n\n")
                
                f.write("Top 10 Feature Importance:\n")
                for i, (feature, importance) in enumerate(list(overall['feature_importance'].items())[:10]):
                    f.write(f"{i+1:2d}. {feature:<30} {importance:.4f}\n")
                f.write("\n")
            
            # Injury Type Models
            if 'injury_types' in results:
                f.write("INJURY TYPE MODELS\n")
                f.write("-" * 20 + "\n")
                for injury_type, type_results in results['injury_types'].items():
                    f.write(f"{injury_type.upper():<15} AUC: {type_results['auc_score']:.3f}, "
                           f"Cases: {type_results['positive_cases']}\n")
                f.write("\n")
            
            # Severity Model
            if 'severity' in results:
                severity = results['severity']
                f.write("INJURY SEVERITY MODEL\n")
                f.write("-" * 25 + "\n")
                f.write(f"Mean Absolute Error: {severity['mae']:.3f}\n")
                f.write(f"R² Score: {severity['r2_score']:.3f}\n")
                f.write(f"Training Samples: {severity['training_samples']}\n\n")
        
        logger.info(f"Training report saved to {report_path}")
    
    def evaluate_model_performance(self, test_data_path: str = None) -> Dict[str, Any]:
        """Evaluate trained models on test data"""
        logger.info("Evaluating model performance")
        
        # Load test data
        if test_data_path:
            test_data = pd.read_csv(test_data_path)
        else:
            # Use a portion of training data as test
            test_data = pd.read_csv("data/injury_training_data.csv").sample(n=1000, random_state=42)
        
        # Load trained models
        try:
            overall_model = joblib.load('models/injury_overall_risk.pkl')
            scaler = joblib.load('models/injury_scaler.pkl')
        except FileNotFoundError:
            logger.error("Trained models not found. Please train models first.")
            return {}
        
        # Prepare test features
        feature_columns = [col for col in test_data.columns 
                          if not col.startswith('injury_') and col not in ['player_id', 'position']]
        X_test = test_data[feature_columns]
        y_test = test_data['injury_occurred']
        
        # Scale features
        X_test_scaled = scaler.transform(X_test)
        
        # Predictions
        y_pred_proba = overall_model.predict_proba(X_test_scaled)[:, 1]
        y_pred = overall_model.predict(X_test_scaled)
        
        # Metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Risk level distribution
        risk_levels = pd.cut(y_pred_proba, bins=[0, 0.1, 0.2, 0.35, 0.5, 0.7, 1.0],
                            labels=['very_low', 'low', 'moderate', 'elevated', 'high', 'critical'])
        risk_distribution = risk_levels.value_counts().to_dict()
        
        # Calibration analysis
        calibration_data = []
        for threshold in np.arange(0.1, 1.0, 0.1):
            predicted_positive = y_pred_proba >= threshold
            if predicted_positive.sum() > 0:
                actual_rate = y_test[predicted_positive].mean()
                calibration_data.append({
                    'threshold': threshold,
                    'predicted_rate': threshold,
                    'actual_rate': actual_rate,
                    'samples': predicted_positive.sum()
                })
        
        results = {
            'auc_score': auc_score,
            'accuracy': (y_pred == y_test).mean(),
            'total_samples': len(test_data),
            'injury_rate': y_test.mean(),
            'risk_distribution': risk_distribution,
            'calibration': calibration_data
        }
        
        logger.info(f"Model evaluation complete - AUC: {auc_score:.3f}")
        return results


async def main():
    """Main training function"""
    trainer = InjuryModelTrainer()
    
    # Train all models
    results = await trainer.train_all_models(retrain=True)
    
    # Evaluate performance
    evaluation = trainer.evaluate_model_performance()
    
    print("Training completed successfully!")
    print(f"Overall AUC: {results.get('overall_risk', {}).get('auc_score', 'N/A')}")
    print(f"Models saved to: models/")
    print(f"Report saved to: reports/")


if __name__ == "__main__":
    asyncio.run(main())