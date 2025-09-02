#!/bin/bash

# Trading Bot Logs Script
# This script displays and manages log files

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_ROOT/logs"

# Function to show usage
show_usage() {
    echo -e "${BLUE}📝 Trading Bot Log Viewer${NC}"
    echo -e "${BLUE}========================${NC}"
    echo
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo
    echo "Services:"
    echo "  backend     - FastAPI backend logs"
    echo "  frontend    - React frontend logs"
    echo "  worker      - Celery worker logs"
    echo "  beat        - Celery beat scheduler logs"
    echo "  all         - All services (default)"
    echo
    echo "Options:"
    echo "  -f, --follow    Follow log output (like tail -f)"
    echo "  -n, --lines N   Show last N lines (default: 50)"
    echo "  -c, --clear     Clear all log files"
    echo "  -h, --help      Show this help"
    echo
    echo "Examples:"
    echo "  $0 backend              # Show last 50 lines of backend logs"
    echo "  $0 -f worker            # Follow worker logs"
    echo "  $0 -n 100 all          # Show last 100 lines of all logs"
    echo "  $0 --clear              # Clear all log files"
}

# Default values
FOLLOW=false
LINES=50
SERVICE="all"
CLEAR_LOGS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -c|--clear)
            CLEAR_LOGS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        backend|frontend|worker|beat|all)
            SERVICE="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Function to clear logs
clear_logs() {
    echo -e "${YELLOW}🧹 Clearing all log files...${NC}"
    rm -f "$LOGS_DIR"/*.log
    echo -e "${GREEN}✅ All log files cleared${NC}"
}

# Function to display a log file
show_log() {
    local service=$1
    local log_file="$LOGS_DIR/${service}.log"
    
    if [ ! -f "$log_file" ]; then
        echo -e "${YELLOW}⚠️  Log file not found: ${log_file}${NC}"
        return
    fi
    
    echo -e "${BLUE}📄 ${service} logs (last ${LINES} lines):${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..50})${NC}"
    
    if [ "$FOLLOW" = true ]; then
        tail -n "$LINES" -f "$log_file"
    else
        tail -n "$LINES" "$log_file"
    fi
    echo
}

# Function to show all logs
show_all_logs() {
    local services=("backend" "frontend" "celery-worker" "celery-beat")
    
    for service in "${services[@]}"; do
        show_log "$service"
    done
    
    if [ "$FOLLOW" = true ]; then
        echo -e "${BLUE}🔄 Following all logs (press Ctrl+C to stop)...${NC}"
        tail -n 0 -f "$LOGS_DIR"/*.log 2>/dev/null
    fi
}

# Main logic
if [ "$CLEAR_LOGS" = true ]; then
    clear_logs
    exit 0
fi

case $SERVICE in
    backend)
        show_log "backend"
        ;;
    frontend)
        show_log "frontend"
        ;;
    worker)
        show_log "celery-worker"
        ;;
    beat)
        show_log "celery-beat"
        ;;
    all)
        show_all_logs
        ;;
    *)
        echo -e "${RED}Unknown service: $SERVICE${NC}"
        show_usage
        exit 1
        ;;
esac
