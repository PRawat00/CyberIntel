#!/bin/bash

# SecureChat - Simple Start Script
# Uses your existing venv and setup

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit ${1:-0}
}

trap cleanup SIGINT SIGTERM

echo -e "${BLUE}Starting SecureChat...${NC}"
echo ""

# Check if venv exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo -e "${YELLOW}Create it with: python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$PROJECT_ROOT/frontend" ]; then
    echo -e "${RED}Error: Frontend directory not found${NC}"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd "$PROJECT_ROOT/frontend"
    npm install --silent
    cd "$PROJECT_ROOT"
fi

# Activate venv
cd "$PROJECT_ROOT"
source venv/bin/activate

# Check if Python dependencies are installed
if ! python -c "import numpy" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q -r requirements.txt
fi

# Start API
python -m api.main > /tmp/securechat-api.log 2>&1 &
API_PID=$!

echo -e "${YELLOW}Waiting for API...${NC}"
sleep 4

# Check API
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}API failed to start. Recent logs:${NC}"
    tail -20 /tmp/securechat-api.log
    cleanup 1
fi

echo -e "${GREEN}✓ API running (PID: $API_PID)${NC}"

# Start Frontend
cd "$PROJECT_ROOT/frontend"
npm run dev > /tmp/securechat-frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${YELLOW}Waiting for frontend...${NC}"
sleep 5

# Check frontend
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${RED}Frontend failed to start. Recent logs:${NC}"
    tail -20 /tmp/securechat-frontend.log
    cleanup 1
fi

echo -e "${GREEN}✓ Frontend running (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SecureChat Ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}Frontend:  http://localhost:3000${NC}"
echo -e "${BLUE}API:       http://localhost:8000${NC}"
echo -e "${BLUE}API Docs:  http://localhost:8000/api/docs${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  API:      tail -f /tmp/securechat-api.log"
echo -e "  Frontend: tail -f /tmp/securechat-frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open http://localhost:3000
fi

# Keep running
wait
