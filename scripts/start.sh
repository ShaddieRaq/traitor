#!/bin/bash

# Trading Bot Startup Script
# This script starts all services in the correct order

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

echo -e "${BLUE}🚀 Starting Trading Bot Application...${NC}"
echo -e "${BLUE}Project Root: ${PROJECT_ROOT}${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for ${service_name} to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ${service_name} is ready!${NC}"
            return 0
        fi
        
        echo -e "   Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ ${service_name} failed to start after $max_attempts attempts${NC}"
    return 1
}

# Step 1: Start Redis
echo -e "\n${BLUE}📦 Starting Redis...${NC}"
cd "$PROJECT_ROOT"
if docker-compose up redis -d; then
    echo -e "${GREEN}✅ Redis started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start Redis${NC}"
    exit 1
fi

# Wait a moment for Redis to be fully ready
sleep 3

# Step 2: Start FastAPI Backend
echo -e "\n${BLUE}🐍 Starting FastAPI Backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup.sh first.${NC}"
    exit 1
fi

# Start backend in background
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✅ FastAPI Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8000/health" "FastAPI Backend"; then
    echo -e "${RED}❌ Backend failed to start properly${NC}"
    exit 1
fi

# Step 3: Start React Frontend
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Start frontend in background
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo -e "${GREEN}✅ React Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
if ! wait_for_service "http://localhost:3000" "React Frontend"; then
    echo -e "${RED}❌ Frontend failed to start properly${NC}"
    exit 1
fi

# Step 4: Start Celery Worker
echo -e "\n${BLUE}👷 Starting Celery Worker (single process)...${NC}"
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
nohup celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1 > ../logs/celery-worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > ../logs/celery-worker.pid
echo -e "${GREEN}✅ Celery Worker started (PID: $WORKER_PID)${NC}"

# Step 5: Start Celery Beat
echo -e "\n${BLUE}⏰ Starting Celery Beat Scheduler...${NC}"
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
nohup celery -A app.tasks.celery_app beat --loglevel=info > ../logs/celery-beat.log 2>&1 &
BEAT_PID=$!
echo $BEAT_PID > ../logs/celery-beat.pid
echo -e "${GREEN}✅ Celery Beat started (PID: $BEAT_PID)${NC}"

# Final verification
echo -e "\n${BLUE}🔍 Final Health Check...${NC}"
sleep 5

# Check all services
echo -e "\n${BLUE}📊 Service Status:${NC}"
if check_port 6379; then
    echo -e "   Redis (6379): ${GREEN}✅ Running${NC}"
else
    echo -e "   Redis (6379): ${RED}❌ Not responding${NC}"
fi

if check_port 8000; then
    echo -e "   Backend (8000): ${GREEN}✅ Running${NC}"
else
    echo -e "   Backend (8000): ${RED}❌ Not responding${NC}"
fi

if check_port 3000; then
    echo -e "   Frontend (3000): ${GREEN}✅ Running${NC}"
else
    echo -e "   Frontend (3000): ${RED}❌ Not responding${NC}"
fi

# Test API endpoints
echo -e "\n${BLUE}🧪 Testing API Endpoints:${NC}"
if curl -s -f "http://localhost:8000/health" > /dev/null; then
    echo -e "   Health Check: ${GREEN}✅ OK${NC}"
else
    echo -e "   Health Check: ${RED}❌ Failed${NC}"
fi

if curl -s -f "http://localhost:8000/api/v1/bots/" > /dev/null; then
    echo -e "   Bots API: ${GREEN}✅ OK${NC}"
else
    echo -e "   Bots API: ${RED}❌ Failed${NC}"
fi

echo -e "\n${GREEN}🎉 Trading Bot Application Started Successfully!${NC}"
echo -e "\n${BLUE}📱 Access Points:${NC}"
echo -e "   🌐 Frontend Dashboard: ${YELLOW}http://localhost:3000${NC}"
echo -e "   📚 API Documentation: ${YELLOW}http://localhost:8000/api/docs${NC}"
echo -e "   📖 ReDoc Documentation: ${YELLOW}http://localhost:8000/api/redoc${NC}"
echo -e "\n${BLUE}📝 Logs Location: ${PROJECT_ROOT}/logs/${NC}"
echo -e "\n${BLUE}🛑 To stop all services, run: ${YELLOW}./scripts/stop.sh${NC}"
