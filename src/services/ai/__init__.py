"""
AI Services for Fantasy Football Assistant

This module contains AI-powered services including:
- Claude API integration for natural language processing
- Machine learning models for player performance prediction
- Automated insights generation
- Sentiment analysis and news processing
"""

from .claude_client import ClaudeAIClient
from .ml_pipeline import MLPipeline
from .insights_engine import InsightsEngine
from .sentiment_analyzer import SentimentAnalyzer
from .recommendation_engine import RecommendationEngine
from .weekly_report_generator import WeeklyReportGenerator
from .analytics_dashboard import AnalyticsDashboard
from .injury_predictor import InjuryPredictor
from .breakout_detector import BreakoutDetector
from .game_script_predictor import GameScriptPredictor
from .expert_simulator import ExpertSimulator

__all__ = [
    "ClaudeAIClient",
    "MLPipeline", 
    "InsightsEngine",
    "SentimentAnalyzer",
    "RecommendationEngine",
    "WeeklyReportGenerator",
    "AnalyticsDashboard",
    "InjuryPredictor",
    "BreakoutDetector",
    "GameScriptPredictor",
    "ExpertSimulator"
]