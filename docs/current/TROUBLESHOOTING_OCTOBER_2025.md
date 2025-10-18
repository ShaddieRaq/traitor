# Troubleshooting Guide - October 2025

## Quick Reference

```bash
# System health check
./scripts/status.sh

# Check bot count (should be ~13)
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'

# Check for errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq

# Test API responsiveness
curl -s --max-time 5 "http://localhost:8000/health"
```

---

## Common Issues & Solutions

### 1. Bot Deletion Says "Liquidated" But No Coinbase Trade

**Symptoms**:
- Bot deleted successfully from UI
- Logs show "Total XYZ across 2 account(s): 295.258"
- Coinbase API responds: "INSUFFICIENT_FUND - Insufficient balance in source account"
- No trade appears in Coinbase order history

**Root Cause**: Coinbase has multiple accounts for the same currency (rare edge case). The API cannot automatically consolidate funds across accounts for a single order.

**Example Discovery** (October 14, 2025):
```bash
# XTZ had 2 separate accounts:
Account #1: 0.0 available + 0.058 on hold = 0.058 XTZ
Account #2: 295.2 available + 0.0 on hold = 295.2 XTZ
Total: 295.258 XTZ

# System correctly detected total but Coinbase rejected order
```

**Detection**:
```bash
# Check logs for multiple accounts
tail -50 logs/backend.log | grep "account #"

# Look for patterns like:
# "💰 XTZ account #1: 0.0 + 0.058127 = 0.058127"
# "💰 XTZ account #2: 295.2 + 0.0 = 295.2"
# "💰 Total XTZ across 2 account(s): 295.258127"
```

**Solutions**:

1. **Manual Consolidation in Coinbase**:
   - Go to Coinbase website/app
   - Find the currency with multiple accounts
   - Transfer holdings from secondary account to primary
   - Retry bot deletion

2. **Manual Sale in Coinbase**:
   - Sell holdings directly in Coinbase UI
   - Return to trading system
   - Delete bot without liquidation checkbox

3. **Wait for Future API Enhancement**:
   - This is a Coinbase API limitation
   - System working as designed
   - May be addressed in future Coinbase updates

**Prevention**:
- Check Coinbase account structure before creating bots
- Consolidate holdings into single accounts
- Rare edge case - most users won't encounter this

---

### 2. Market Analysis Page Hanging / API Not Responding

**Symptoms**:
- Frontend shows loading spinner indefinitely
- Health endpoint times out: `curl --max-time 3 "http://localhost:8000/health"` fails
- WebSocket price streaming still works
- Backend process visible in `ps aux` but not responding

**Root Cause**: Backend deadlock under load (investigation ongoing).

**Indicators**:
```bash
# Health check fails
curl --max-time 3 "http://localhost:8000/health"
# (no response, timeout)

# Process running but unresponsive
ps aux | grep uvicorn
# lazy_genius 88942 ... uvicorn app.main:app

# WebSocket still functioning
tail -f logs/backend.log | grep "💰.*USD:"
# (still seeing price updates)
```

**Solution**: Force restart backend
```bash
# Kill backend process
pkill -9 -f "uvicorn app.main:app" && sleep 2

# Restart backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

# Verify health
sleep 5 && curl -s "http://localhost:8000/health"
# Should return: {"status": "healthy"}
```

**Or use restart script**:
```bash
./scripts/stop.sh
./scripts/start.sh
./scripts/status.sh  # Verify recovery
```

**Frequency**: Observed twice during October 14-18 session (rare but recurring).

**Investigation Needed**:
- Heavy Celery task processing
- Database lock contention during bulk operations
- Memory pressure
- Async/await deadlock in FastAPI request handlers

**Prevention**:
- Monitor backend logs for warnings
- Use timeouts on all API calls
- Diagnose before restarting (check logs first)

---

### 3. Scan Script Crashes with KeyError

**Symptoms**:
```bash
python backend/scanforbreakout.py

# Output:
Breakouts detected: 0
After USD filter: N/A
KeyError: 'new_opportunities'
```

**Root Cause**: Scan failed but script expected success response structure.

**Fix Applied** (October 17, 2025):
Script now handles both success and error responses:

```python
# Check for error status first
if result.get('status') == 'error':
    print(f"❌ SCAN FAILED: {result.get('error', 'Unknown error')}")
    sys.exit(1)

# Success path with safe defaults
print(f"  Breakouts detected: {result.get('breakouts_detected', 0)}")
print(f"  New opportunities: {result.get('new_opportunities', 0)}")
```

**Solution**: Update to latest version of `backend/scanforbreakout.py`.

---

### 4. Auto-Created Bots Not Starting

**Symptoms**:
- Breakout scanner creates new bots
- Bots appear in UI with status "STOPPED"
- Requires manual "Start Bot" button click

**Status**: ✅ FIXED (October 16, 2025)

**Fix Applied**: Changed default bot status in `bot_creator.py`:
```python
# Before:
status="STOPPED",  # Start stopped, user can activate

# After:
status="RUNNING",  # Auto-start for breakout opportunities
```

**Impact**: Only affects NEW bots created after October 16, 2025.

**Verification**:
```bash
# Check for stopped breakout bots
curl -s "http://localhost:8000/api/v1/bots/" | \
  jq '[.[] | select(.trading_mode == "BREAKOUT" and .status == "STOPPED")] | length'

# Should return: 0
```

---

### 5. Balance Warning Shows "Need X Crypto" for Buy Signal

**Symptoms**:
- Bot shows strong BUY signal (score < -0.05)
- User has sufficient USD in account
- UI displays: "Balance Required: Need 10.5 XTZ to execute"

**Status**: ✅ FIXED (October 14, 2025)

**Root Cause**: UI was checking `trading_intent.next_action` instead of actual signal direction from score.

**Fix Applied** (`BotCardSamples.tsx`):
```typescript
// Calculate signal direction from score
const signalDirection = bot.current_combined_score < -0.05 ? 'buy' 
  : bot.current_combined_score > 0.05 ? 'sell' 
  : 'hold';

// Only show error when missing RELEVANT currency
if (signalDirection === 'buy' && blockingReason.includes('USD')) {
  return <span>Need ${bot.position_size_usd || 25} USD minimum</span>;
}
// Don't show crypto error for buy signals
return null;
```

**Verification**: Buy signals should only show USD balance requirements, not crypto.

---

## Diagnostic Commands

### System Health
```bash
# Full status check
./scripts/status.sh

# Quick health check
curl -s --max-time 3 "http://localhost:8000/health"

# Check services
docker ps | grep redis
ps aux | grep -E "uvicorn|celery"
```

### Bot Status
```bash
# Total bot count
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'

# Running bots
curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | select(.status == "RUNNING")] | length'

# Stopped bots
curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | select(.status == "STOPPED")] | length'

# Breakout mode bots
curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | select(.trading_mode == "BREAKOUT")] | length'
```

### Error Checking
```bash
# System errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:3]'

# Backend logs
tail -50 logs/backend.log | grep -i error
tail -50 logs/backend.log | grep -i "insufficient"

# WebSocket streaming
curl -s "http://localhost:8000/api/v1/websocket-prices/status" | jq
```

### Multi-Account Detection
```bash
# Check for multiple accounts per currency
tail -100 logs/backend.log | grep "account #"

# Look for Coinbase rejection
tail -100 logs/backend.log | grep "INSUFFICIENT_FUND"

# Full liquidation attempt
tail -100 logs/backend.log | grep -A 10 "EXECUTING REAL TRADE"
```

---

## Recovery Procedures

### Full System Restart
```bash
# Stop all services
./scripts/stop.sh

# Verify stopped
ps aux | grep -E "uvicorn|celery" | grep -v grep

# Start all services
./scripts/start.sh

# Verify health
./scripts/status.sh
```

### Backend Only Restart
```bash
# Stop backend
pkill -9 -f "uvicorn app.main:app"

# Restart
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

# Verify
sleep 5 && curl -s "http://localhost:8000/health"
```

### Celery Restart (for schedule changes)
```bash
# Stop Celery Beat
pkill -f "celery.*beat"

# Stop Celery Worker
pkill -f "celery.*worker"

# Restart Beat
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info > ../logs/celery-beat.log 2>&1 &

# Restart Worker
celery -A app.tasks.celery_app worker --loglevel=info > ../logs/celery-worker.log 2>&1 &
```

---

## Performance Monitoring

### Cache Performance
```bash
# Redis cache stats
curl -s "http://localhost:8000/api/v1/cache/stats" | jq

# WebSocket price cache
curl -s "http://localhost:8000/api/v1/websocket-prices/status" | jq
```

### Market Data Service
```bash
# Service stats
curl -s "http://localhost:8000/api/v1/market-data/stats" | jq

# Check batch fetching
tail -50 logs/celery-worker.log | grep "market_data"
```

### Recent Activity
```bash
# Recent price updates
tail -20 logs/backend.log | grep "💰.*USD:"

# Recent bot evaluations
tail -50 logs/celery-worker.log | grep "Evaluating bot"

# Recent trades
curl -s "http://localhost:8000/api/v1/raw-trades/recent?limit=5" | jq
```

---

## Known Limitations

### 1. Multi-Account Liquidation
- **Cannot**: Liquidate from multiple Coinbase accounts in one order
- **Workaround**: Manual consolidation or separate orders
- **Affects**: Rare edge case (e.g., XTZ with 2 accounts)

### 2. Backend Deadlocks
- **Cannot**: Prevent deadlocks completely (root cause unknown)
- **Workaround**: Force restart backend
- **Frequency**: Rare but recurring (2x in October 14-18)

### 3. Historical Trade Data
- **Cannot**: Use old `/api/v1/trades/` endpoints (removed October 5, 2025)
- **Workaround**: Use `/api/v1/raw-trades/` exclusively
- **Reason**: Trade table corrupted, RawTrade is source of truth

---

## Contact & Escalation

### When to Escalate
- Backend deadlocks more than once per day
- Multi-account liquidation affecting multiple users
- System errors persist after restart
- Data corruption detected

### Debugging Information to Collect
```bash
# System state
./scripts/status.sh > system_state.txt

# Recent logs
tail -200 logs/backend.log > backend_recent.txt
tail -100 logs/celery-worker.log > celery_recent.txt

# Bot status
curl -s "http://localhost:8000/api/v1/bots/" > bots.json

# System errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" > errors.json
```

---

**Last Updated**: October 18, 2025  
**System Version**: Production with Multi-Account Fix  
**Next Review**: As issues arise
