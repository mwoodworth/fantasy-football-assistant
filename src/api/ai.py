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