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

__all__ = [
    "ClaudeAIClient",
    "MLPipeline", 
    "InsightsEngine"
]