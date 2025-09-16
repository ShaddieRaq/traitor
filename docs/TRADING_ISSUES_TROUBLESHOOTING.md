# 🚨 Trading Issues Troubleshooting Guide

**Last Updated**: September 16, 2025  
**Purpose**: Comprehensive troubleshooting for common trading blockages and system issues

## � **Real-time Monitoring & UI Integration**

### **Enhanced System Health Panel**
The frontend now includes comprehensive real-time monitoring:

**Features:**
- **Overview Tab**: Active errors and recent critical events
- **Live Logs Tab**: Real-time log streaming from all services
- **Health Status Tab**: Service status and bot health monitoring
- **Auto-refresh**: Updates every 5-15 seconds automatically

**API Endpoints:**
```bash
# Comprehensive health summary
curl "http://localhost:8000/api/v1/health/comprehensive" | jq '.'

# Live log streaming
curl "http://localhost:8000/api/v1/health/logs?log_file=backend.log&lines=50" | jq '.'

# Critical events from last hour
curl "http://localhost:8000/api/v1/health/critical-events?minutes=60" | jq '.'

# Monitoring system status
curl "http://localhost:8000/api/v1/health/monitoring-status" | jq '.'
```

**Visual Indicators:**
- 🎉 **All Systems Operational** (Green) - No issues detected
- ⚠️ **Degraded** (Yellow) - Some issues but system functional  
- 🚨 **Critical** (Red) - Major issues requiring attention
- �🔍 **Monitoring Active** badge when health_monitor.sh is running

### **Background Health Monitoring**
Run continuous monitoring to catch issues before they impact trading:

```bash
# Start background monitoring (recommended)
./scripts/health_monitor.sh &

# Monitor will:
# - Check signal locks every 5 minutes
# - Check position discrepancies every 30 minutes  
# - Auto-fix critical issues
# - Send macOS notifications for alerts
# - Log all activity to logs/health_monitor.log
```

---

## 🔍 Quick Diagnosis Commands

### System Health Check
```bash
# Overall system status
./scripts/status.sh

# Enhanced health monitoring (NEW)
curl -s "http://localhost:8000/api/v1/health/comprehensive" | jq '.overall_status, .health_score'

# Check bot states and temperatures
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | jq '.[] | {name, status, temperature, trade_readiness}'

# Check for system errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'
```

### Trading Activity Check
```bash
# Check for pending orders blocking new trades
curl -s "http://localhost:8000/api/v1/trades/pending" | jq '.total_pending_orders'

# Check recent trading activity
curl -s "http://localhost:8000/api/v1/raw-trades/stats" | jq '.'

# Check position discrepancies
bash scripts/position-reconcile.sh check
```

## 🚨 **Issue 1: Signal Confirmation State Locks**

### **Symptoms**
- Bots showing "blocked" or "confirmation in progress" for extended periods
- API shows different signal scores than database
- No new trades opening despite HOT/WARM temperatures
- Logs showing "Another trade in progress" errors

### **Root Cause**
Signal confirmation state gets stuck when:
- Race conditions during trade execution
- Failed trades don't properly clear confirmation state
- System restarts during confirmation periods

### **Diagnosis**
```bash
# Check for stuck signal confirmations
python scripts/fix_signal_locks.py --check

# Manual database check
cd backend && python -c "
from app.core.database import get_db
from app.models.models import Bot
db = next(get_db())
bots = db.query(Bot).filter(Bot.signal_confirmation_start.isnot(None)).all()
for bot in bots:
    print(f'Bot {bot.id} ({bot.name}): confirmation_start={bot.signal_confirmation_start}')
db.close()
"
```

### **Solutions**

#### **Automatic Fix (Recommended)**
```bash
# Fix all detected signal locks
python scripts/fix_signal_locks.py --fix

# Start continuous monitoring (prevents future locks)
python scripts/fix_signal_locks.py --monitor
```

#### **Manual Fix**
```bash
# Clear specific bot's signal lock (replace BOT_ID)
cd backend && python -c "
from app.core.database import get_db
from app.models.models import Bot
db = next(get_db())
bot = db.query(Bot).filter(Bot.id == BOT_ID).first()
if bot:
    bot.signal_confirmation_start = None
    bot.current_combined_score = 0.0
    db.commit()
    print(f'✅ Cleared signal lock for bot {bot.id}')
db.close()
"
```

### **Prevention**
- Run `python scripts/fix_signal_locks.py --monitor` in background
- Include signal lock check in regular health monitoring
- Restart system if multiple locks detected

---

## 💰 **Issue 2: Position Tracking Discrepancies**

### **Symptoms**
- Bot dashboard shows incorrect position values
- P&L calculations seem wrong
- Position sizes don't match Coinbase holdings
- Large discrepancies between tracked vs actual positions

### **Root Cause**
Position tracking becomes inaccurate due to:
- Failed trade synchronization with Coinbase
- Race conditions in position updates
- Historical data migration issues
- Manual trades outside the system

### **Diagnosis**
```bash
# Check position discrepancies
bash scripts/position-reconcile.sh check

# Check raw trade data integrity
curl -s "http://localhost:8000/api/v1/raw-trades/pnl-by-product" | jq '.'
```

### **Solutions**

#### **Automatic Fix (Recommended)**
```bash
# Fix all position discrepancies
bash scripts/position-reconcile.sh fix
```

#### **Manual Investigation**
```bash
# Check specific bot position details
curl -s "http://localhost:8000/api/v1/trades/position/BOT_ID" | jq '.'

# Compare with Coinbase raw data
curl -s "http://localhost:8000/api/v1/raw-trades/?product_id=PAIR-USD" | jq '.[0:5]'
```

### **Prevention**
- Run position reconciliation weekly: `bash scripts/position-reconcile.sh check`
- Monitor for large discrepancies (>10%)
- Include in automated health checks

---

## 🔄 **Issue 3: Rate Limiting (429 Errors)**

### **Symptoms**
- Frequent "429 Too Many Requests" errors in logs
- Market data fetch failures
- Reduced trading frequency
- Bot evaluations failing

### **Root Cause**
- Failed WebSocket implementation forcing REST API usage
- Too many concurrent API requests
- Inefficient data fetching patterns

### **Current Mitigation**
```bash
# Check rate limiting errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq '.[] | select(.details.error_type == "rate_limit_429")'

# Monitor API usage patterns
tail -f logs/backend.log | grep "429"
```

### **Temporary Solutions**
- Increase delays between API calls
- Reduce bot evaluation frequency
- Cache market data more aggressively

### **Long-term Fix**
- Implement proper WebSocket connection for market data
- Reduce REST API dependency
- Add intelligent request spacing

---

## 🏦 **Issue 4: Insufficient Balance Errors**

### **Symptoms**
- "Insufficient balance" errors despite having funds
- Trades blocked by balance checks
- Inconsistent balance reporting

### **Diagnosis**
```bash
# Check current account balances
curl -s "http://localhost:8000/api/v1/raw-trades/stats" | jq '.'

# Check specific bot's balance requirements
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | jq '.[] | select(.trade_readiness.status == "blocked") | {name, blocking_reason}'
```

### **Solutions**
- Verify actual Coinbase account balances
- Check for locked/pending funds
- Reduce position sizes if necessary
- Ensure sufficient USD balance for new positions

---

## 🛠️ **Emergency Recovery Procedures**

### **Complete System Reset**
```bash
# Stop all services
./scripts/stop.sh

# Clear stuck states (if system is completely locked)
cd backend && python -c "
from app.core.database import get_db
from app.models.models import Bot
db = next(get_db())
db.query(Bot).update({Bot.signal_confirmation_start: None, Bot.current_combined_score: 0.0})
db.commit()
print('✅ Cleared all signal confirmation states')
db.close()
"

# Restart system
./scripts/start.sh

# Verify operation
./scripts/status.sh
```

### **Force Position Sync**
```bash
# Force sync all positions
bash scripts/position-reconcile.sh fix

# Verify sync worked
bash scripts/position-reconcile.sh check
```

## 📊 **Real-Time Monitoring & UI Integration**

### **Enhanced System Health Panel**
The trading dashboard now includes comprehensive real-time monitoring:

**UI Location**: Main trading dashboard → "Enhanced System Health" panel  
**Update Frequency**: 5-second polling via TanStack Query

**Available Tabs:**
1. **Overview**: Health score, critical alerts, system status summary
2. **Live Logs**: Real-time application log streaming (last 100 lines)  
3. **Monitoring**: Background task status and performance metrics

**Key Features:**
- Automatic log updates without page refresh
- Color-coded health indicators (🔥🌡️❄️🧊)
- Critical event highlighting
- Real-time bot status tracking

### **Health Monitoring API Endpoints**
```bash
# Comprehensive health summary
curl "http://localhost:8000/api/v1/health-monitoring/health" | jq

# Recent application logs (last 100 lines)
curl "http://localhost:8000/api/v1/health-monitoring/logs" | jq

# Critical events only  
curl "http://localhost:8000/api/v1/health-monitoring/critical-events" | jq
```

### **Background Health Monitoring**
```bash
# Start continuous monitoring (recommended for production)
nohup ./scripts/health_monitor.sh > /dev/null 2>&1 &

# Monitor in foreground for debugging
./scripts/health_monitor.sh

# Check monitoring status
ps aux | grep health_monitor
```

**Monitoring Features:**
- 5-minute health check intervals
- Automatic signal lock detection and clearing
- Position discrepancy alerts with auto-correction
- macOS desktop notifications for critical issues
- Comprehensive logging to `logs/health_monitor.log`

---

## 📊 **Monitoring & Prevention**

### **Daily Health Checks**
```bash
# Add to cron or run daily
#!/bin/bash
echo "🏥 Daily Trading System Health Check - $(date)"

# NEW: Enhanced health check
curl -s "http://localhost:8000/api/v1/health/comprehensive" | jq '.overall_status, .health_score, .monitoring_active'

# Check for signal locks
python scripts/fix_signal_locks.py --check

# Check position accuracy  
bash scripts/position-reconcile.sh check

# Check system errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'

# Check trading activity
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | jq '.[] | select(.trade_readiness.can_trade == false) | {name, blocking_reason}'
```

### **Automated Monitoring**
- Run signal lock monitoring: `python scripts/fix_signal_locks.py --monitor`
- Run health monitoring: `./scripts/health_monitor.sh` (background recommended)
- Set up alerts for position discrepancies >10%
- Monitor rate limiting error frequency
- Track daily trading volume vs expectations
- **NEW**: Real-time dashboard monitoring in UI (http://localhost:3000)

---

## 📞 **Support & Additional Resources**

### **Key Log Files**
- `/logs/backend.log` - API and bot evaluation logs
- `/logs/celery-worker.log` - Background task execution
- `/logs/celery-beat.log` - Scheduled task execution

### **Critical API Endpoints**
- `/api/v1/bots/status/enhanced` - Real-time bot status
- `/api/v1/system-errors/errors` - System error tracking  
- `/api/v1/trades/pending` - Stuck order detection
- `/api/v1/raw-trades/stats` - Trading statistics

### **Useful Scripts**
- `./scripts/status.sh` - Complete system health
- `./scripts/test-workflow.sh` - Full system validation
- `./scripts/quick-test.sh` - Rapid development testing
- `python scripts/fix_signal_locks.py` - Signal lock management
- `bash scripts/position-reconcile.sh` - Position accuracy

---

*This guide covers the most common trading issues. For system architecture details, see `/docs/COMPREHENSIVE_CODEBASE_ANALYSIS.md`*
