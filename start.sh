#!/bin/bash

# Fantasy Football Assistant Startup Script

set -e

echo "🏈 Starting Fantasy Football Assistant..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Please run this script from the fantasy-football-assistant directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "requirements.txt" ]; then
    echo "⚠️  requirements.txt not found, creating basic requirements..."
    cat > requirements.txt << EOF
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
httpx>=0.25.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
EOF
fi

# Install/update Python dependencies
echo "📦 Installing/updating Python dependencies..."
pip install -r requirements.txt

# Check Node.js installation
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js version: $NODE_VERSION"
    
    # Install ESPN service dependencies if needed
    if [ -d "espn-service" ] && [ ! -d "espn-service/node_modules" ]; then
        echo "📦 Installing ESPN service dependencies..."
        cd espn-service
        npm install
        cd ..
    fi
    
    # Install Frontend dependencies if needed
    if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
        echo "📦 Installing Frontend dependencies..."
        cd frontend
        npm install
        cd ..
    fi
    
    echo "✓ ESPN service dependencies ready"
    echo "✓ Frontend dependencies ready"
else
    echo "⚠️  Node.js not found. ESPN service and Frontend will not be available."
    echo "   Install Node.js 18+ to enable ESPN Fantasy integration and Frontend."
fi

# Check environment configuration
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env file from .env.example..."
        cp .env.example .env
        echo "   Please edit .env file with your configuration"
    else
        echo "📝 Creating basic .env file..."
        cat > .env << EOF
# Fantasy Football Assistant Configuration
APP_NAME="Fantasy Football Assistant"
SECRET_KEY="change-this-in-production"
DATABASE_URL="sqlite:///./fantasy_football.db"
LOG_LEVEL="INFO"

# ESPN Service Configuration
ESPN_SERVICE_URL="http://localhost:3001"
ESPN_COOKIE_S2=""
ESPN_COOKIE_SWID=""
EOF
        echo "   Basic .env file created. Edit as needed."
    fi
fi

# Create logs directory
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill frontend dev server if running
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f 'vite' 2>/dev/null || true
    pkill -f 'uvicorn.*main:app' 2>/dev/null || true
    
    echo "✓ All services stopped"
    exit 0
}

# Set up trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check if ports are available
check_port() {
    local port=$1
    local service=$2
    
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "❌ Port $port is already in use (needed for $service)."
            echo "   You can try: lsof -ti:$port | xargs kill -9"
            return 1
        fi
    fi
    
    echo "✓ Port $port is available for $service"
    return 0
}

# Check all required ports
echo ""
echo "🔍 Checking port availability..."
check_port 6001 "Main API" || exit 1
check_port 3001 "ESPN Service" || exit 1
check_port 5173 "Frontend" || exit 1

# Start Frontend if available
if [ -d "frontend" ] && command -v node &> /dev/null; then
    echo ""
    echo "🎨 Starting Frontend development server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "   Frontend starting on http://localhost:5173"
    
    # Give frontend time to start
    sleep 2
fi

# Start the application
echo ""
echo "🚀 Starting Fantasy Football Assistant..."
echo ""
echo "   📊 Main API: http://localhost:6001"
echo "   📚 API Docs: http://localhost:6001/docs"
echo "   🔐 ESPN Login: http://localhost:6001/static/espn-login.html"
if command -v node &> /dev/null; then
    echo "   🏈 ESPN Service: http://localhost:3001 (auto-started)"
fi
if [ -d "frontend" ] && command -v node &> /dev/null; then
    echo "   🎨 Frontend: http://localhost:5173"
fi
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start the FastAPI application (which will auto-start ESPN service)
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 6001 --reload