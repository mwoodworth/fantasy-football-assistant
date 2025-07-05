"""
AI API endpoints for Fantasy Football Assistant

Provides endpoints for AI-powered chat, player analysis, trade evaluation,
automated insights, and machine learning predictions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import uuid

from ..models.database import get_db
from ..models.user import User
from ..utils.dependencies import get_current_active_user
from ..services.ai import ClaudeAIClient, MLPipeline, InsightsEngine
from ..services.ai.claude_client import ai_client
from ..services.ai.ml_pipeline import ml_pipeline
from ..services.ai.insights_engine import insights_engine
from ..services.ai.sentiment_analyzer import sentiment_analyzer
from ..services.ai.recommendation_engine import recommendation_engine
from ..services.ai.weekly_report_generator import weekly_report_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# Pydantic models for requests/responses
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message or question")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuity")
    analysis_type: str = Field("general", description="Type of analysis (general, player_analysis, trade_analysis, etc.)")

class ChatResponse(BaseModel):
    response: str
    confidence: float
    conversation_id: Optional[str]
    analysis_type: str
    timestamp: str
    usage: Optional[Dict[str, int]]
    error: Optional[str] = None

class PlayerAnalysisRequest(BaseModel):
    player_id: int = Field(..., description="Player ID to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class TradeAnalysisRequest(BaseModel):
    trade_data: Dict[str, Any] = Field(..., description="Trade proposal details")
    team_context: Optional[Dict[str, Any]] = Field(None, description="Team roster and context")

class WeeklyReportRequest(BaseModel):
    team_id: int = Field(..., description="Fantasy team ID")
    week: int = Field(..., ge=1, le=18, description="NFL week number")
    include_projections: bool = Field(True, description="Include ML projections")
    include_insights: bool = Field(True, description="Include AI insights")

class PlayerPredictionRequest(BaseModel):
    player_id: int = Field(..., description="Player ID")
    week_context: Optional[Dict[str, Any]] = Field(None, description="Week-specific context")

class BreakoutCandidatesRequest(BaseModel):
    position: Optional[str] = Field(None, description="Filter by position")
    min_probability: float = Field(0.6, ge=0.0, le=1.0, description="Minimum breakout probability")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of candidates")

class SentimentAnalysisRequest(BaseModel):
    player_id: int = Field(..., description="Player ID to analyze")
    player_name: str = Field(..., description="Player name for news search")
    time_range_hours: int = Field(48, ge=1, le=168, description="Hours to look back for news")

class LeagueSentimentRequest(BaseModel):
    player_ids: List[int] = Field(..., min_items=1, max_items=50, description="List of player IDs to analyze")

class RecommendationRequest(BaseModel):
    team_context: Dict[str, Any] = Field(..., description="Current team roster and situation")
    league_context: Dict[str, Any] = Field(..., description="League settings and context")
    current_week: int = Field(..., ge=1, le=18, description="Current NFL week")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences (risk tolerance, etc.)")

class QuickRecommendationRequest(BaseModel):
    request_type: str = Field(..., description="Type of recommendation (start_sit, waiver_wire, trade_opportunity)")
    context: Dict[str, Any] = Field(..., description="Context for the recommendation")

class WeeklyReportRequest(BaseModel):
    team_context: Dict[str, Any] = Field(..., description="Current team roster and situation")
    league_context: Dict[str, Any] = Field(..., description="League settings and context")
    week: int = Field(..., ge=1, le=18, description="NFL week number")
    include_analysis_details: bool = Field(True, description="Include detailed player analysis")


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    chat_request: ChatMessage,
    current_user: User = Depends(get_current_active_user)
):
    """
    Natural language chat with AI fantasy football assistant
    
    Supports various types of queries:
    - General fantasy football questions
    - Player analysis requests
    - Trade evaluations
    - Start/sit decisions
    - Draft strategy
    """
    try:
        logger.info(f"AI chat request from user {current_user.id}: {chat_request.message[:100]}...")
        
        # Generate conversation ID if not provided
        if not chat_request.conversation_id:
            chat_request.conversation_id = str(uuid.uuid4())
        
        # Add user context to the request
        enhanced_context = chat_request.context or {}
        enhanced_context["user_id"] = current_user.id
        enhanced_context["user_preferences"] = {
            "scoring_system": "ppr",  # Could be user preference
            "league_size": 12  # Could be from user's leagues
        }
        
        # Get AI response
        result = await ai_client.chat_completion(
            message=chat_request.message,
            context=enhanced_context,
            conversation_id=chat_request.conversation_id,
            analysis_type=chat_request.analysis_type
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"AI chat error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process AI request: {str(e)}"
        )


@router.post("/player/analyze")
async def analyze_player(
    analysis_request: PlayerAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered player analysis with ML predictions
    
    Provides comprehensive analysis including:
    - AI-generated insights and recommendations
    - ML predictions for performance
    - Trend analysis
    - Rest-of-season outlook
    """
    try:
        logger.info(f"Player analysis request for player {analysis_request.player_id} by user {current_user.id}")
        
        # Get player analysis
        analysis = await insights_engine.analyze_player_outlook(
            player_id=analysis_request.player_id,
            analysis_type=analysis_request.analysis_type,
            context=analysis_request.context
        )
        
        return {
            "success": True,
            "data": analysis,
            "meta": {
                "player_id": analysis_request.player_id,
                "analysis_type": analysis_request.analysis_type,
                "requested_by": current_user.id,
                "generated_at": analysis.get("generated_at")
            }
        }
        
    except Exception as e:
        logger.error(f"Player analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze player: {str(e)}"
        )


@router.post("/trade/analyze")
async def analyze_trade(
    trade_request: TradeAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    AI-powered trade analysis and recommendation
    
    Evaluates trade proposals considering:
    - Player values and projections
    - Team needs and context
    - Risk assessment
    - Timing factors
    """
    try:
        logger.info(f"Trade analysis request by user {current_user.id}")
        
        # Add user context
        enhanced_team_context = trade_request.team_context or {}
        enhanced_team_context["user_id"] = current_user.id
        
        # Get trade evaluation
        evaluation = await insights_engine.evaluate_trade_proposal(
            trade_data=trade_request.trade_data,
            team_context=enhanced_team_context
        )
        
        return {
            "success": True,
            "data": evaluation,
            "meta": {
                "requested_by": current_user.id,
                "evaluated_at": evaluation.get("evaluated_at")
            }
        }
        
    except Exception as e:
        logger.error(f"Trade analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze trade: {str(e)}"
        )


@router.post("/insights/weekly")
async def generate_weekly_insights(
    report_request: WeeklyReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered weekly team report
    
    Includes:
    - Team performance analysis
    - Start/sit recommendations
    - Waiver wire targets
    - Trade opportunities
    - Weekly outlook
    """
    try:
        logger.info(f"Weekly report request for team {report_request.team_id}, week {report_request.week}")
        
        # Generate comprehensive weekly report
        report = await insights_engine.generate_weekly_report(
            team_id=report_request.team_id,
            user_id=current_user.id,
            week=report_request.week,
            db_session=db,
            league_context={"include_projections": report_request.include_projections}
        )
        
        return {
            "success": True,
            "data": report,
            "meta": {
                "team_id": report_request.team_id,
                "week": report_request.week,
                "requested_by": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Weekly insights error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate weekly insights: {str(e)}"
        )


@router.post("/predictions/player")
async def predict_player_performance(
    prediction_request: PlayerPredictionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    ML predictions for player performance
    
    Provides:
    - Fantasy points prediction with confidence intervals
    - Boom/bust probability
    - Injury risk assessment
    - Breakout potential (if applicable)
    """
    try:
        logger.info(f"Player prediction request for player {prediction_request.player_id}")
        
        # This would integrate with your player service to get player data
        player_data = {
            "player_id": prediction_request.player_id,
            "name": "Sample Player",  # Would come from database
            "position": "RB",  # Would come from database
            # ... other player stats
        }
        
        week_context = prediction_request.week_context or {}
        
        # Get ML predictions
        predictions = {
            "points_prediction": ml_pipeline.predict_player_points(player_data, week_context),
            "boom_bust_probability": ml_pipeline.predict_boom_bust_probability(player_data, week_context),
            "injury_risk": ml_pipeline.assess_injury_risk(player_data, week_context)
        }
        
        return {
            "success": True,
            "data": {
                "player_id": prediction_request.player_id,
                "predictions": predictions,
                "generated_at": predictions["points_prediction"].get("timestamp"),
                "model_accuracy": {
                    "points_mae": predictions["points_prediction"].get("model_accuracy"),
                    "classification_acc": predictions["boom_bust_probability"].get("model_accuracy")
                }
            },
            "meta": {
                "requested_by": current_user.id,
                "prediction_methods": ["random_forest", "gradient_boosting", "logistic_regression"]
            }
        }
        
    except Exception as e:
        logger.error(f"Player prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to predict player performance: {str(e)}"
        )


@router.get("/insights/breakout-candidates")
async def get_breakout_candidates(
    position: Optional[str] = Query(None, description="Filter by position"),
    min_probability: float = Query(0.6, ge=0.0, le=1.0, description="Minimum breakout probability"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of candidates"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Identify players with high breakout potential using ML
    
    Returns players likely to significantly outperform current expectations
    based on usage trends, opportunity, and performance indicators.
    """
    try:
        logger.info(f"Breakout candidates request by user {current_user.id}")
        
        # This would get all players from database and filter by position
        players_data = []  # Would come from database query
        
        # Get breakout candidates
        candidates = ml_pipeline.identify_breakout_candidates(
            players_data=players_data,
            min_probability=min_probability
        )
        
        # Filter by position if specified
        if position:
            candidates = [c for c in candidates if c.get("position") == position.upper()]
        
        # Limit results
        candidates = candidates[:limit]
        
        return {
            "success": True,
            "data": {
                "candidates": candidates,
                "filter_criteria": {
                    "position": position,
                    "min_probability": min_probability,
                    "limit": limit
                },
                "total_candidates": len(candidates)
            },
            "meta": {
                "requested_by": current_user.id,
                "model_type": "xgboost_classifier"
            }
        }
        
    except Exception as e:
        logger.error(f"Breakout candidates error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify breakout candidates: {str(e)}"
        )


@router.post("/models/train")
async def train_ml_models(
    background_tasks: BackgroundTasks,
    retrain_all: bool = Query(False, description="Retrain all models from scratch"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Train or retrain ML models with latest data
    
    This is typically run periodically or when significant new data is available.
    Training happens in the background to avoid blocking the API.
    """
    try:
        logger.info(f"ML model training initiated by user {current_user.id}")
        
        # Check if user has admin privileges (you might want to restrict this)
        if not current_user.is_admin:  # Assuming you have admin flag
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to train models"
            )
        
        # Add training to background tasks
        background_tasks.add_task(
            _train_models_background,
            retrain_all=retrain_all,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Model training initiated in background",
            "data": {
                "retrain_all": retrain_all,
                "estimated_time": "15-30 minutes",
                "initiated_by": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Model training initiation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate model training: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary of conversation history"""
    try:
        summary = ai_client.get_conversation_summary(conversation_id)
        
        return {
            "success": True,
            "data": {
                "conversation_id": conversation_id,
                "summary": summary
            },
            "meta": {
                "requested_by": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Conversation summary error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation summary: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Clear conversation history"""
    try:
        ai_client.clear_conversation(conversation_id)
        
        return {
            "success": True,
            "message": f"Conversation {conversation_id} cleared",
            "data": {
                "conversation_id": conversation_id,
                "cleared_by": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Clear conversation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear conversation: {str(e)}"
        )


@router.post("/sentiment/analyze")
async def analyze_player_sentiment(
    sentiment_request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze sentiment for a specific player from recent news
    
    Provides comprehensive sentiment analysis including:
    - Overall sentiment classification and score
    - Fantasy football impact assessment
    - Key themes and news summary
    - Actionable recommendations
    - Confidence metrics
    """
    try:
        logger.info(f"Sentiment analysis request for player {sentiment_request.player_id} by user {current_user.id}")
        
        # Get sentiment analysis
        analysis = await sentiment_analyzer.analyze_player_sentiment(
            player_id=sentiment_request.player_id,
            player_name=sentiment_request.player_name,
            time_range_hours=sentiment_request.time_range_hours
        )
        
        # Convert to JSON-serializable format
        analysis_dict = {
            "player_id": analysis.player_id,
            "player_name": analysis.player_name,
            "overall_sentiment": analysis.overall_sentiment.value,
            "sentiment_score": analysis.sentiment_score,
            "fantasy_impact": analysis.fantasy_impact.value,
            "impact_score": analysis.impact_score,
            "key_themes": analysis.key_themes,
            "recommendation": analysis.recommendation,
            "confidence": analysis.confidence,
            "last_updated": analysis.last_updated.isoformat(),
            "news_summary": {
                "total_articles": len(analysis.news_articles),
                "recent_articles": len([a for a in analysis.news_articles 
                                     if (datetime.now() - a.published_at).total_seconds() / 3600 < 24]),
                "sources": list(set(a.source for a in analysis.news_articles)),
                "latest_news": analysis.news_articles[0].title if analysis.news_articles else None
            }
        }
        
        return {
            "success": True,
            "data": analysis_dict,
            "meta": {
                "requested_by": current_user.id,
                "analysis_type": "sentiment_analysis",
                "time_range_hours": sentiment_request.time_range_hours,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze player sentiment: {str(e)}"
        )


@router.post("/sentiment/league-summary")
async def get_league_sentiment_summary(
    league_request: LeagueSentimentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get sentiment summary for multiple players in a league context
    
    Provides:
    - Overall market sentiment trends
    - Top positive and negative sentiment players
    - League-wide news themes
    - Comparative sentiment analysis
    """
    try:
        logger.info(f"League sentiment analysis for {len(league_request.player_ids)} players by user {current_user.id}")
        
        # Get league sentiment summary
        summary = await sentiment_analyzer.get_league_sentiment_summary(league_request.player_ids)
        
        return {
            "success": True,
            "data": {
                "league_sentiment": summary,
                "player_count": len(league_request.player_ids),
                "analysis_summary": {
                    "overall_sentiment": summary.get("overall_market_sentiment", 0.0),
                    "positive_players": summary.get("positive_sentiment", 0),
                    "negative_players": summary.get("negative_sentiment", 0),
                    "neutral_players": summary.get("total_players", 0) - 
                                     summary.get("positive_sentiment", 0) - 
                                     summary.get("negative_sentiment", 0)
                }
            },
            "meta": {
                "requested_by": current_user.id,
                "analysis_type": "league_sentiment_summary",
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"League sentiment analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze league sentiment: {str(e)}"
        )


@router.get("/sentiment/trending")
async def get_trending_sentiment(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of trending players"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get players with the most significant sentiment changes
    
    Identifies players with:
    - Major positive news (opportunities, health updates)
    - Major negative news (injuries, role changes)
    - Trending stories and breaking news
    """
    try:
        logger.info(f"Trending sentiment analysis for last {hours} hours by user {current_user.id}")
        
        # In a real implementation, this would:
        # 1. Query database for all active players
        # 2. Analyze recent sentiment changes
        # 3. Identify biggest sentiment shifts
        # 4. Return trending players with context
        
        # Mock trending data for demonstration
        trending_data = {
            "positive_trending": [
                {
                    "player_id": 1001,
                    "player_name": "Josh Allen",
                    "sentiment_change": 0.6,
                    "reason": "Cleared from injury report, full practice participation",
                    "fantasy_impact": "major_positive"
                },
                {
                    "player_id": 1002,
                    "player_name": "Christian McCaffrey",
                    "sentiment_change": 0.4,
                    "reason": "Coach confirms lead role, increased red zone usage",
                    "fantasy_impact": "minor_positive"
                }
            ],
            "negative_trending": [
                {
                    "player_id": 2001,
                    "player_name": "Ja'Marr Chase",
                    "sentiment_change": -0.7,
                    "reason": "Listed as questionable with hip injury",
                    "fantasy_impact": "major_negative"
                },
                {
                    "player_id": 2002,
                    "player_name": "Derrick Henry",
                    "sentiment_change": -0.3,
                    "reason": "Reduced practice participation, rest concerns",
                    "fantasy_impact": "minor_negative"
                }
            ],
            "breaking_news": [
                {
                    "player_id": 3001,
                    "player_name": "Travis Kelce",
                    "news": "Ruled out for Sunday's game with ankle injury",
                    "impact": "major_negative",
                    "published_minutes_ago": 15
                }
            ]
        }
        
        return {
            "success": True,
            "data": {
                "trending_sentiment": trending_data,
                "time_range_hours": hours,
                "market_summary": {
                    "overall_trend": "mixed",
                    "major_movers": len(trending_data["positive_trending"]) + len(trending_data["negative_trending"]),
                    "breaking_news_count": len(trending_data["breaking_news"])
                }
            },
            "meta": {
                "requested_by": current_user.id,
                "analysis_type": "trending_sentiment",
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Trending sentiment analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trending sentiment: {str(e)}"
        )


@router.post("/recommendations/comprehensive")
async def get_comprehensive_recommendations(
    rec_request: RecommendationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate comprehensive AI-powered recommendations for fantasy team
    
    Provides complete recommendation suite including:
    - Lineup optimization suggestions
    - Waiver wire targets with analysis
    - Trade opportunity identification
    - Season-long strategic guidance
    - Prioritized action items
    """
    try:
        logger.info(f"Comprehensive recommendations request for user {current_user.id}, week {rec_request.current_week}")
        
        # Generate comprehensive recommendations
        recommendations_suite = await recommendation_engine.generate_comprehensive_recommendations(
            user_id=current_user.id,
            team_context=rec_request.team_context,
            league_context=rec_request.league_context,
            current_week=rec_request.current_week,
            preferences=rec_request.preferences
        )
        
        # Convert to JSON-serializable format
        suite_dict = {
            "user_id": recommendations_suite.user_id,
            "team_id": recommendations_suite.team_id,
            "overall_strategy": recommendations_suite.overall_strategy,
            "key_priorities": recommendations_suite.key_priorities,
            "season_outlook": recommendations_suite.season_outlook,
            "generated_at": recommendations_suite.generated_at.isoformat(),
            "valid_until": recommendations_suite.valid_until.isoformat(),
            "recommendations": []
        }
        
        # Convert recommendations
        for rec in recommendations_suite.recommendations:
            rec_dict = {
                "id": rec.id,
                "type": rec.type.value,
                "title": rec.title,
                "description": rec.description,
                "action": rec.action,
                "reasoning": rec.reasoning,
                "confidence": rec.confidence.value,
                "confidence_score": rec.confidence_score,
                "priority": rec.priority,
                "expected_impact": rec.expected_impact,
                "alternatives": rec.alternatives,
                "risk_factors": rec.risk_factors,
                "created_at": rec.created_at.isoformat(),
                "expires_at": rec.expires_at.isoformat() if rec.expires_at else None
            }
            suite_dict["recommendations"].append(rec_dict)
        
        return {
            "success": True,
            "data": suite_dict,
            "meta": {
                "total_recommendations": len(suite_dict["recommendations"]),
                "high_priority_count": len([r for r in suite_dict["recommendations"] if r["priority"] >= 8]),
                "recommendation_types": list(set(r["type"] for r in suite_dict["recommendations"])),
                "requested_by": current_user.id,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive recommendations error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate comprehensive recommendations: {str(e)}"
        )


@router.post("/recommendations/quick")
async def get_quick_recommendation(
    quick_request: QuickRecommendationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get quick AI recommendation for specific fantasy decision
    
    Provides fast, targeted recommendations for:
    - Start/sit decisions
    - Waiver wire pickups
    - Trade opportunities
    - Draft picks
    """
    try:
        logger.info(f"Quick recommendation request: {quick_request.request_type} by user {current_user.id}")
        
        # Map request type to enum
        from ..services.ai.recommendation_engine import RecommendationType
        type_mapping = {
            "start_sit": RecommendationType.START_SIT,
            "waiver_wire": RecommendationType.WAIVER_WIRE,
            "trade_opportunity": RecommendationType.TRADE_OPPORTUNITY,
            "draft_strategy": RecommendationType.DRAFT_STRATEGY
        }
        
        recommendation_type = type_mapping.get(quick_request.request_type)
        if not recommendation_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recommendation type: {quick_request.request_type}"
            )
        
        # Generate quick recommendations
        recommendations = await recommendation_engine.get_quick_recommendations(
            user_id=current_user.id,
            request_type=recommendation_type,
            context=quick_request.context
        )
        
        # Convert to JSON format
        recommendations_data = []
        for rec in recommendations:
            rec_data = {
                "id": rec.id,
                "type": rec.type.value,
                "title": rec.title,
                "description": rec.description,
                "action": rec.action,
                "reasoning": rec.reasoning,
                "confidence": rec.confidence.value,
                "confidence_score": rec.confidence_score,
                "priority": rec.priority,
                "expected_impact": rec.expected_impact,
                "alternatives": rec.alternatives,
                "risk_factors": rec.risk_factors,
                "created_at": rec.created_at.isoformat()
            }
            recommendations_data.append(rec_data)
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations_data,
                "request_type": quick_request.request_type,
                "context": quick_request.context
            },
            "meta": {
                "recommendation_count": len(recommendations_data),
                "request_type": quick_request.request_type,
                "requested_by": current_user.id,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Quick recommendation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quick recommendation: {str(e)}"
        )


@router.get("/recommendations/types")
async def get_recommendation_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available recommendation types and their descriptions
    
    Returns all available recommendation types that can be requested
    from the AI recommendation engine.
    """
    try:
        from ..services.ai.recommendation_engine import RecommendationType
        
        recommendation_types = {
            "lineup_optimization": {
                "name": "Lineup Optimization",
                "description": "Optimize weekly lineup with start/sit recommendations",
                "use_case": "Weekly lineup decisions and player comparisons"
            },
            "waiver_wire": {
                "name": "Waiver Wire Targets",
                "description": "Identify best available players to add",
                "use_case": "Finding sleepers and addressing roster needs"
            },
            "trade_opportunity": {
                "name": "Trade Opportunities",
                "description": "Find beneficial trade partners and proposals",
                "use_case": "Improving roster through strategic trades"
            },
            "draft_strategy": {
                "name": "Draft Strategy",
                "description": "Draft guidance and player selection advice",
                "use_case": "Draft preparation and in-draft decisions"
            },
            "start_sit": {
                "name": "Start/Sit Decisions",
                "description": "Quick start/sit recommendations for specific players",
                "use_case": "Last-minute lineup decisions"
            },
            "season_strategy": {
                "name": "Season Strategy",
                "description": "Long-term strategic guidance and planning",
                "use_case": "Playoff preparation and season-long planning"
            }
        }
        
        return {
            "success": True,
            "data": {
                "recommendation_types": recommendation_types,
                "total_types": len(recommendation_types)
            },
            "meta": {
                "requested_by": current_user.id,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Get recommendation types error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendation types: {str(e)}"
        )


@router.post("/reports/weekly")
async def generate_weekly_report(
    report_request: WeeklyReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI-powered weekly report for fantasy team
    
    Provides complete weekly analysis including:
    - Detailed player analysis with ML predictions and sentiment
    - Optimized lineup recommendations with matchup analysis
    - Strategic insights and actionable recommendations
    - Performance tracking and season trajectory analysis
    - Opponent analysis and league trends
    - Executive summary with key insights
    """
    try:
        logger.info(f"Weekly report request for user {current_user.id}, week {report_request.week}")
        
        # Generate comprehensive weekly report
        team_id = report_request.team_context.get("team_id", f"user_{current_user.id}")
        
        weekly_report = await weekly_report_generator.generate_weekly_report(
            team_id=team_id,
            user_id=current_user.id,
            week=report_request.week,
            team_context=report_request.team_context,
            league_context=report_request.league_context,
            include_analysis_details=report_request.include_analysis_details
        )
        
        # Convert to JSON-serializable format
        def serialize_player_analysis(player: Any) -> Dict[str, Any]:
            return {
                "player_id": player.player_id,
                "player_name": player.player_name,
                "position": player.position,
                "team": player.team,
                "projected_points": player.projected_points,
                "projection_range": player.projection_range,
                "confidence": round(player.confidence, 3),
                "start_sit_recommendation": player.start_sit_recommendation,
                "reasoning": player.reasoning,
                "risk_factors": player.risk_factors,
                "upside_factors": player.upside_factors,
                "matchup": {
                    "opponent": player.matchup.opponent,
                    "matchup_rating": player.matchup.matchup_rating,
                    "matchup_score": player.matchup.matchup_score,
                    "key_factors": player.matchup.key_factors,
                    "start_recommendation": player.matchup.start_recommendation
                },
                "sentiment": {
                    "overall_sentiment": player.sentiment_analysis.overall_sentiment.value,
                    "sentiment_score": player.sentiment_analysis.sentiment_score,
                    "fantasy_impact": player.sentiment_analysis.fantasy_impact.value,
                    "recommendation": player.sentiment_analysis.recommendation,
                    "confidence": player.sentiment_analysis.confidence
                } if hasattr(player.sentiment_analysis, 'overall_sentiment') else None,
                "ml_predictions": player.ml_predictions
            }
        
        report_dict = {
            "team_id": weekly_report.team_id,
            "user_id": weekly_report.user_id,
            "week": weekly_report.week,
            "generated_at": weekly_report.generated_at.isoformat(),
            
            # Executive summary
            "executive_summary": weekly_report.executive_summary,
            "key_insights": weekly_report.key_insights,
            "week_outlook": weekly_report.week_outlook,
            
            # Team metrics
            "lineup_score": weekly_report.lineup_score,
            "projected_total": weekly_report.projected_total,
            "confidence_level": weekly_report.confidence_level,
            "risk_assessment": weekly_report.risk_assessment,
            
            # Player analysis
            "starting_lineup": [serialize_player_analysis(p) for p in weekly_report.starting_lineup],
            "bench_considerations": [serialize_player_analysis(p) for p in weekly_report.bench_considerations] if report_request.include_analysis_details else [],
            
            # Strategic elements
            "recommendations": weekly_report.recommendations,
            "waiver_targets": weekly_report.waiver_targets,
            "trade_considerations": weekly_report.trade_considerations,
            
            # Market intelligence
            "opponent_analysis": weekly_report.opponent_analysis,
            "league_trends": weekly_report.league_trends,
            
            # Performance tracking
            "last_week_recap": weekly_report.last_week_recap,
            "season_trajectory": weekly_report.season_trajectory
        }
        
        return {
            "success": True,
            "data": report_dict,
            "meta": {
                "report_type": "weekly_comprehensive",
                "analysis_depth": "detailed" if report_request.include_analysis_details else "summary",
                "starting_lineup_count": len(weekly_report.starting_lineup),
                "total_recommendations": len(weekly_report.recommendations),
                "confidence_level": weekly_report.confidence_level,
                "lineup_score": weekly_report.lineup_score,
                "requested_by": current_user.id,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Weekly report generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate weekly report: {str(e)}"
        )


@router.get("/reports/weekly/template")
async def get_weekly_report_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get template structure for weekly report request
    
    Returns the expected structure for team_context and league_context
    to help users format their weekly report requests properly.
    """
    try:
        template = {
            "team_context": {
                "team_id": "unique_team_identifier",
                "roster": [
                    {
                        "id": "player_id",
                        "name": "Player Name",
                        "position": "QB|RB|WR|TE|K|DST",
                        "team": "NFL_TEAM",
                        "projected_points": 15.5,
                        "status": "active|injured|bye",
                        "ownership_percentage": 95.2
                    }
                ],
                "record": {
                    "wins": 7,
                    "losses": 5,
                    "ties": 0
                },
                "current_standing": 4,
                "playoff_position": "in_hunt"
            },
            "league_context": {
                "league_id": "unique_league_identifier",
                "scoring_system": "ppr|half_ppr|standard",
                "league_size": 12,
                "playoff_spots": 6,
                "trade_deadline": "2024-11-19",
                "current_week": 12,
                "roster_positions": {
                    "QB": 1,
                    "RB": 2,
                    "WR": 2,
                    "TE": 1,
                    "FLEX": 1,
                    "K": 1,
                    "DST": 1,
                    "BENCH": 6
                }
            },
            "optional_preferences": {
                "risk_tolerance": "conservative|balanced|aggressive",
                "analysis_focus": "projections|matchups|sentiment|all",
                "include_bench_analysis": True,
                "include_waiver_suggestions": True,
                "include_trade_analysis": True
            }
        }
        
        return {
            "success": True,
            "data": {
                "template": template,
                "description": "Use this structure to format your weekly report request",
                "required_fields": [
                    "team_context.roster",
                    "league_context.scoring_system",
                    "week"
                ],
                "optional_fields": [
                    "team_context.record",
                    "league_context.roster_positions",
                    "include_analysis_details"
                ]
            },
            "meta": {
                "template_version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "requested_by": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Get weekly report template error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weekly report template: {str(e)}"
        )


@router.get("/health")
async def ai_health_check():
    """Check health of AI services"""
    try:
        health_status = {
            "ai_service": "healthy",
            "claude_api": "unknown",
            "ml_models": "unknown",
            "insights_engine": "healthy"
        }
        
        # Check Claude API
        if ai_client.client:
            health_status["claude_api"] = "configured"
        else:
            health_status["claude_api"] = "not_configured"
        
        # Check ML models
        if ml_pipeline.models:
            health_status["ml_models"] = f"{len(ml_pipeline.models)} models loaded"
        else:
            health_status["ml_models"] = "no_models_loaded"
        
        return {
            "success": True,
            "data": health_status,
            "timestamp": logger.info("AI health check completed")
        }
        
    except Exception as e:
        logger.error(f"AI health check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI health check failed: {str(e)}"
        )


# Background task functions
async def _train_models_background(retrain_all: bool, user_id: int):
    """Background task for training ML models"""
    try:
        logger.info(f"Starting background model training (retrain_all={retrain_all}, user={user_id})")
        
        # This would load training data from database
        import pandas as pd
        training_data = pd.DataFrame()  # Would come from database
        
        if len(training_data) > 0:
            results = ml_pipeline.train_models(training_data)
            ml_pipeline.save_models()
            logger.info(f"Model training completed: {results}")
        else:
            logger.warning("No training data available for model training")
            
    except Exception as e:
        logger.error(f"Background model training error: {e}")


# Initialize ML models on startup
@router.on_event("startup")
async def load_ml_models():
    """Load pre-trained ML models on startup"""
    try:
        success = ml_pipeline.load_models()
        if success:
            logger.info("ML models loaded successfully")
        else:
            logger.warning("No pre-trained models found - will need training")
    except Exception as e:
        logger.error(f"Error loading ML models: {e}")