"""
Sentiment Analysis Service for Fantasy Football News

Analyzes player news sentiment and impact assessment for fantasy football decisions.
Provides news aggregation, sentiment scoring, and fantasy relevance evaluation.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SentimentScore(Enum):
    """Sentiment classification for news articles"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive" 
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class FantasyImpact(Enum):
    """Fantasy football impact classification"""
    MAJOR_POSITIVE = "major_positive"
    MINOR_POSITIVE = "minor_positive"
    NEUTRAL = "neutral"
    MINOR_NEGATIVE = "minor_negative"
    MAJOR_NEGATIVE = "major_negative"


@dataclass
class NewsArticle:
    """Represents a news article about a player"""
    title: str
    content: str
    source: str
    published_at: datetime
    player_id: Optional[int] = None
    player_name: Optional[str] = None
    url: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentScore] = None
    fantasy_impact: Optional[FantasyImpact] = None
    impact_score: Optional[float] = None
    keywords: List[str] = None


@dataclass
class SentimentAnalysis:
    """Complete sentiment analysis result for a player"""
    player_id: int
    player_name: str
    overall_sentiment: SentimentScore
    sentiment_score: float  # -1.0 to 1.0
    fantasy_impact: FantasyImpact
    impact_score: float  # -1.0 to 1.0
    news_articles: List[NewsArticle]
    key_themes: List[str]
    recommendation: str
    confidence: float
    last_updated: datetime


class SentimentAnalyzer:
    """Advanced sentiment analysis for fantasy football news"""
    
    def __init__(self):
        """Initialize sentiment analyzer with fantasy football context"""
        self.fantasy_keywords = self._get_fantasy_keywords()
        self.sentiment_patterns = self._get_sentiment_patterns()
        self.impact_weights = self._get_impact_weights()
        
        # Cache for recent analyses
        self.sentiment_cache: Dict[int, SentimentAnalysis] = {}
        self.cache_duration = timedelta(hours=1)
    
    def _get_fantasy_keywords(self) -> Dict[str, Dict[str, float]]:
        """Define fantasy football relevant keywords with impact weights"""
        return {
            "positive": {
                # Performance indicators
                "touchdown": 0.8, "td": 0.8, "score": 0.6, "yards": 0.5,
                "targets": 0.7, "carries": 0.6, "snaps": 0.6, "usage": 0.7,
                "breakout": 0.9, "trending up": 0.8, "hot streak": 0.7,
                "confident": 0.6, "ready": 0.5, "healthy": 0.8,
                
                # Role/opportunity
                "starter": 0.8, "lead back": 0.9, "feature": 0.8, "workhorse": 0.9,
                "red zone": 0.8, "goal line": 0.8, "primary": 0.7,
                "promoted": 0.7, "elevated": 0.6, "expanded role": 0.8,
                
                # Team context
                "high-powered": 0.6, "explosive": 0.6, "prolific": 0.6,
                "favorable": 0.5, "plus matchup": 0.7, "soft defense": 0.6,
                
                # General positive
                "excellent": 0.7, "outstanding": 0.8, "impressive": 0.6,
                "strong": 0.5, "solid": 0.4, "reliable": 0.5
            },
            "negative": {
                # Injuries
                "injured": 0.9, "hurt": 0.8, "questionable": 0.6, "doubtful": 0.8,
                "out": 0.9, "ruled out": 0.9, "sidelined": 0.8, "benched": 0.8,
                "concussion": 0.9, "ankle": 0.7, "hamstring": 0.8, "knee": 0.8,
                "shoulder": 0.7, "back": 0.8, "surgery": 0.9,
                
                # Performance issues
                "struggling": 0.7, "slump": 0.7, "disappointing": 0.6,
                "ineffective": 0.7, "limited": 0.6, "reduced": 0.6,
                "dropped": 0.7, "fumble": 0.6, "turnover": 0.6,
                
                # Role reduction
                "backup": 0.7, "split": 0.5, "committee": 0.6, "rotation": 0.5,
                "demoted": 0.8, "lost job": 0.9, "replaced": 0.8,
                
                # Team context
                "tough matchup": 0.6, "elite defense": 0.7, "shutdown": 0.7,
                "low-scoring": 0.5, "conservative": 0.4,
                
                # General negative
                "terrible": 0.8, "awful": 0.8, "poor": 0.6, "weak": 0.5,
                "concerning": 0.6, "worrying": 0.7
            },
            "neutral": {
                "practice": 0.2, "meeting": 0.1, "interview": 0.2,
                "press conference": 0.1, "media": 0.1, "available": 0.3,
                "listed": 0.2, "probable": 0.3, "expected": 0.2
            }
        }
    
    def _get_sentiment_patterns(self) -> Dict[str, List[str]]:
        """Define regex patterns for sentiment analysis"""
        return {
            "injury_severity": [
                r"placed on (?:IR|injured reserve)",
                r"out (?:for|multiple) weeks?",
                r"season-ending",
                r"surgery",
                r"torn (?:ACL|MCL|achilles)",
                r"broken (?:bone|rib|finger)"
            ],
            "opportunity_increase": [
                r"named (?:starter|lead back)",
                r"promoted to (?:starter|first team)",
                r"expanded role",
                r"increased (?:snaps|targets|carries)",
                r"feature back",
                r"workhorse role"
            ],
            "performance_trends": [
                r"(?:three|3|four|4|five|5) straight games with",
                r"trending (?:up|upward)",
                r"hot streak",
                r"breakout (?:game|performance)",
                r"career-high",
                r"season-high"
            ]
        }
    
    def _get_impact_weights(self) -> Dict[str, float]:
        """Define impact weights for different news categories"""
        return {
            "injury": 1.0,
            "role_change": 0.9,
            "performance": 0.7,
            "matchup": 0.6,
            "team_news": 0.5,
            "personal": 0.3
        }
    
    async def analyze_player_sentiment(
        self, 
        player_id: int, 
        player_name: str,
        time_range_hours: int = 48
    ) -> SentimentAnalysis:
        """
        Analyze sentiment for a specific player from recent news
        
        Args:
            player_id: Player ID to analyze
            player_name: Player name for news search
            time_range_hours: Hours to look back for news
            
        Returns:
            Complete sentiment analysis
        """
        # Check cache first
        if player_id in self.sentiment_cache:
            cached = self.sentiment_cache[player_id]
            if datetime.now() - cached.last_updated < self.cache_duration:
                logger.info(f"Returning cached sentiment analysis for player {player_id}")
                return cached
        
        try:
            logger.info(f"Analyzing sentiment for player {player_name} ({player_id})")
            
            # Get recent news articles
            articles = await self._fetch_player_news(player_name, time_range_hours)
            
            if not articles:
                logger.warning(f"No news found for player {player_name}")
                return self._create_neutral_analysis(player_id, player_name)
            
            # Analyze each article
            analyzed_articles = []
            for article in articles:
                analyzed_article = await self._analyze_article_sentiment(article)
                analyzed_articles.append(analyzed_article)
            
            # Aggregate sentiment scores
            overall_sentiment, sentiment_score = self._calculate_overall_sentiment(analyzed_articles)
            fantasy_impact, impact_score = self._calculate_fantasy_impact(analyzed_articles)
            
            # Extract key themes
            key_themes = self._extract_key_themes(analyzed_articles)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                overall_sentiment, fantasy_impact, key_themes
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(analyzed_articles)
            
            # Create analysis result
            analysis = SentimentAnalysis(
                player_id=player_id,
                player_name=player_name,
                overall_sentiment=overall_sentiment,
                sentiment_score=sentiment_score,
                fantasy_impact=fantasy_impact,
                impact_score=impact_score,
                news_articles=analyzed_articles,
                key_themes=key_themes,
                recommendation=recommendation,
                confidence=confidence,
                last_updated=datetime.now()
            )
            
            # Cache the result
            self.sentiment_cache[player_id] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for player {player_id}: {e}")
            return self._create_neutral_analysis(player_id, player_name, error=str(e))
    
    async def _fetch_player_news(self, player_name: str, hours: int) -> List[NewsArticle]:
        """Fetch recent news articles for a player"""
        # Mock news data for demonstration - in production, integrate with news APIs
        mock_articles = [
            NewsArticle(
                title=f"{player_name} listed as questionable with ankle injury",
                content=f"The team has listed {player_name} as questionable for Sunday's game due to an ankle injury sustained in practice. Coach says he's day-to-day.",
                source="ESPN",
                published_at=datetime.now() - timedelta(hours=2)
            ),
            NewsArticle(
                title=f"{player_name} expected to play despite injury concerns",
                content=f"Sources indicate {player_name} is expected to suit up Sunday despite being listed as questionable. He participated in limited practice sessions.",
                source="NFL Network",
                published_at=datetime.now() - timedelta(hours=6)
            ),
            NewsArticle(
                title=f"Fantasy outlook: {player_name} remains solid option",
                content=f"Despite injury concerns, {player_name} has been consistent this season with strong target share and red zone usage making him a reliable start.",
                source="FantasyPros",
                published_at=datetime.now() - timedelta(hours=12)
            )
        ]
        
        # In production, implement actual news API integration:
        # - NewsAPI, ESPN, NFL.com, Rotoworld, etc.
        # - Filter by player name and relevance
        # - Sort by recency and importance
        
        return mock_articles
    
    async def _analyze_article_sentiment(self, article: NewsArticle) -> NewsArticle:
        """Analyze sentiment of a single news article"""
        text = f"{article.title} {article.content}".lower()
        
        # Calculate sentiment score
        sentiment_score = self._calculate_text_sentiment(text)
        sentiment_label = self._classify_sentiment(sentiment_score)
        
        # Calculate fantasy impact
        impact_score = self._calculate_fantasy_impact_score(text)
        fantasy_impact = self._classify_fantasy_impact(impact_score)
        
        # Extract keywords
        keywords = self._extract_keywords(text)
        
        # Update article with analysis
        article.sentiment_score = sentiment_score
        article.sentiment_label = sentiment_label
        article.impact_score = impact_score
        article.fantasy_impact = fantasy_impact
        article.keywords = keywords
        
        return article
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text (-1.0 to 1.0)"""
        positive_score = 0.0
        negative_score = 0.0
        
        # Check positive keywords
        for keyword, weight in self.fantasy_keywords["positive"].items():
            if keyword in text:
                positive_score += weight
        
        # Check negative keywords
        for keyword, weight in self.fantasy_keywords["negative"].items():
            if keyword in text:
                negative_score += weight
        
        # Check patterns for additional context
        for pattern in self.sentiment_patterns["injury_severity"]:
            if re.search(pattern, text):
                negative_score += 1.0
        
        for pattern in self.sentiment_patterns["opportunity_increase"]:
            if re.search(pattern, text):
                positive_score += 1.0
        
        # Normalize to -1.0 to 1.0 range
        total_score = positive_score - negative_score
        if total_score > 0:
            return min(1.0, total_score / 5.0)  # Scale positive scores
        else:
            return max(-1.0, total_score / 5.0)  # Scale negative scores
    
    def _classify_sentiment(self, score: float) -> SentimentScore:
        """Convert sentiment score to classification"""
        if score >= 0.6:
            return SentimentScore.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentScore.POSITIVE
        elif score >= -0.2:
            return SentimentScore.NEUTRAL
        elif score >= -0.6:
            return SentimentScore.NEGATIVE
        else:
            return SentimentScore.VERY_NEGATIVE
    
    def _calculate_fantasy_impact_score(self, text: str) -> float:
        """Calculate fantasy football specific impact score"""
        impact_score = 0.0
        
        # Injury impact (negative)
        injury_terms = ["injured", "hurt", "questionable", "doubtful", "out"]
        for term in injury_terms:
            if term in text:
                impact_score -= 0.3
        
        # Opportunity impact (positive)  
        opportunity_terms = ["starter", "targets", "carries", "snaps", "role"]
        for term in opportunity_terms:
            if term in text:
                impact_score += 0.2
        
        # Performance impact
        performance_terms = ["touchdown", "yards", "score"]
        for term in performance_terms:
            if term in text:
                impact_score += 0.1
        
        return max(-1.0, min(1.0, impact_score))
    
    def _classify_fantasy_impact(self, score: float) -> FantasyImpact:
        """Convert impact score to classification"""
        if score >= 0.6:
            return FantasyImpact.MAJOR_POSITIVE
        elif score >= 0.2:
            return FantasyImpact.MINOR_POSITIVE
        elif score >= -0.2:
            return FantasyImpact.NEUTRAL
        elif score >= -0.6:
            return FantasyImpact.MINOR_NEGATIVE
        else:
            return FantasyImpact.MAJOR_NEGATIVE
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        keywords = []
        
        # Check all fantasy keywords
        for category in self.fantasy_keywords.values():
            for keyword in category.keys():
                if keyword in text:
                    keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_overall_sentiment(self, articles: List[NewsArticle]) -> Tuple[SentimentScore, float]:
        """Calculate overall sentiment from multiple articles"""
        if not articles:
            return SentimentScore.NEUTRAL, 0.0
        
        # Weight recent articles more heavily
        total_score = 0.0
        total_weight = 0.0
        
        for article in articles:
            age_hours = (datetime.now() - article.published_at).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 48.0))  # Decay over 48 hours
            
            total_score += (article.sentiment_score or 0.0) * weight
            total_weight += weight
        
        avg_score = total_score / total_weight if total_weight > 0 else 0.0
        sentiment_label = self._classify_sentiment(avg_score)
        
        return sentiment_label, avg_score
    
    def _calculate_fantasy_impact(self, articles: List[NewsArticle]) -> Tuple[FantasyImpact, float]:
        """Calculate overall fantasy impact from multiple articles"""
        if not articles:
            return FantasyImpact.NEUTRAL, 0.0
        
        # Weight recent articles more heavily
        total_score = 0.0
        total_weight = 0.0
        
        for article in articles:
            age_hours = (datetime.now() - article.published_at).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 48.0))
            
            total_score += (article.impact_score or 0.0) * weight
            total_weight += weight
        
        avg_score = total_score / total_weight if total_weight > 0 else 0.0
        impact_label = self._classify_fantasy_impact(avg_score)
        
        return impact_label, avg_score
    
    def _extract_key_themes(self, articles: List[NewsArticle]) -> List[str]:
        """Extract key themes from articles"""
        all_keywords = []
        for article in articles:
            if article.keywords:
                all_keywords.extend(article.keywords)
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Return top themes
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:5]]
    
    def _generate_recommendation(
        self, 
        sentiment: SentimentScore, 
        impact: FantasyImpact, 
        themes: List[str]
    ) -> str:
        """Generate actionable recommendation based on sentiment analysis"""
        
        # High impact negative news
        if impact in [FantasyImpact.MAJOR_NEGATIVE, FantasyImpact.MINOR_NEGATIVE]:
            if "injured" in themes or "questionable" in themes:
                return "CAUTION: Monitor injury status closely. Consider backup options."
            elif "benched" in themes or "backup" in themes:
                return "AVOID: Role concerns make this player risky for fantasy."
            else:
                return "DOWNGRADE: Negative news suggests reduced fantasy value."
        
        # High impact positive news
        elif impact in [FantasyImpact.MAJOR_POSITIVE, FantasyImpact.MINOR_POSITIVE]:
            if "starter" in themes or "promoted" in themes:
                return "UPGRADE: Increased opportunity makes this player attractive."
            elif "healthy" in themes or "ready" in themes:
                return "START: Health clearance boosts confidence in this player."
            else:
                return "CONSIDER: Positive developments increase fantasy appeal."
        
        # Neutral impact
        else:
            if sentiment == SentimentScore.POSITIVE:
                return "STABLE: Steady news coverage suggests consistent role."
            elif sentiment == SentimentScore.NEGATIVE:
                return "MONITOR: Mixed signals warrant careful observation."
            else:
                return "NEUTRAL: No significant news affecting fantasy value."
    
    def _calculate_confidence(self, articles: List[NewsArticle]) -> float:
        """Calculate confidence in the sentiment analysis"""
        if not articles:
            return 0.0
        
        # Base confidence on number of articles and recency
        base_confidence = min(1.0, len(articles) / 5.0)  # Max confidence with 5+ articles
        
        # Adjust for article age
        recent_articles = sum(1 for a in articles 
                             if (datetime.now() - a.published_at).total_seconds() / 3600 < 24)
        recency_boost = recent_articles / len(articles) * 0.2
        
        # Adjust for sentiment consistency
        sentiment_scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        if sentiment_scores:
            variance = sum((s - sum(sentiment_scores)/len(sentiment_scores))**2 
                          for s in sentiment_scores) / len(sentiment_scores)
            consistency_boost = max(0, 0.3 - variance)
        else:
            consistency_boost = 0
        
        final_confidence = min(1.0, base_confidence + recency_boost + consistency_boost)
        return round(final_confidence, 2)
    
    def _create_neutral_analysis(
        self, 
        player_id: int, 
        player_name: str, 
        error: Optional[str] = None
    ) -> SentimentAnalysis:
        """Create a neutral sentiment analysis when no data is available"""
        return SentimentAnalysis(
            player_id=player_id,
            player_name=player_name,
            overall_sentiment=SentimentScore.NEUTRAL,
            sentiment_score=0.0,
            fantasy_impact=FantasyImpact.NEUTRAL,
            impact_score=0.0,
            news_articles=[],
            key_themes=[],
            recommendation="NEUTRAL: No recent news available for analysis." + 
                         (f" Error: {error}" if error else ""),
            confidence=0.0,
            last_updated=datetime.now()
        )
    
    async def get_league_sentiment_summary(self, player_ids: List[int]) -> Dict[str, Any]:
        """Get sentiment summary for multiple players"""
        try:
            analyses = []
            for player_id in player_ids:
                # In a real implementation, you'd get player names from database
                player_name = f"Player_{player_id}"
                analysis = await self.analyze_player_sentiment(player_id, player_name)
                analyses.append(analysis)
            
            # Summarize trends
            positive_players = [a for a in analyses if a.sentiment_score > 0.2]
            negative_players = [a for a in analyses if a.sentiment_score < -0.2]
            
            return {
                "total_players": len(analyses),
                "positive_sentiment": len(positive_players),
                "negative_sentiment": len(negative_players),
                "top_positive": sorted(positive_players, key=lambda x: x.sentiment_score, reverse=True)[:5],
                "top_negative": sorted(negative_players, key=lambda x: x.sentiment_score)[:5],
                "overall_market_sentiment": sum(a.sentiment_score for a in analyses) / len(analyses) if analyses else 0.0,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating league sentiment summary: {e}")
            return {"error": str(e), "generated_at": datetime.now().isoformat()}


# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()