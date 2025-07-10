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
import subprocess
import os
import signal
import atexit
import time
import socketio

from .config import settings
from .models.database import create_tables, engine
from .models import Base
from .api import auth_router, players_router, fantasy_router, espn_router, espn_enhanced_router, ai_router, dashboard_router, teams_router
from .services.websocket_server import create_socket_app, sio
from .middleware.rate_limiter import RateLimitMiddleware
from .middleware.error_handler import setup_exception_handlers
from .middleware.request_tracker import RequestTrackingMiddleware, PerformanceMonitoringMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variable to track ESPN service process
espn_service_process = None

def start_espn_service():
    """Start the Node.js ESPN service"""
    global espn_service_process
    
    try:
        espn_service_dir = Path(__file__).parent.parent / "espn-service"
        
        if not espn_service_dir.exists():
            logger.warning(f"ESPN service directory not found: {espn_service_dir}")
            return None
        
        # Check if Node.js is available
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Node.js not found. Please install Node.js to run the ESPN service.")
            return None
        
        # Check if package.json exists
        package_json_path = espn_service_dir / "package.json"
        if not package_json_path.exists():
            logger.error(f"package.json not found in {espn_service_dir}")
            return None
        
        # Check if node_modules exists, install if not
        node_modules_path = espn_service_dir / "node_modules"
        if not node_modules_path.exists():
            logger.info("Installing ESPN service dependencies...")
            subprocess.run(["npm", "install"], cwd=espn_service_dir, check=True)
        
        # Start the ESPN service
        logger.info("Starting ESPN service...")
        espn_service_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=espn_service_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if espn_service_process.poll() is None:
            logger.info("ESPN service started successfully on port 3001")
            return espn_service_process
        else:
            stdout, stderr = espn_service_process.communicate()
            logger.error(f"ESPN service failed to start: {stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error starting ESPN service: {e}")
        return None

def stop_espn_service():
    """Stop the Node.js ESPN service"""
    global espn_service_process
    
    if espn_service_process and espn_service_process.poll() is None:
        logger.info("Stopping ESPN service...")
        espn_service_process.terminate()
        try:
            espn_service_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("ESPN service did not stop gracefully, forcing termination")
            espn_service_process.kill()
        espn_service_process = None
        logger.info("ESPN service stopped")

# Register cleanup function
atexit.register(stop_espn_service)

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
    
    # Start ESPN service
    espn_process = start_espn_service()
    if espn_process:
        logger.info("ESPN service integration enabled")
    else:
        logger.warning("ESPN service not available - some features may be limited")
    
    # Start draft monitor service
    try:
        from .services.draft_monitor import draft_monitor
        await draft_monitor.start()
        logger.info("Draft monitor service started")
    except Exception as e:
        logger.error(f"Failed to start draft monitor: {e}")
    
    # Start background sync service (can be enabled via BACKGROUND_SYNC_ENABLED env var)
    if os.getenv('BACKGROUND_SYNC_ENABLED', 'false').lower() == 'true':
        try:
            from .services.background_sync import background_sync
            await background_sync.start()
            logger.info("Background sync service started")
        except Exception as e:
            logger.error(f"Failed to start background sync: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("Shutting down Fantasy Football Assistant...")
    
    # Stop draft monitor
    try:
        from .services.draft_monitor import draft_monitor
        await draft_monitor.stop()
        logger.info("Draft monitor service stopped")
    except Exception as e:
        logger.error(f"Error stopping draft monitor: {e}")
    
    # Stop background sync service if running
    if os.getenv('BACKGROUND_SYNC_ENABLED', 'false').lower() == 'true':
        try:
            from .services.background_sync import background_sync
            await background_sync.stop()
            logger.info("Background sync service stopped")
        except Exception as e:
            logger.error(f"Error stopping background sync: {e}")
    
    stop_espn_service()

# Add middleware in the correct order (order matters!)

# 1. Request tracking (first to track all requests)
app.add_middleware(RequestTrackingMiddleware, log_request_body=False, slow_request_threshold=2.0)

# 2. Performance monitoring
app.add_middleware(PerformanceMonitoringMiddleware)

# 3. Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    default_limit=60,      # 60 requests per minute default
    default_window=60,
    espn_limit=10,         # 10 ESPN requests per minute
    espn_window=60,
    ai_limit=20,           # 20 AI requests per hour
    ai_window=3600
)

# 4. CORS (must be after rate limiting)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(fantasy_router, prefix="/api")
app.include_router(espn_router, prefix="/api")
app.include_router(espn_enhanced_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(teams_router, prefix="/api")

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount Socket.IO on a specific path
app.mount("/socket.io", socketio.ASGIApp(sio))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global espn_service_process
    
    # Check ESPN service status
    espn_status = "unknown"
    if espn_service_process:
        if espn_service_process.poll() is None:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:3001/health", timeout=2)
                    espn_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                espn_status = "unreachable"
        else:
            espn_status = "stopped"
    else:
        espn_status = "not_started"
    
    return {
        "status": "healthy", 
        "message": "Fantasy Football Assistant is running",
        "services": {
            "fastapi": "healthy",
            "espn_service": espn_status
        },
        "ports": {
            "main_api": 6001,
            "espn_service": 3001
        }
    }

# Performance monitoring endpoint
@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics"""
    # Get performance stats from middleware
    perf_middleware = None
    for middleware in app.middleware:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'PerformanceMonitoringMiddleware':
            perf_middleware = middleware
            break
    
    if perf_middleware and hasattr(perf_middleware, 'app'):
        stats = perf_middleware.app.get_stats()
        return {
            "endpoint_stats": stats,
            "timestamp": time.time()
        }
    
    return {"message": "Performance metrics not available"}

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
            <div class="status">Status: Active - Phase 3 Development (AI Integration)</div>
            
            <div class="features">
                <h2>Available Features</h2>
                <ul>
                    <li>🎯 <strong>Draft Assistant</strong> - Real-time draft suggestions based on team needs</li>
                    <li>📊 <strong>Lineup Optimizer</strong> - Weekly lineup recommendations with matchup analysis</li>
                    <li>🔍 <strong>Waiver Wire Analysis</strong> - Identify pickup targets and trends</li>
                    <li>🤝 <strong>Trade Analyzer</strong> - Evaluate trade proposals with win probability</li>
                    <li>🚨 <strong>Injury Monitoring</strong> - Real-time injury updates and impact analysis</li>
                    <li>🤖 <strong>AI Chat Assistant</strong> - Natural language queries and intelligent responses</li>
                    <li>🧠 <strong>ML Predictions</strong> - Player performance forecasting with confidence intervals</li>
                    <li>📈 <strong>Automated Insights</strong> - AI-generated weekly reports and recommendations</li>
                    <li>🔮 <strong>Breakout Detection</strong> - ML-powered identification of emerging players</li>
                </ul>
            </div>
            
            <div class="api-links">
                <h2>API Documentation</h2>
                <a href="/api/docs">Interactive API Docs (Swagger)</a>
                <a href="/api/redoc">ReDoc Documentation</a>
                <a href="/health">Health Check</a>
            </div>
            
            <p><em>Phase 3 in development - AI integration underway! Core features from Phase 2 remain fully functional.</em></p>
            <p><strong>ESPN Authentication:</strong> <a href="/static/espn-login.html">ESPN Login Page</a></p>
            <p><strong>AI Features:</strong> Natural language chat, ML predictions, and automated insights</p>
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
        "src.main:app",
        host="0.0.0.0",
        port=6001,
        reload=True,
        log_level="info"
    )