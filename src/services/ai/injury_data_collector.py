"""
Injury Training Data Collection and Preparation System

Collects, processes, and prepares training data for injury prediction models from various sources:
- Historical NFL injury reports
- Player performance and usage data
- Game conditions and context
- Recovery time tracking
- Biomechanical indicators
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
import json
import random
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class InjuryRecord:
    """Individual injury record for training data"""
    player_id: int
    player_name: str
    position: str
    age: int
    
    # Injury details
    injury_date: datetime
    injury_type: str
    injury_severity: float  # 0-1 scale
    games_missed: int
    recovery_days: int
    
    # Context at time of injury
    week: int
    season: int
    snap_percentage: float
    usage_rate: float
    touches_per_game: float
    
    # Pre-injury indicators
    workload_trend: str
    recent_performance: float
    fatigue_indicators: List[str]
    
    # Game context
    opponent: str
    weather_conditions: Dict[str, Any]
    playing_surface: str
    game_importance: float


@dataclass
class HealthyPlayerRecord:
    """Record for players who remained healthy (negative examples)"""
    player_id: int
    player_name: str
    position: str
    age: int
    
    # Time period
    week: int
    season: int
    games_played: int
    
    # Performance metrics
    snap_percentage: float
    usage_rate: float
    touches_per_game: float
    
    # Health indicators
    workload_management: float
    recovery_time: float
    injury_prevention_score: float


class InjuryDataCollector:
    """Collects and processes injury training data"""
    
    def __init__(self):
        self.injury_records: List[InjuryRecord] = []
        self.healthy_records: List[HealthyPlayerRecord] = []
        self.data_sources = {
            'nfl_injury_reports': True,
            'player_performance': True,
            'weather_data': True,
            'game_conditions': True
        }
    
    async def collect_historical_injury_data(self, start_season: int = 2018, 
                                           end_season: int = 2023) -> List[InjuryRecord]:
        """Collect historical injury data from multiple seasons"""
        logger.info(f"Collecting injury data from {start_season} to {end_season}")
        
        all_injury_records = []
        
        for season in range(start_season, end_season + 1):
            season_records = await self._collect_season_injuries(season)
            all_injury_records.extend(season_records)
            logger.info(f"Collected {len(season_records)} injury records from {season} season")
        
        self.injury_records = all_injury_records
        logger.info(f"Total injury records collected: {len(all_injury_records)}")
        return all_injury_records
    
    async def collect_healthy_player_data(self, start_season: int = 2018,
                                        end_season: int = 2023) -> List[HealthyPlayerRecord]:
        """Collect data for players who remained healthy (negative examples)"""
        logger.info(f"Collecting healthy player data from {start_season} to {end_season}")
        
        all_healthy_records = []
        
        for season in range(start_season, end_season + 1):
            season_records = await self._collect_season_healthy_players(season)
            all_healthy_records.extend(season_records)
            logger.info(f"Collected {len(season_records)} healthy player records from {season}")
        
        self.healthy_records = all_healthy_records
        logger.info(f"Total healthy player records: {len(all_healthy_records)}")
        return all_healthy_records
    
    async def _collect_season_injuries(self, season: int) -> List[InjuryRecord]:
        """Collect injury data for a specific season"""
        # Mock data generation - in production would integrate with real data sources
        injury_records = []
        
        # Generate realistic injury data for different positions
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        injury_types = ['soft_tissue', 'joint', 'impact', 'overuse', 'contact']
        
        # Different injury rates by position
        position_injury_rates = {
            'QB': 0.15, 'RB': 0.35, 'WR': 0.25, 'TE': 0.28, 'K': 0.05, 'DST': 0.20
        }
        
        for position in positions:
            # Generate players for this position
            players_per_position = {'QB': 50, 'RB': 80, 'WR': 120, 'TE': 60, 'K': 32, 'DST': 32}
            
            for player_id in range(len(injury_records), len(injury_records) + players_per_position[position]):
                injury_rate = position_injury_rates[position]
                
                # Simulate multiple potential injuries per season
                for week in range(1, 18):
                    if random.random() < injury_rate / 17:  # Weekly injury probability
                        injury_record = self._generate_injury_record(
                            player_id, position, week, season
                        )
                        injury_records.append(injury_record)
        
        return injury_records
    
    async def _collect_season_healthy_players(self, season: int) -> List[HealthyPlayerRecord]:
        """Collect healthy player data for a specific season"""
        healthy_records = []
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        
        for position in positions:
            players_per_position = {'QB': 50, 'RB': 80, 'WR': 120, 'TE': 60, 'K': 32, 'DST': 32}
            
            for player_id in range(1000 + len(healthy_records), 
                                 1000 + len(healthy_records) + players_per_position[position]):
                
                # Generate healthy weeks for each player
                for week in range(1, 18):
                    if random.random() < 0.8:  # 80% chance of being healthy each week
                        healthy_record = self._generate_healthy_record(
                            player_id, position, week, season
                        )
                        healthy_records.append(healthy_record)
        
        return healthy_records
    
    def _generate_injury_record(self, player_id: int, position: str, 
                               week: int, season: int) -> InjuryRecord:
        """Generate realistic injury record"""
        injury_types = ['soft_tissue', 'joint', 'impact', 'overuse', 'contact']
        
        # Position-specific injury likelihood
        position_injury_weights = {
            'QB': {'soft_tissue': 0.1, 'joint': 0.3, 'impact': 0.4, 'overuse': 0.1, 'contact': 0.1},
            'RB': {'soft_tissue': 0.3, 'joint': 0.2, 'impact': 0.2, 'overuse': 0.1, 'contact': 0.2},
            'WR': {'soft_tissue': 0.4, 'joint': 0.2, 'impact': 0.15, 'overuse': 0.15, 'contact': 0.1},
            'TE': {'soft_tissue': 0.2, 'joint': 0.25, 'impact': 0.2, 'overuse': 0.15, 'contact': 0.2},
            'K': {'soft_tissue': 0.3, 'joint': 0.3, 'impact': 0.1, 'overuse': 0.25, 'contact': 0.05},
            'DST': {'soft_tissue': 0.2, 'joint': 0.2, 'impact': 0.3, 'overuse': 0.1, 'contact': 0.2}
        }
        
        # Select injury type based on position
        weights = position_injury_weights.get(position, position_injury_weights['RB'])
        injury_type = random.choices(injury_types, weights=list(weights.values()))[0]
        
        # Injury severity and recovery time
        severity_ranges = {
            'soft_tissue': (0.3, 0.7), 'joint': (0.5, 0.9), 'impact': (0.2, 0.8),
            'overuse': (0.4, 0.6), 'contact': (0.3, 0.9)
        }
        severity = random.uniform(*severity_ranges[injury_type])
        
        # Games missed based on severity
        base_games_missed = {'soft_tissue': 2, 'joint': 4, 'impact': 1, 'overuse': 3, 'contact': 3}
        games_missed = max(1, int(base_games_missed[injury_type] * severity + random.uniform(-1, 2)))
        recovery_days = games_missed * 7 + random.randint(-3, 10)
        
        # Player characteristics
        age = random.randint(22, 35)
        
        # Usage patterns (higher usage often correlates with injury)
        base_snap_pct = {'QB': 0.95, 'RB': 0.6, 'WR': 0.7, 'TE': 0.65, 'K': 1.0, 'DST': 1.0}
        snap_percentage = max(0.1, min(1.0, base_snap_pct[position] + random.uniform(-0.2, 0.1)))
        
        usage_rate = random.uniform(0.15, 0.35) if position in ['RB', 'WR', 'TE'] else 0.0
        touches_per_game = usage_rate * 25 if position in ['RB', 'WR', 'TE'] else 0.0
        
        # Pre-injury indicators
        workload_trends = ['increasing', 'stable', 'decreasing']
        workload_trend = random.choices(workload_trends, weights=[0.4, 0.4, 0.2])[0]
        
        recent_performance = random.uniform(0.7, 1.1)  # Performance relative to season average
        
        fatigue_indicators = []
        if snap_percentage > 0.8:
            fatigue_indicators.append("high_snap_count")
        if workload_trend == "increasing":
            fatigue_indicators.append("increasing_workload")
        if week > 12:
            fatigue_indicators.append("late_season_fatigue")
        
        # Game context
        opponents = [f"Team_{i}" for i in range(1, 33)]
        opponent = random.choice(opponents)
        
        # Weather conditions
        weather_conditions = {
            'temperature': random.randint(20, 85),
            'wind_speed': random.randint(0, 25),
            'precipitation': random.choice([0, 0, 0, 0.1, 0.3, 0.8]),  # Most games are dry
            'field_condition': random.choice(['excellent', 'good', 'fair', 'poor'])
        }
        
        playing_surface = random.choice(['grass', 'artificial_turf'])
        game_importance = random.uniform(3.0, 9.0)  # Playoff games have higher importance
        
        return InjuryRecord(
            player_id=player_id,
            player_name=f"{position}_Player_{player_id}",
            position=position,
            age=age,
            injury_date=datetime(season, 9, 1) + timedelta(weeks=week-1),
            injury_type=injury_type,
            injury_severity=severity,
            games_missed=games_missed,
            recovery_days=recovery_days,
            week=week,
            season=season,
            snap_percentage=snap_percentage,
            usage_rate=usage_rate,
            touches_per_game=touches_per_game,
            workload_trend=workload_trend,
            recent_performance=recent_performance,
            fatigue_indicators=fatigue_indicators,
            opponent=opponent,
            weather_conditions=weather_conditions,
            playing_surface=playing_surface,
            game_importance=game_importance
        )
    
    def _generate_healthy_record(self, player_id: int, position: str,
                                week: int, season: int) -> HealthyPlayerRecord:
        """Generate healthy player record (negative example)"""
        age = random.randint(22, 35)
        
        # Healthy players often have more managed workloads
        base_snap_pct = {'QB': 0.85, 'RB': 0.55, 'WR': 0.65, 'TE': 0.6, 'K': 1.0, 'DST': 1.0}
        snap_percentage = max(0.1, min(1.0, base_snap_pct[position] + random.uniform(-0.15, 0.1)))
        
        # More conservative usage for healthy players
        usage_rate = random.uniform(0.1, 0.25) if position in ['RB', 'WR', 'TE'] else 0.0
        touches_per_game = usage_rate * 20 if position in ['RB', 'WR', 'TE'] else 0.0
        
        # Better workload management
        workload_management = random.uniform(0.6, 1.0)
        recovery_time = random.uniform(0.7, 1.0)
        injury_prevention_score = random.uniform(0.6, 1.0)
        
        return HealthyPlayerRecord(
            player_id=player_id,
            player_name=f"Healthy_{position}_Player_{player_id}",
            position=position,
            age=age,
            week=week,
            season=season,
            games_played=1,  # This week they played
            snap_percentage=snap_percentage,
            usage_rate=usage_rate,
            touches_per_game=touches_per_game,
            workload_management=workload_management,
            recovery_time=recovery_time,
            injury_prevention_score=injury_prevention_score
        )


class InjuryDataProcessor:
    """Processes raw injury data into ML-ready training sets"""
    
    def __init__(self):
        self.feature_columns = [
            # Player demographics
            'age', 'position_encoded', 'years_experience',
            
            # Usage patterns
            'snap_percentage', 'usage_rate', 'touches_per_game',
            'workload_trend_encoded', 'games_played_streak',
            
            # Performance indicators
            'recent_performance', 'performance_trend',
            'efficiency_metrics', 'fatigue_score',
            
            # Historical factors
            'previous_injuries', 'recovery_history_score',
            'injury_proneness', 'position_injury_rate',
            
            # Game context
            'week', 'season_progress', 'game_importance',
            'opponent_strength', 'weather_risk_score',
            'surface_risk', 'travel_fatigue',
            
            # Team factors
            'team_medical_rating', 'coaching_stability',
            'team_injury_rate', 'workload_management_score'
        ]
    
    def prepare_training_data(self, injury_records: List[InjuryRecord],
                            healthy_records: List[HealthyPlayerRecord]) -> pd.DataFrame:
        """Prepare comprehensive training dataset"""
        logger.info("Preparing training data from injury and healthy records")
        
        # Convert injury records to training examples
        injury_examples = []
        for record in injury_records:
            example = self._injury_record_to_features(record)
            example['injury_occurred'] = 1
            example['injury_type_' + record.injury_type] = 1
            example['injury_severity'] = record.injury_severity
            injury_examples.append(example)
        
        # Convert healthy records to training examples
        healthy_examples = []
        for record in healthy_records:
            example = self._healthy_record_to_features(record)
            example['injury_occurred'] = 0
            # Set all injury types to 0
            for injury_type in ['soft_tissue', 'joint', 'impact', 'overuse', 'contact']:
                example[f'injury_type_{injury_type}'] = 0
            example['injury_severity'] = 0.0
            healthy_examples.append(example)
        
        # Combine datasets
        all_examples = injury_examples + healthy_examples
        
        # Create DataFrame
        df = pd.DataFrame(all_examples)
        
        # Fill missing values
        df = self._fill_missing_values(df)
        
        # Add derived features
        df = self._add_derived_features(df)
        
        logger.info(f"Training dataset created: {len(df)} examples, {len(df.columns)} features")
        logger.info(f"Injury rate: {df['injury_occurred'].mean():.3f}")
        
        return df
    
    def _injury_record_to_features(self, record: InjuryRecord) -> Dict[str, Any]:
        """Convert injury record to feature dictionary"""
        features = {
            # Player demographics
            'player_id': record.player_id,
            'age': record.age,
            'position': record.position,
            'position_encoded': self._encode_position(record.position),
            'years_experience': max(1, record.age - 22),  # Rough estimate
            
            # Usage patterns
            'snap_percentage': record.snap_percentage,
            'usage_rate': record.usage_rate,
            'touches_per_game': record.touches_per_game,
            'workload_trend_encoded': self._encode_workload_trend(record.workload_trend),
            'games_played_streak': random.randint(1, record.week),
            
            # Performance indicators
            'recent_performance': record.recent_performance,
            'performance_trend': random.uniform(-0.2, 0.2),
            'efficiency_metrics': random.uniform(0.7, 1.2),
            'fatigue_score': len(record.fatigue_indicators) / 3.0,
            
            # Historical factors
            'previous_injuries': random.randint(0, 3),
            'recovery_history_score': random.uniform(0.5, 1.0),
            'injury_proneness': random.uniform(0.0, 1.0),
            'position_injury_rate': self._get_position_injury_rate(record.position),
            
            # Game context
            'week': record.week,
            'season_progress': record.week / 17.0,
            'game_importance': record.game_importance,
            'opponent_strength': random.uniform(0.3, 0.9),
            'weather_risk_score': self._calculate_weather_risk(record.weather_conditions),
            'surface_risk': 1.0 if record.playing_surface == 'artificial_turf' else 0.0,
            'travel_fatigue': random.uniform(0.0, 0.5),
            
            # Team factors
            'team_medical_rating': random.uniform(0.6, 0.95),
            'coaching_stability': random.uniform(0.5, 1.0),
            'team_injury_rate': random.uniform(0.1, 0.3),
            'workload_management_score': random.uniform(0.4, 0.9)
        }
        
        return features
    
    def _healthy_record_to_features(self, record: HealthyPlayerRecord) -> Dict[str, Any]:
        """Convert healthy record to feature dictionary"""
        features = {
            # Player demographics
            'player_id': record.player_id,
            'age': record.age,
            'position': record.position,
            'position_encoded': self._encode_position(record.position),
            'years_experience': max(1, record.age - 22),
            
            # Usage patterns
            'snap_percentage': record.snap_percentage,
            'usage_rate': record.usage_rate,
            'touches_per_game': record.touches_per_game,
            'workload_trend_encoded': random.uniform(-0.5, 0.5),  # Neutral trend
            'games_played_streak': random.randint(record.week, 17),
            
            # Performance indicators
            'recent_performance': random.uniform(0.9, 1.1),  # Stable performance
            'performance_trend': random.uniform(-0.1, 0.1),
            'efficiency_metrics': random.uniform(0.8, 1.1),
            'fatigue_score': random.uniform(0.0, 0.3),  # Low fatigue for healthy players
            
            # Historical factors
            'previous_injuries': random.randint(0, 1),  # Fewer previous injuries
            'recovery_history_score': record.recovery_time,
            'injury_proneness': random.uniform(0.0, 0.4),  # Lower injury proneness
            'position_injury_rate': self._get_position_injury_rate(record.position),
            
            # Game context
            'week': record.week,
            'season_progress': record.week / 17.0,
            'game_importance': random.uniform(3.0, 7.0),
            'opponent_strength': random.uniform(0.3, 0.9),
            'weather_risk_score': random.uniform(0.0, 0.3),  # Better weather for healthy games
            'surface_risk': random.uniform(0.0, 0.5),
            'travel_fatigue': random.uniform(0.0, 0.3),
            
            # Team factors
            'team_medical_rating': random.uniform(0.7, 1.0),  # Better medical support
            'coaching_stability': random.uniform(0.6, 1.0),
            'team_injury_rate': random.uniform(0.05, 0.2),  # Lower team injury rate
            'workload_management_score': record.workload_management
        }
        
        return features
    
    def _encode_position(self, position: str) -> float:
        """Encode position with injury risk weighting"""
        position_encoding = {
            'QB': 0.2, 'RB': 0.9, 'WR': 0.6, 'TE': 0.7, 'K': 0.1, 'DST': 0.5
        }
        return position_encoding.get(position, 0.5)
    
    def _encode_workload_trend(self, trend: str) -> float:
        """Encode workload trend"""
        encoding = {'increasing': 1.0, 'stable': 0.0, 'decreasing': -1.0}
        return encoding.get(trend, 0.0)
    
    def _get_position_injury_rate(self, position: str) -> float:
        """Get historical injury rate for position"""
        rates = {'QB': 0.15, 'RB': 0.35, 'WR': 0.25, 'TE': 0.28, 'K': 0.05, 'DST': 0.20}
        return rates.get(position, 0.25)
    
    def _calculate_weather_risk(self, conditions: Dict[str, Any]) -> float:
        """Calculate weather-based injury risk"""
        risk = 0.0
        
        # Temperature extremes
        temp = conditions.get('temperature', 70)
        if temp < 32 or temp > 90:
            risk += 0.3
        
        # High winds
        wind = conditions.get('wind_speed', 0)
        if wind > 15:
            risk += 0.2
        
        # Precipitation
        precip = conditions.get('precipitation', 0)
        risk += min(precip, 0.4)
        
        # Poor field conditions
        field_condition = conditions.get('field_condition', 'good')
        if field_condition in ['fair', 'poor']:
            risk += 0.3
        
        return min(risk, 1.0)
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values in dataset"""
        # Fill numeric columns with median
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = df[col].fillna(df[col].median())
        
        # Fill categorical columns with mode
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else 'unknown')
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to improve model performance"""
        # Age groups
        df['age_group'] = pd.cut(df['age'], bins=[0, 25, 28, 31, 40], labels=['young', 'prime', 'veteran', 'old'])
        df['age_group'] = df['age_group'].cat.codes
        
        # Usage intensity
        df['usage_intensity'] = df['snap_percentage'] * df['usage_rate']
        
        # Fatigue risk
        df['fatigue_risk'] = (df['fatigue_score'] * df['games_played_streak'] / 17.0)
        
        # Position-adjusted usage
        df['position_adjusted_usage'] = df['usage_rate'] / df['position_injury_rate']
        
        # Week-based fatigue
        df['late_season_factor'] = np.where(df['week'] > 12, (df['week'] - 12) / 5.0, 0.0)
        
        # Injury risk composite
        df['composite_risk'] = (
            df['age'] / 35.0 * 0.2 +
            df['usage_intensity'] * 0.3 +
            df['fatigue_risk'] * 0.2 +
            df['injury_proneness'] * 0.3
        )
        
        return df
    
    def save_training_data(self, df: pd.DataFrame, filepath: str):
        """Save processed training data"""
        df.to_csv(filepath, index=False)
        logger.info(f"Training data saved to {filepath}")
    
    def load_training_data(self, filepath: str) -> pd.DataFrame:
        """Load processed training data"""
        df = pd.read_csv(filepath)
        logger.info(f"Training data loaded from {filepath}: {len(df)} samples")
        return df


# Training data collection and processing functions
async def collect_and_prepare_injury_training_data(start_season: int = 2018,
                                                  end_season: int = 2023,
                                                  save_path: str = "data/injury_training_data.csv") -> pd.DataFrame:
    """Complete pipeline to collect and prepare injury training data"""
    logger.info("Starting injury training data collection and preparation")
    
    # Initialize collectors
    collector = InjuryDataCollector()
    processor = InjuryDataProcessor()
    
    # Collect raw data
    injury_records = await collector.collect_historical_injury_data(start_season, end_season)
    healthy_records = await collector.collect_healthy_player_data(start_season, end_season)
    
    # Process into training dataset
    training_df = processor.prepare_training_data(injury_records, healthy_records)
    
    # Save processed data
    processor.save_training_data(training_df, save_path)
    
    logger.info("Injury training data collection and preparation complete")
    return training_df


# Global instances
injury_data_collector = InjuryDataCollector()
injury_data_processor = InjuryDataProcessor()