#!/bin/bash

# Trading Bot Status Script
# This script checks the status of all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📊 Trading Bot Application Status${NC}"
echo -e "${BLUE}================================${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check service by PID file
check_service_by_pid() {
    local service_name=$1
    local pid_file="$PROJECT_ROOT/logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "   ${service_name}: ${GREEN}✅ Running (PID: $pid)${NC}"
            return 0
        else
            echo -e "   ${service_name}: ${RED}❌ PID file exists but process not running${NC}"
            return 1
        fi
    else
        echo -e "   ${service_name}: ${RED}❌ Not running (no PID file)${NC}"
        return 1
    fi
}

# Check Docker
echo -e "\n${BLUE}🐳 Docker Services:${NC}"
if command -v docker >/dev/null 2>&1; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "trader-redis"; then
        echo -e "   Redis Container: ${GREEN}✅ Running${NC}"
        docker ps --filter "name=trader-redis" --format "   └─ {{.Status}}"
    else
        echo -e "   Redis Container: ${RED}❌ Not running${NC}"
    fi
else
    echo -e "   Docker: ${RED}❌ Not installed${NC}"
fi

# Check Ports
echo -e "\n${BLUE}🔌 Port Status:${NC}"
if check_port 6379; then
    echo -e "   Redis (6379): ${GREEN}✅ Listening${NC}"
else
    echo -e "   Redis (6379): ${RED}❌ Not listening${NC}"
fi

if check_port 8000; then
    echo -e "   Backend (8000): ${GREEN}✅ Listening${NC}"
else
    echo -e "   Backend (8000): ${RED}❌ Not listening${NC}"
fi

if check_port 3000; then
    echo -e "   Frontend (3000): ${GREEN}✅ Listening${NC}"
else
    echo -e "   Frontend (3000): ${RED}❌ Not listening${NC}"
fi

# Check Services by PID
echo -e "\n${BLUE}🔧 Service Processes:${NC}"
check_service_by_pid "backend"
check_service_by_pid "frontend"
check_service_by_pid "celery-worker"
check_service_by_pid "celery-beat"

# Test API Endpoints
echo -e "\n${BLUE}🧪 API Health Checks:${NC}"
if curl -s -f "http://localhost:8000/health" >/dev/null 2>&1; then
    health_response=$(curl -s "http://localhost:8000/health")
    echo -e "   Health Endpoint: ${GREEN}✅ OK${NC}"
    echo -e "   └─ Response: ${health_response}"
else
    echo -e "   Health Endpoint: ${RED}❌ Failed${NC}"
fi

if curl -s -f "http://localhost:8000/api/v1/signals/" >/dev/null 2>&1; then
    signals_count=$(curl -s "http://localhost:8000/api/v1/signals/" | jq length 2>/dev/null || echo "unknown")
    echo -e "   Signals API: ${GREEN}✅ OK${NC}"
    echo -e "   └─ Signals count: ${signals_count}"
else
    echo -e "   Signals API: ${RED}❌ Failed${NC}"
fi

if curl -s -f "http://localhost:8000/api/v1/market/products" >/dev/null 2>&1; then
    echo -e "   Market Data API: ${GREEN}✅ OK${NC}"
    # Get first product as test
    first_product=$(curl -s "http://localhost:8000/api/v1/market/products" | jq -r '.products[0].product_id // "none"' 2>/dev/null || echo "unknown")
    echo -e "   └─ First product: ${first_product}"
else
    echo -e "   Market Data API: ${RED}❌ Failed${NC}"
fi

if curl -s -I "http://localhost:3000" >/dev/null 2>&1; then
    echo -e "   Frontend: ${GREEN}✅ OK${NC}"
else
    echo -e "   Frontend: ${RED}❌ Failed${NC}"
fi

# Check logs
echo -e "\n${BLUE}📝 Recent Log Activity:${NC}"
if [ -d "$PROJECT_ROOT/logs" ]; then
    for log_file in backend.log frontend.log celery-worker.log celery-beat.log; do
        if [ -f "$PROJECT_ROOT/logs/$log_file" ]; then
            last_line=$(tail -n 1 "$PROJECT_ROOT/logs/$log_file" 2>/dev/null)
            if [ -n "$last_line" ]; then
                echo -e "   ${log_file}: ${GREEN}✅ Active${NC}"
                echo -e "   └─ Last: $(echo "$last_line" | cut -c1-60)..."
            else
                echo -e "   ${log_file}: ${YELLOW}⚠️  Empty${NC}"
            fi
        else
            echo -e "   ${log_file}: ${RED}❌ Missing${NC}"
        fi
    done
else
    echo -e "   Log directory: ${RED}❌ Missing${NC}"
fi

# System Resources
echo -e "\n${BLUE}💻 System Resources:${NC}"
if command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2)
    echo -e "   Python: ${GREEN}✅ ${python_version}${NC}"
else
    echo -e "   Python: ${RED}❌ Not found${NC}"
fi

if command -v node >/dev/null 2>&1; then
    node_version=$(node --version 2>/dev/null)
    echo -e "   Node.js: ${GREEN}✅ ${node_version}${NC}"
else
    echo -e "   Node.js: ${RED}❌ Not found${NC}"
fi

# Memory usage
if command -v ps >/dev/null 2>&1; then
    total_memory=$(ps aux | grep -E "(uvicorn|celery|node.*dev)" | grep -v grep | awk '{sum += $4} END {printf "%.1f%%", sum}')
    echo -e "   Memory Usage: ${GREEN}${total_memory}${NC}"
fi

echo -e "\n${BLUE}🔗 Access Points:${NC}"
echo -e "   🌐 Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "   📚 API Docs: ${YELLOW}http://localhost:8000/api/docs${NC}"
echo -e "   📖 ReDoc: ${YELLOW}http://localhost:8000/api/redoc${NC}"

echo -e "\n${BLUE}🛠️  Management Commands:${NC}"
echo -e "   Start: ${YELLOW}./scripts/start.sh${NC}"
echo -e "   Stop: ${YELLOW}./scripts/stop.sh${NC}"
echo -e "   Restart: ${YELLOW}./scripts/restart.sh${NC}"
echo -e "   Logs: ${YELLOW}./scripts/logs.sh${NC}"
