#!/bin/bash

# Fantasy Football Assistant - Dependency Checker
# This script checks all required dependencies for the project

echo "🏈 Fantasy Football Assistant - Dependency Checker"
echo "=================================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Node.js
echo -e "\n📦 Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "  Install from: https://nodejs.org/"
fi

# Check npm
echo -e "\n📦 Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm installed: $NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm not found${NC}"
fi

# Check Python
echo -e "\n🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
fi

# Check Python packages
echo -e "\n🐍 Checking Python packages..."
PYTHON_PACKAGES=(
    "fastapi"
    "uvicorn"
    "python-socketio"
    "websockets"
    "sqlalchemy"
    "httpx"
    "pandas"
    "numpy"
)

MISSING_PYTHON=()
for package in "${PYTHON_PACKAGES[@]}"; do
    if python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo -e "  ${GREEN}✓ $package${NC}"
    else
        echo -e "  ${RED}✗ $package${NC}"
        MISSING_PYTHON+=($package)
    fi
done

# Check frontend dependencies
echo -e "\n🎨 Checking frontend dependencies..."
FRONTEND_DIR="$(dirname "$0")/../frontend"

if [ -f "$FRONTEND_DIR/package.json" ]; then
    if [ -d "$FRONTEND_DIR/node_modules" ]; then
        # Check specific packages
        FRONTEND_PACKAGES=(
            "react"
            "socket.io-client"
            "@tanstack/react-query"
            "axios"
            "tailwindcss"
        )
        
        echo "  Checking critical packages:"
        MISSING_FRONTEND=()
        for package in "${FRONTEND_PACKAGES[@]}"; do
            if [ -d "$FRONTEND_DIR/node_modules/$package" ]; then
                echo -e "  ${GREEN}✓ $package${NC}"
            else
                echo -e "  ${RED}✗ $package${NC}"
                MISSING_FRONTEND+=($package)
            fi
        done
    else
        echo -e "  ${RED}✗ node_modules not found${NC}"
        echo -e "  ${YELLOW}Run: cd frontend && npm install${NC}"
    fi
else
    echo -e "  ${RED}✗ package.json not found${NC}"
fi

# Check ESPN service (optional)
echo -e "\n🏈 Checking ESPN service (optional)..."
ESPN_DIR="$(dirname "$0")/../espn-service"

if [ -f "$ESPN_DIR/package.json" ]; then
    if [ -d "$ESPN_DIR/node_modules" ]; then
        echo -e "  ${GREEN}✓ ESPN service dependencies installed${NC}"
    else
        echo -e "  ${YELLOW}⚠ ESPN service found but dependencies not installed${NC}"
        echo -e "  ${YELLOW}Run: cd espn-service && npm install${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ ESPN service not found (optional)${NC}"
fi

# Summary
echo -e "\n📊 Summary"
echo "=========="

if [ ${#MISSING_PYTHON[@]} -eq 0 ] && [ ${#MISSING_FRONTEND[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All dependencies are installed!${NC}"
    echo -e "\nYou can start the application with:"
    echo "  python3 scripts/start_with_websockets.py"
else
    echo -e "${RED}❌ Some dependencies are missing${NC}"
    
    if [ ${#MISSING_PYTHON[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}To install missing Python packages:${NC}"
        echo "  pip install ${MISSING_PYTHON[*]}"
    fi
    
    if [ ${#MISSING_FRONTEND[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}To install missing frontend packages:${NC}"
        echo "  cd frontend && npm install"
        
        # Check npm permissions
        if [ -d "$HOME/.npm" ]; then
            NPM_OWNER=$(stat -f '%Su' "$HOME/.npm" 2>/dev/null || stat -c '%U' "$HOME/.npm" 2>/dev/null)
            CURRENT_USER=$(whoami)
            if [ "$NPM_OWNER" != "$CURRENT_USER" ]; then
                echo -e "\n${YELLOW}⚠️  npm cache has incorrect permissions${NC}"
                echo "  Fix with: sudo chown -R $(whoami) ~/.npm"
            fi
        fi
    fi
fi

echo -e "\n🔧 WebSocket Features Status:"
if [[ " ${MISSING_FRONTEND[@]} " =~ " socket.io-client " ]]; then
    echo -e "${RED}✗ WebSocket support not available (socket.io-client missing)${NC}"
else
    echo -e "${GREEN}✓ WebSocket support available${NC}"
    echo "  - Real-time draft updates"
    echo "  - Instant pick notifications"
    echo "  - Live connection status"
fi