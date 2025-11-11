#!/bin/bash

# SecureChat - Stop Script
# Stops all running servers

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping SecureChat servers...${NC}"

# Stop API (running on port 8000)
API_PID=$(lsof -t -i:8000 2>/dev/null)
if [ ! -z "$API_PID" ]; then
    kill $API_PID
    echo -e "${GREEN}✓ Stopped API server (PID: $API_PID)${NC}"
else
    echo -e "${YELLOW}No API server running on port 8000${NC}"
fi

# Stop Frontend (running on port 3000)
FRONTEND_PID=$(lsof -t -i:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
    echo -e "${GREEN}✓ Stopped frontend server (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}No frontend server running on port 3000${NC}"
fi

# Clean up log files
rm -f /tmp/securechat-api.log /tmp/securechat-frontend.log
echo -e "${GREEN}✓ Cleaned up log files${NC}"

echo -e "${GREEN}All servers stopped!${NC}"
