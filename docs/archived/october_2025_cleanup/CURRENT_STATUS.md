# Current System Status

**Last Updated**: October 13, 2025 - 18:30 PM  
**Status**: 🟢 All Systems Operational

## 🎯 Today's Major Achievements

### 1. Real Capital System Deployed ✅
**Impact**: System now uses actual Coinbase USD balance instead of fake $500 limit  
**Status**: $14.42 available (need $15 for next bot)  
**Docs**: `docs/current/REAL_CAPITAL_SYSTEM.md`

### 2. USD-Only Trading Filter ✅
**Impact**: Breakout scanner only creates bots for -USD pairs (excludes USDC/USDT)  
**Status**: 18:03 scan filtered out 3 USDC pairs, kept 4 USD pairs  
**Docs**: `docs/current/USD_ONLY_FILTER.md`

### 3. P&L Monitoring Active ✅
**Impact**: Automatic stop loss (-5%) / take profit (+10%) every 10 minutes  
**Status**: 23 bots monitored at 18:26, 0 triggers  
**Docs**: Previous deployment

---

## Quick Health Check

```bash
# Run these commands to verify system status
./scripts/status.sh
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Should be 30
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'  # Should be 0
```

## System Services

```
✅ Backend (FastAPI): Running on port 8000
✅ Celery Worker: Running (concurrency: 1)
✅ Celery Beat: Running (scheduler active)
✅ Redis: Connected (97.5% cache hit rate)
✅ WebSocket: Streaming prices
✅ Database: /trader.db (30 active bots)
```

## Current Trading State

### Capital
- **Available**: $14.42 USD
- **Needed**: $15.00 per bot
- **Gap**: $0.58 short
- **Strategy**: Scalping (fast capital turnover)

### Active Bots
- **Count**: 30 bots
- **Status**: RUNNING
- **Pairs**: All USD-quoted (USDC/USDT excluded)
- **Signals**: Learning-optimized weights

### Breakout Scanner
- **Frequency**: Every 2 hours
- **Last scan**: 18:03 PM
- **Filter**: USD pairs only
- **Next scan**: 20:03 PM

### Top Opportunities (18:03 scan)
1. **ALICE-USD**: Score 100, +46% price, +3,634% volume (HIGH)
2. **MAGIC-USD**: Score 81.1, +21% price, +554% volume (HIGH)
3. **BAT-USD**: Score 73.5, +23% price, +442% volume (HIGH)
4. **BAND-USD**: Score 71.6, +16% price (HIGH)

## Scheduled Tasks

```
- breakout-scanner: Every 2 hours
- check-pnl-triggers: Every 10 minutes
- check-closing-bots: Every hour
- update-trade-statuses: Every 2 minutes
- cache-stats-logger: Every 1 minute
- daily-bot-cleanup: Daily at 2 AM
```

## Recent Changes

### October 13, 2025
- 18:30: All documentation updated
- 18:03: Breakout scan (4 USD opportunities found, 3 USDC filtered)
- 16:03: First scan with USD filter active
- Afternoon: USD-only filter deployed to production
- Morning: Real capital system deployed (removed fake $500 limit)

### October 11, 2025
- RiskAdjustmentService activated (dynamic position scaling 0.2x-3.0x)

### October 9, 2025
- Bot deletion with liquidation feature

### October 5, 2025
- Universal learning system deployed (all bots optimized)

## Health Metrics

- **Cache Hit Rate**: 97.5%
- **System Errors**: 0
- **Rate Limit Issues**: 0
- **Active Bots**: 30
- **Signal Predictions**: 141,000+
- **WebSocket**: Connected and streaming

## Documentation

### Core Guides
- **Main Instructions**: `.github/copilot-instructions.md`
- **Capital System**: `docs/current/REAL_CAPITAL_SYSTEM.md`
- **USD Filter**: `docs/current/USD_ONLY_FILTER.md`
- **Today's Status**: `SYSTEM_STATUS_OCTOBER_13_2025.md`

### Monitoring Commands
```bash
# Watch logs
./scripts/logs.sh

# Check breakout scans
grep "Breakout scanner" logs/celery-worker.log | tail -5

# Check USD filter
grep "Filtered out.*non-USD" logs/celery-worker.log | tail -5

# Check capital
cd backend && source venv/bin/activate
python -c "
from app.services.capital_reallocation_service import CapitalReallocationService
capital = CapitalReallocationService().get_available_capital()
print(f'USD: \${capital[\"usd_balance\"]:.2f}')
"
```

## Next Expected Events

- **20:03 PM**: Next breakout scan
- **18:36 PM**: Next P&L check
- **When**: $0.58+ available → ALICE-USD bot created (score 100)

## Emergency Contacts

- **System hangs**: Check WebSocket streaming, restart if needed
- **Rate limiting**: Verify WebSocket active, check cache stats
- **No bot creation**: Check capital balance, verify USD filter

---

**Status**: 🟢 Production Ready  
**Capital**: $14.42 USD available  
**Filter**: USD-only active  
**P&L Monitoring**: Every 10 minutes  
**Next Bot**: ALICE-USD at score 100 (need $0.58 more)
