#!/bin/bash

# Trading System Health Monitor
# Continuous monitoring for signal locks and position discrepancies
# Run in background to prevent trading issues

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🏥 Trading System Health Monitor"
echo "==============================="
echo "Started at: $(date)"
echo "Project: $PROJECT_ROOT"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Configuration
CHECK_INTERVAL=300  # 5 minutes
POSITION_CHECK_INTERVAL=1800  # 30 minutes
LOG_FILE="$PROJECT_ROOT/logs/health_monitor.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check signal locks
check_signal_locks() {
    log_message "🔍 Checking for signal confirmation locks..."
    
    cd "$PROJECT_ROOT"
    result=$(python scripts/fix_signal_locks.py --check 2>&1)
    
    if echo "$result" | grep -q "Found.*stuck signal"; then
        lock_count=$(echo "$result" | grep -o '[0-9]\+' | head -1)
        log_message "🚨 ALERT: Found $lock_count signal lock(s)!"
        
        # Auto-fix if locks detected
        log_message "🔧 Auto-fixing signal locks..."
        fix_result=$(python scripts/fix_signal_locks.py --fix 2>&1)
        log_message "Fix result: $fix_result"
        
        # Send notification (if notification system available)
        if command -v osascript >/dev/null 2>&1; then
            osascript -e "display notification \"Fixed $lock_count signal locks\" with title \"Trading Bot Alert\""
        fi
    else
        log_message "✅ No signal locks detected"
    fi
}

# Function to check position discrepancies
check_position_discrepancies() {
    log_message "💰 Checking position discrepancies..."
    
    cd "$PROJECT_ROOT"
    result=$(bash scripts/position-reconcile.sh check 2>&1)
    
    if echo "$result" | grep -q "Found [1-9]"; then
        discrepancy_count=$(echo "$result" | grep -o 'Found [0-9]\+' | grep -o '[0-9]\+')
        log_message "⚠️  ALERT: Found $discrepancy_count position discrepancies!"
        
        # Check if any discrepancy is >20%
        if echo "$result" | grep -q "([2-9][0-9]\|[0-9][0-9][0-9])"; then
            log_message "🚨 CRITICAL: Large position discrepancy detected (>20%)"
            
            # Auto-fix critical discrepancies
            log_message "🔧 Auto-fixing position discrepancies..."
            fix_result=$(bash scripts/position-reconcile.sh fix 2>&1)
            log_message "Position fix result: $fix_result"
            
            # Send critical notification
            if command -v osascript >/dev/null 2>&1; then
                osascript -e "display notification \"Critical position discrepancy fixed\" with title \"Trading Bot CRITICAL\""
            fi
        else
            log_message "ℹ️  Minor discrepancies detected, monitoring..."
        fi
    else
        log_message "✅ All positions accurate"
    fi
}

# Function to check system health
check_system_health() {
    log_message "🔧 Checking system health..."
    
    # Check if API is responding
    if curl -s -f "http://localhost:8000/health" >/dev/null; then
        log_message "✅ API server responding"
    else
        log_message "❌ API server not responding!"
        return 1
    fi
    
    # Check for recent rate limiting errors
    error_count=$(curl -s "http://localhost:8000/api/v1/system-errors/errors" 2>/dev/null | jq -r 'map(select(.error_type == "market_data" and .details.error_type == "rate_limit_429")) | length' 2>/dev/null || echo "0")
    
    if [ "$error_count" -gt 10 ]; then
        log_message "⚠️  High rate limiting errors detected: $error_count recent 429 errors"
    else
        log_message "✅ Rate limiting under control ($error_count recent errors)"
    fi
    
    # Check bot readiness
    blocked_bots=$(curl -s "http://localhost:8000/api/v1/bots/status/enhanced" 2>/dev/null | jq -r 'map(select(.trade_readiness.can_trade == false)) | length' 2>/dev/null || echo "0")
    
    if [ "$blocked_bots" -gt 0 ]; then
        log_message "⚠️  $blocked_bots bot(s) blocked from trading"
    else
        log_message "✅ All bots ready for trading"
    fi
}

# Function to cleanup old logs
cleanup_logs() {
    # Keep last 7 days of logs
    find "$PROJECT_ROOT/logs" -name "health_monitor.log.*" -mtime +7 -delete 2>/dev/null || true
}

# Trap Ctrl+C
trap 'log_message "👋 Health monitoring stopped"; exit 0' INT

# Main monitoring loop
last_position_check=0
loop_count=0

while true; do
    current_time=$(date +%s)
    
    # Always check signal locks
    check_signal_locks
    
    # Check system health every loop
    check_system_health
    
    # Check positions every 30 minutes
    if [ $((current_time - last_position_check)) -ge $POSITION_CHECK_INTERVAL ]; then
        check_position_discrepancies
        last_position_check=$current_time
    fi
    
    # Cleanup logs daily
    if [ $((loop_count % 288)) -eq 0 ]; then  # 288 * 5min = 24 hours
        cleanup_logs
    fi
    
    loop_count=$((loop_count + 1))
    
    log_message "😴 Sleeping for $((CHECK_INTERVAL / 60)) minutes..."
    sleep $CHECK_INTERVAL
done
