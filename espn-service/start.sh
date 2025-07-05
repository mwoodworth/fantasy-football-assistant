#!/bin/bash

# ESPN Fantasy Football Service Startup Script

set -e

echo "🏈 Starting ESPN Fantasy Football Service..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18.0.0 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if ! printf '%s\n%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V -C; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please install Node.js $REQUIRED_VERSION or higher."
    exit 1
fi

echo "✓ Node.js version: $NODE_VERSION"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Please run this script from the espn-service directory."
    exit 1
fi

# Check if node_modules exists, install if not
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✓ Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env file not found. Copying from .env.example..."
        cp .env.example .env
        echo "📝 Please edit .env file with your configuration before starting the service."
        echo "   Required: ESPN_COOKIE_S2, ESPN_COOKIE_SWID (for private leagues)"
        echo "   Optional: API_KEY (for authentication)"
        exit 1
    else
        echo "❌ .env file not found and .env.example is missing."
        exit 1
    fi
fi

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Check required environment variables for private leagues
if [ -z "$ESPN_COOKIE_S2" ] || [ -z "$ESPN_COOKIE_SWID" ]; then
    echo "⚠️  ESPN cookies not configured. Only public leagues will be accessible."
    echo "   To access private leagues, set ESPN_COOKIE_S2 and ESPN_COOKIE_SWID in .env"
fi

# Check if port is available
PORT=${PORT:-3001}
if command -v lsof &> /dev/null; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $PORT is already in use. Please stop the existing service or change the PORT in .env"
        exit 1
    fi
fi

echo "✓ Port $PORT is available"

# Start the service
echo "🚀 Starting ESPN Fantasy Football Service on port $PORT..."
echo "   Environment: ${NODE_ENV:-development}"
echo "   API Documentation: http://localhost:$PORT/api/docs"
echo "   Health Check: http://localhost:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start with appropriate script based on environment
if [ "${NODE_ENV:-development}" = "production" ]; then
    npm start
else
    npm run dev
fi