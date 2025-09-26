#!/bin/bash

# Trading Bot Stop Script
# This script stops all services gracefully

set -e  # Exit on any error

# Add /usr/local/bin to PATH for Docker tools
export PATH="/usr/local/bin:$PATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🛑 Stopping Trading Bot Application...${NC}"

# Function to stop a service by PID file
stop_service_by_pid() {
    local service_name=$1
    local pid_file="$PROJECT_ROOT/logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}🔄 Stopping ${service_name} (PID: $pid)...${NC}"
            kill $pid
            
            # Wait for graceful shutdown
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Force killing ${service_name}...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ ${service_name} stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  ${service_name} was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for ${service_name}${NC}"
    fi
}

# Function to stop processes by pattern
stop_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    echo -e "${YELLOW}🔄 Stopping ${service_name}...${NC}"
    if pkill -f "$pattern" 2>/dev/null; then
        sleep 2
        echo -e "${GREEN}✅ ${service_name} stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  ${service_name} was not running${NC}"
    fi
}

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Stop Celery Beat Scheduler
stop_service_by_pid "celery-beat"

# Stop Celery Worker
stop_service_by_pid "celery-worker"

# Stop FastAPI Backend
stop_service_by_pid "backend"

# Stop React Frontend
stop_service_by_pid "frontend"

# Fallback: Stop any remaining processes by pattern
echo -e "\n${BLUE}🧹 Cleaning up any remaining processes...${NC}"
stop_by_pattern "uvicorn app.main:app" "FastAPI Backend (fallback)"
stop_by_pattern "celery.*app.tasks.celery_app" "Celery processes (fallback)"
stop_by_pattern "npm run dev" "React Frontend (fallback)"

# Stop Redis Docker container
echo -e "\n${BLUE}🐳 Stopping Redis Docker container...${NC}"
cd "$PROJECT_ROOT"
if docker-compose down; then
    echo -e "${GREEN}✅ Redis stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Redis was not running or failed to stop${NC}"
fi

# Clean up log files older than 7 days
echo -e "\n${BLUE}🧹 Cleaning up old log files...${NC}"
find "$PROJECT_ROOT/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Final verification
echo -e "\n${BLUE}🔍 Verifying all services are stopped...${NC}"
sleep 2

# Check ports
if ! lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "   Redis (6379): ${GREEN}✅ Stopped${NC}"
else
    echo -e "   Redis (6379): ${RED}❌ Still running${NC}"
fi

if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "   Backend (8000): ${GREEN}✅ Stopped${NC}"
else
    echo -e "   Backend (8000): ${RED}❌ Still running${NC}"
fi

if ! lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "   Frontend (3000): ${GREEN}✅ Stopped${NC}"
else
    echo -e "   Frontend (3000): ${RED}❌ Still running${NC}"
fi

echo -e "\n${GREEN}🎉 Trading Bot Application Stopped Successfully!${NC}"
echo -e "\n${BLUE}💡 To start the application again, run: ${YELLOW}./scripts/start.sh${NC}"
