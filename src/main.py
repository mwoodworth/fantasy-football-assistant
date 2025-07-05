"""
Fantasy Football Assistant - Main Application Entry Point

This is the main FastAPI application for the Assistant Fantasy Football Manager.
Phase 1: Foundation implementation with database, auth, and basic APIs.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import logging

from .config import settings
from .models.database import create_tables, engine
from .models import Base
from .api import auth_router, players_router, fantasy_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered fantasy football assistant for draft strategies, lineup optimization, and trade analysis",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    logger.info("Starting Fantasy Football Assistant...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # TODO: Initialize team data
    # TODO: Set up background tasks for data updates

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(fantasy_router, prefix="/api")

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Fantasy Football Assistant is running"}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with project information"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assistant Fantasy Football Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; }
            .status { background: #f39c12; color: white; padding: 10px; border-radius: 5px; display: inline-block; }
            .features { margin: 20px 0; }
            .features ul { list-style-type: none; padding: 0; }
            .features li { padding: 10px; margin: 5px 0; background: #ecf0f1; border-radius: 5px; }
            .api-links { margin: 20px 0; }
            .api-links a { color: #3498db; text-decoration: none; margin-right: 20px; }
            .api-links a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏈 Assistant Fantasy Football Manager</h1>
            <div class="status">Status: Active - Phase 2 Complete with Mock Data</div>
            
            <div class="features">
                <h2>Available Features</h2>
                <ul>
                    <li>🎯 <strong>Draft Assistant</strong> - Real-time draft suggestions based on team needs</li>
                    <li>📊 <strong>Lineup Optimizer</strong> - Weekly lineup recommendations with matchup analysis</li>
                    <li>🔍 <strong>Waiver Wire Analysis</strong> - Identify pickup targets and trends</li>
                    <li>🤝 <strong>Trade Analyzer</strong> - Evaluate trade proposals with win probability</li>
                    <li>🚨 <strong>Injury Monitoring</strong> - Real-time injury updates and impact analysis</li>
                    <li>🤖 <strong>AI Insights</strong> - Natural language queries and automated reports</li>
                </ul>
            </div>
            
            <div class="api-links">
                <h2>API Documentation</h2>
                <a href="/api/docs">Interactive API Docs (Swagger)</a>
                <a href="/api/redoc">ReDoc Documentation</a>
                <a href="/health">Health Check</a>
            </div>
            
            <p><em>Phase 2 complete with mock data! Use the CLI tools to seed test data and explore all features.</em></p>
        </div>
    </body>
    </html>
    """

# Mock data management endpoint
@app.get("/api/mock-data/status")
async def get_mock_data_status():
    """Get status of mock data in database"""
    from .models.database import SessionLocal
    from .models.player import Player, Team
    from .models.user import User
    from .models.fantasy import League
    
    db = SessionLocal()
    try:
        return {
            "teams": db.query(Team).count(),
            "players": db.query(Player).count(),
            "users": db.query(User).count(),
            "leagues": db.query(League).count(),
            "mock_data_available": db.query(Player).count() > 0
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=6001,
        reload=True,
        log_level="info"
    )