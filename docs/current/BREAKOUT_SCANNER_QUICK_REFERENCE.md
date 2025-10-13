# 🚀 Breakout Scanner Quick Reference

## Testing Commands

```bash
# Test scanner (scan-only, no bot creation)
python test_breakout_scanner.py

# Create bots for detected breakouts
python test_breakout_scanner.py --create

# Check existing breakout bots
sqlite3 trader.db "SELECT id, pair, trading_mode, stop_loss_pct, take_profit_pct, status FROM bots WHERE trading_mode='BREAKOUT';"

# Verify all bots
sqlite3 trader.db "SELECT id, pair, trading_mode FROM bots ORDER BY id;"
```

## Celery Task Usage

```python
# Manual scan from Python
from app.tasks.trading_tasks import scan_for_breakouts

# Scan only (no bot creation)
result = scan_for_breakouts(create_bots=False, min_confidence="MEDIUM")

# Scan and create bots
result = scan_for_breakouts(create_bots=True, min_confidence="HIGH")

# Result format:
{
    "breakouts_detected": 2,
    "bots_created": 2,
    "opportunities": [
        {
            "product_id": "TRAC-USD",
            "score": 80.1,
            "confidence": "HIGH",
            "price_change_24h": 44.0,
            "volume_change_24h": 201.1,
            "signals": ["STRONG_PUMP", "HUGE_VOLUME", "HIGH_LIQUIDITY"]
        }
    ]
}
```

## Detection Thresholds

```python
# Minimum criteria (ALL must pass)
MIN_PRICE_CHANGE = 15.0%        # At least +15% in 24h
MIN_VOLUME_CHANGE = 100.0%      # Volume doubled (2x)
MIN_VOLUME_USD = $500,000       # Minimum liquidity

# Scoring ranges
PRICE_MOMENTUM = 0-40 points    # More price change = more points
VOLUME_SPIKE = 0-30 points      # Bigger volume spike = more points
LIQUIDITY = 0-10 points         # Higher volume USD = more points
EXTREME_BONUS = 0-20 points     # +50% or +500% volume = bonus

# Confidence levels
HIGH:   score >= 70  → 8% stop-loss, 30% take-profit
MEDIUM: score >= 50  → 6% stop-loss, 20% take-profit
LOW:    score >= 30  → 5% stop-loss, 15% take-profit
```

## Bot Configuration Differences

```python
# CORE BOTS (long-term)
{
  "rsi": {"weight": 0.4, "period": 14, "buy": 30, "sell": 70},
  "moving_average": {"weight": 0.35, "fast": 50, "slow": 200},  # SLOW
  "macd": {"weight": 0.25, "fast": 12, "slow": 26}
}
exit_strategy = "signal_reversal"  # Wait for combined_score >= 0.05

# BREAKOUT BOTS (short-term)
{
  "rsi": {"weight": 0.5, "period": 14, "buy": 40, "sell": 65},
  "moving_average": {"weight": 0.3, "fast": 8, "slow": 20},  # FAST
  "macd": {"weight": 0.2, "fast": 12, "slow": 26}
}
exit_strategy = "take_profit_or_signal"  # Exit at 15-30% profit OR signal
```

## Monitoring

```bash
# Watch for breakouts in logs
tail -f logs/backend.log | grep "breakout"

# Check bot count by mode
sqlite3 trader.db "SELECT trading_mode, COUNT(*) FROM bots GROUP BY trading_mode;"

# View recent breakout bots
sqlite3 trader.db "SELECT id, pair, created_at, stop_loss_pct, take_profit_pct FROM bots WHERE trading_mode='BREAKOUT' ORDER BY created_at DESC LIMIT 10;"

# Check bot performance
sqlite3 trader.db "SELECT pair, last_trade_reason, current_combined_score FROM bots WHERE trading_mode='BREAKOUT';"
```

## Cleanup

```python
# Manual cleanup of stale breakout bots (older than 72 hours)
from app.services.bot_creator import cleanup_stale_breakout_bots
from app.core.database import SessionLocal

db = SessionLocal()
try:
    cleanup_stale_breakout_bots(db, max_age_hours=72)
    db.commit()
    print("✅ Cleanup complete")
finally:
    db.close()
```

## API Endpoints (TO BE IMPLEMENTED)

```bash
# Get current breakout opportunities
GET /api/v1/breakouts
Response: {
  "opportunities": [...],
  "count": 2,
  "last_scan": "2025-10-12T10:30:00Z"
}

# Trigger manual scan
POST /api/v1/breakouts/scan
Body: {"create_bots": false, "min_confidence": "MEDIUM"}
Response: {
  "breakouts_detected": 2,
  "bots_created": 0
}

# List breakout bots
GET /api/v1/bots/breakout
Response: {
  "bots": [...],
  "count": 2
}

# Create bot from opportunity
POST /api/v1/breakouts/create-bot
Body: {"product_id": "TRAC-USD", "initial_investment": 15.0}
```

## Deployment Steps

### 1. Logging-Only Validation (48 hours)
```python
# Add to celery.py beat_schedule:
'scan-for-breakouts': {
    'task': 'app.tasks.trading_tasks.scan_for_breakouts',
    'schedule': crontab(minute='*/5'),
    'args': (False, 'MEDIUM')  # create_bots=False
}

# Monitor:
tail -f logs/celery-worker.log | grep "breakout"
```

### 2. Enable Auto-Trading (After validation)
```python
# Change create_bots to True:
'scan-for-breakouts': {
    'task': 'app.tasks.trading_tasks.scan_for_breakouts',
    'schedule': crontab(minute='*/5'),
    'args': (True, 'MEDIUM')  # create_bots=True
}
```

### 3. Adjust Confidence Threshold
```python
# If too many bots created:
'args': (True, 'HIGH')  # Only HIGH confidence

# If too few bots:
'args': (True, 'LOW')   # Include LOW confidence
```

## Expected Behavior

### Scan Frequency
- Every 5 minutes (configurable via Celery Beat)
- ~300ms scan time for 807 products
- Creates 0-5 bots per scan (max limit)

### Bot Lifecycle
1. **Detection** - Breakout identified (score >= 30)
2. **Creation** - Bot auto-created with dynamic SL/TP
3. **Initial Status** - STOPPED (user must activate)
4. **Trading** - RUNNING (after user activation)
5. **Exit** - Take-profit hit OR stop-loss OR signal reversal
6. **Cleanup** - Auto-deleted after 72 hours if no position

### Performance Expectations
- **Detection quality**: 70%+ accuracy (validate during 48h)
- **Bot creation rate**: 2-10 bots per day
- **Win rate target**: 60%+ (aggressive exits)
- **Average hold time**: 6-48 hours

## Troubleshooting

### No breakouts detected
```python
# Lower thresholds temporarily for testing
MIN_PRICE_CHANGE = 10.0  # Was 15.0
MIN_VOLUME_CHANGE = 50.0  # Was 100.0
```

### Too many false positives
```python
# Raise minimum score
if breakout_score < 50:  # Was 30
    continue
```

### Bots not creating
```bash
# Check logs for errors
tail -f logs/backend.log | grep "ERROR"

# Verify database
sqlite3 trader.db "SELECT COUNT(*) FROM bots;"

# Test manually
python test_breakout_scanner.py --create
```

### Bot creation fails
```bash
# Check Coinbase API credentials
echo $COINBASE_API_KEY
echo $COINBASE_API_SECRET

# Verify database schema
sqlite3 trader.db "PRAGMA table_info(bots);" | grep trading_mode
```

## Files to Monitor

- `/logs/backend.log` - Breakout detection logs
- `/logs/celery-worker.log` - Celery task execution
- `/trader.db` - Bot storage (check trading_mode column)
- `/backend/app/services/breakout_detector.py` - Detection logic
- `/backend/app/services/bot_creator.py` - Bot creation logic
- `/backend/app/tasks/trading_tasks.py` - Celery tasks

## Key Metrics to Track

1. **Detection Accuracy** - % of detected breakouts that sustain momentum
2. **Bot Performance** - Win rate, avg profit, max loss
3. **Scan Efficiency** - Time per scan, API calls used
4. **Bot Count** - Active breakout bots vs CORE bots
5. **Lifecycle Stats** - Avg bot age, deletion rate

---

**Status**: ✅ System ready for 48-hour validation phase  
**Next Step**: Add Celery Beat schedule for automated scanning every 5 minutes
