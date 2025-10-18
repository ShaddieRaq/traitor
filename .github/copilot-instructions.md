# Auto-Trader AI Agent Instructions

## 🎯 System Purpose
Production cryptocurrency trading system managing **~13 live trading bots** with real capital. Changes affect real money—verify everything.

## ⚡ Quick Start Workflow

**1. Check system state FIRST (always):**
```bash
./scripts/status.sh                                      # Overall health
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Bot count (~13)
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq    # Should be []
```

**2. Start services if needed:**
```bash
./scripts/start.sh    # Starts Redis, FastAPI, Celery (worker + beat), React frontend
./scripts/logs.sh     # Monitor all service logs in real-time
```

**3. Verify after changes:**
```bash
curl -s --max-time 5 "http://localhost:8000/health" | jq  # API responsive?
tail -20 logs/backend.log                                  # Recent activity
```

## 🏗️ Architecture at a Glance

**Stack:** FastAPI + SQLAlchemy + Celery/Redis + React 18 + TypeScript  
**Database:** SQLite at `/trader.db` (NOT `backend/trader.db`)  
**Real-time:** WebSocket price streaming + Redis cache (97%+ hit rate)  
**Trading:** Market orders via Coinbase Advanced Trade API

**Critical Services:**
- `MarketDataService` - Centralized price/candle data with Redis (prevents rate limiting)
- `BotSignalEvaluator` - Signal aggregation (RSI + MA + MACD) → trade decisions
- `RiskAdjustmentService` - Dynamic position sizing (0.2x-3.0x based on P&L)
- Celery Beat - Scheduled tasks (hourly breakout scans, bot evaluations)

## 🔑 Critical Patterns

### Database Location
```python
# ALWAYS use project root database
DATABASE_URL = "sqlite:////Users/lazy_genius/Projects/trader/trader.db"
# ❌ NOT: backend/trader.db
```

### Dual-Table Trading Pattern
```python
# Trade table - DEPRECATED (corrupted data, endpoints removed Oct 5, 2025)
# RawTrade table - Source of truth (exact Coinbase fills)
# ✅ ALWAYS use: /api/v1/raw-trades/*
```

### Signal Factory Pattern
```python
# Bots store signal config as JSON in signal_config column
# Factory dynamically creates signal instances
from backend.app.services.signals.base import create_signal_instance

bot.signal_config = {
    "rsi": {"enabled": true, "weight": 0.4, "period": 14},
    "moving_average": {"enabled": true, "weight": 0.35},
    "macd": {"enabled": true, "weight": 0.25}
}

# Maps 'rsi' → RSISignal, 'moving_average' → MovingAverageSignal
signal = create_signal_instance('RSI', {'period': 14})
```

### Global Service Pattern
```python
# Industry-standard singleton with dependency injection
from backend.app.services.market_data_service import get_market_data_service
market_service = get_market_data_service()  # Reuses same instance
```

### API Response Pattern
```python
# Bot API returns computed fields NOT stored in DB
{
    "current_combined_score": -0.087,  # Computed by bot_evaluator
    "temperature": "🔥HOT",             # From temperature utils
    "risk_multiplier": 1.96,            # From RiskAdjustmentService
    "trading_thresholds": {...},       # Computed, NOT in signal_config
    "signal_config": {...}             # Parsed from JSON
}
```

### Frontend Real-Time Pattern
```typescript
// TanStack Query with aggressive 5s polling
export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: fetchBotsStatus,
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0  // Always fetch fresh
  });
};
```

## 🚨 Critical Rules

### Rate Limiting Prevention
```bash
# PRIMARY CHECK - WebSocket must be running
curl -s "http://localhost:8000/api/v1/websocket-prices/status" | jq

# Start if not running (solves 99% of rate limit issues)
curl -X POST "http://localhost:8000/api/v1/websocket-prices/start-price-streaming"

# Verify streaming in logs
grep "💰.*USD:" logs/backend.log | tail -5
```

### Signal Thresholds (NEVER CHANGE)
```python
# Optimized system-wide values
buy_threshold = -0.05   # ✅ DO NOT MODIFY
sell_threshold = 0.05   # ✅ DO NOT MODIFY
```

### Bot Deletion with Liquidation
```bash
# Multi-account aggregation (Oct 14, 2025 fix)
DELETE /api/v1/bots/{bot_id}?liquidate=true

# Sums holdings across ALL Coinbase accounts per currency
# ⚠️ Known limitation: Coinbase API can't liquidate from multiple accounts atomically
```

### Development Rules
- ❌ **Never modify system defaults during debugging**
- ✅ **Always test single bot before batch operations**
- ✅ **Check OpenAPI schema before API calls**: `curl "http://localhost:8000/openapi.json" | jq`
- ✅ **Use timeouts on all API calls**: `curl -s --max-time 5 ...`
- ✅ **Verify claims with actual responses**, not assumptions

## � Essential Files

### Core Services
- `backend/app/services/bot_evaluator.py` - Signal aggregation & trading decisions
- `backend/app/services/market_data_service.py` - Redis-cached market data (prevents rate limits)
- `backend/app/services/risk_adjustment_service.py` - Dynamic position sizing (0.2x-3.0x)
- `backend/app/tasks/trading_tasks.py` - Celery background evaluation tasks
- `backend/app/models/models.py` - Database schema (Bot, RawTrade, etc.)

### API & Frontend
- `backend/app/api/bots.py` - Bot CRUD with computed fields via `prepare_bot_response()`
- `frontend/src/hooks/useBots.ts` - TanStack Query with 5s polling pattern
- `frontend/src/pages/DashboardRedesigned.tsx` - Main dashboard UI
- `scripts/start.sh` & `scripts/status.sh` - Service orchestration

### Key Utilities
- `backend/app/services/signals/base.py` - Signal factory (`create_signal_instance()`)
- `backend/app/utils/temperature.py` - Bot temperature calculation (🔥/🌡️/❄️/🧊)

## 💡 Development Tips

### Testing Workflow
```bash
./scripts/test-workflow.sh              # Full validation
python backend/tests/test_runner.py rsi # Test specific signal
curl "http://localhost:8000/api/v1/bots/status/enhanced" | jq  # Health check
```

### Debugging
```bash
./scripts/logs.sh                       # Tail all service logs
tail -f logs/backend.log | grep ERROR   # Backend errors
curl "http://localhost:8000/api/v1/cache/stats" | jq  # Cache performance
```

### Common Pitfalls
- **Database path**: Use `/trader.db` (project root), NOT `backend/trader.db`
- **Trade endpoints**: Use `/api/v1/raw-trades/*`, NOT deprecated `/api/v1/trades/*`
- **Signal config**: Only `rsi`, `moving_average`, `macd` keys accepted
- **Computed fields**: `trading_thresholds` computed via `extract_trading_thresholds()`, not stored in DB

## 🚨 Critical Troubleshooting

### Rate Limiting Prevention
**Primary cause: WebSocket not running** - every price request hits REST API when streaming is down.

```bash
# Check WebSocket status (PRIMARY CHECK)
curl -s "http://localhost:8000/api/v1/websocket-prices/status" | jq '.streaming'

# Start if not running (solves 99% of rate limit issues)
curl -X POST "http://localhost:8000/api/v1/websocket-prices/start-price-streaming"

# Verify in logs
grep "💰.*USD:" logs/backend.log | tail -5
```

### Database Corruption Recovery
**Symptom:** "file is not a database" errors - usually caused by corrupted WAL files.

```bash
# 1. Backup database first
cp trader.db trader.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. Remove WAL files (solves 90% of corruption issues)
rm -f trader.db-shm trader.db-wal

# 3. Verify integrity
sqlite3 trader.db "PRAGMA integrity_check;"

# 4. Test connection
python -c "from backend.app.core.database import engine; from sqlalchemy import text; \
conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM bots')).scalar(); \
conn.close(); print(f'✅ {result} bots found')"
```

**Prevention:** Stop backend/celery services cleanly before system shutdown to avoid WAL corruption.

## 📚 Additional Resources

- `/README.md` - Current system status & features
- `/CURRENT_ARCHITECTURE.md` - Detailed architecture documentation  
- `/docs/current/` - Technical guides and troubleshooting
- `/SYSTEM_STATUS_OCTOBER_18_2025.md` - Recent updates and fixes
