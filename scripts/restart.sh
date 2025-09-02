#!/bin/bash

# Trading Bot Restart Script
# This script stops and starts all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo -e "${BLUE}🔄 Restarting Trading Bot Application...${NC}"

# Stop all services
echo -e "\n${YELLOW}🛑 Stopping services...${NC}"
"$SCRIPT_DIR/stop.sh"

# Wait a moment
echo -e "\n${YELLOW}⏳ Waiting 5 seconds before restart...${NC}"
sleep 5

# Start all services
echo -e "\n${YELLOW}🚀 Starting services...${NC}"
"$SCRIPT_DIR/start.sh"

echo -e "\n${GREEN}🎉 Restart completed!${NC}"
