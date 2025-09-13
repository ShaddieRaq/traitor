## Autonomous Trading System — AI Agent Guide

⚠️ **SYSTEM DECOMMISSIONED - SEPTEMBER 11, 2025** ⚠️

**Critical Issue**: Data integrity problem with Coinbase sync importing trades user claims they never made.

**Status**: System suspended until manual verification resolves data source discrepancy.

**Last Known State**: All calculation bugs fixed, but fundamental data validation required.

**Documentation**: See `docs/SYSTEM_DECOMMISSION_REPORT.md` for full details.

**DO NOT RESUME LIVE TRADING** until data integrity verified.

---

## System Architecture & AI Agent Guide

**Purpose**: Enable immediate, safe productivity. Keep changes small, test thoroughly, never break existing functionality.

### 1. Core Architecture Pattern
**Bot-Centric Design**: One bot per trading pair with autonomous signal aggregation pipeline:

`Market Data → Signal Calculation (RSI/MA/MACD) → Weighted Aggregation → Temperature Classification → Action Intent → Safety Checks → Trade Execution`

- **Always recompute**: Never trust `bot.current_combined_score` from DB - recalculate from fresh market data
- **Temperature system**: HOT/WARM/COOL/FROZEN thresholds drive UI indicators and trade readiness
- **Weight constraints**: Signal weights must sum ≤ 1.0 or system rejects configuration
- **Status sync**: All trade state changes broadcast via WebSocket to maintain real-time UI consistency

### 2. Key Service Architecture
**Backend Services** (`backend/app/services/`):
- `bot_evaluator.py` - Core signal aggregation + auto-trade trigger logic
- `trading_service.py` - Trade execution, safety checks, status broadcasting  
- `coinbase_service.py` - Exchange API integration, portfolio breakdown, order status
- `trading_safety.py` - Position limits, cooldown validation, balance checks
- `position_service.py` - Tranche tracking, P&L calculations
- `streaming_bot_evaluator.py` - WebSocket market data processing

**FastAPI Application** (`backend/app/main.py`):
- RESTful API with `/api/v1/` prefix
- Auto-generated OpenAPI docs at `/api/docs`
- CORS enabled for React frontend (localhost:3000, localhost:5173)

**React Frontend** (`frontend/src/`):
- TanStack Query for aggressive 5-second polling with `staleTime: 0`
- Component-based architecture in `components/Trading/`
- Real-time dashboard with WebSocket fallback to polling

### 3. Critical Data Flow Patterns
**Trade Size**: ALWAYS use `trade.size_usd` - never calculate `size * price` (quote/base ambiguity)

**Cooldown Logic**: Based on `filled_at` timestamp, NOT `created_at` (only after order actually fills)

**P&L Calculation**: Include all valid trade statuses, use `size_usd` field consistently

**Fresh Evaluations**: Every endpoint call recalculates from live market data:
```python
data = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
result = evaluator.calculate_bot_temperature(bot, data)
```

**Signal Configuration**: Parse JSON config with weight validation:
```python
config = json.loads(bot.signal_config)
rsi = config.get('RSI', {})
weight_sum = sum(signal.get('weight', 0) for signal in config.values() if signal.get('enabled'))
assert weight_sum <= 1.0, "Signal weights exceed maximum"
```

### 4. Essential Development Workflow
**Mandatory Script Usage** (never bypass these):
```bash
# Health check first
./scripts/status.sh              # Must show all ✅ before changes

# Development cycle
./scripts/start.sh               # Boot all services if needed
# ... make code changes ...
./scripts/test.sh                # Must pass 100% before commit
./scripts/restart.sh             # If runtime services need reload

# Database safety
cp backend/trader.db backend/trader_backup_$(date +%Y%m%d_%H%M%S).db
```

### 5. Key API Endpoints
**Enhanced Bot Status** (authoritative runtime data):
```bash
GET /api/v1/bots/status/enhanced  # Real-time trading_intent, confirmation, readiness
POST /api/v1/bot-evaluation/{id}/evaluate  # Force fresh evaluation + potential auto-trade
```

**Trade Management**:
```bash
POST /api/v1/trades/update-statuses  # Batch order status sync with Coinbase
GET /api/v1/market/accounts          # USD balance via portfolio breakdown
```

**WebSocket Streams**:
```bash
WS /api/v1/ws/trade-execution       # Real-time trade progress updates
POST /api/v1/ws/start-streaming/{bot_id}  # Enable market data streaming
```

### 6. React Frontend Patterns
**TanStack Query Configuration** (critical for real-time updates):
```typescript
export const useEnhancedBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'enhanced-status'],
    queryFn: fetchEnhancedBotsStatus,
    refetchInterval: 5000,                // Poll every 5 seconds
    refetchIntervalInBackground: true,    // Continue when tab inactive
    refetchOnWindowFocus: true,           // Refresh when tab focused
    staleTime: 0,                         // Always consider data stale
  });
};
```

**Reactive Component Keys** (include changing data to force re-renders):
```typescript
<ConsolidatedBotCard 
  key={`bot-${bot.id}-${bot.current_combined_score}`}
  bot={bot}
/>
```

### 7. Testing & Data Safety
**Test Cleanup Pattern** (prevents DB pollution):
```python
def test_bot_creation(self, client):
    created_bot_ids = []
    try:
        # Test logic that creates bots
        if response.status_code == 201:
            created_bot_ids.append(response.json()["id"])
    finally:
        # Always clean up test bots
        for bot_id in created_bot_ids:
            client.delete(f"/api/v1/bots/{bot_id}")
```

**Automated Cleanup**:
```bash
./scripts/cleanup.sh --dry-run     # Preview test data cleanup
./scripts/cleanup.sh               # Remove test bots and orphaned data
```

### 8. Common Pitfalls to Avoid
- **Temperature enum mismatch**: Frontend uses "COOL", backend has "COLD" - always use COOL
- **Stale DB data**: Never use `bot.current_combined_score` without fresh calculation
- **Size calculation bugs**: Always use `trade.size_usd`, never `size * price`
- **Test pollution**: Always cleanup created bots in tests
- **Blocking UI**: Include reactive keys with changing values (scores, timestamps)
- **WebSocket complexity**: Reuse existing streaming endpoints, don't rebuild

### 9. Fast Diagnostics
```bash
# System health
./scripts/status.sh
curl -s localhost:8000/health

# Runtime state check
curl -s localhost:8000/api/v1/bots/status/enhanced | jq '.[0] | {id,temperature,trading_intent,trade_readiness}'

# Check for stuck trades
sqlite3 backend/trader.db "SELECT id,side,status,created_at FROM trades WHERE status='pending'"
```

### 10. Database Patterns
**SQLAlchemy Models** (`backend/app/models/models.py`):
- `Bot`: Main entity with `signal_config` JSON field
- `Trade`: Always include `size_usd`, `filled_at` for cooldown logic
- `BotSignalHistory`: Timestamped signal evaluations for debugging

**Database Connection**:
```python
from app.core.database import get_db, SessionLocal
# Use get_db() for FastAPI dependencies
# Use SessionLocal() for scripts and services
```

### 11. Configuration Management
**Settings** (`backend/app/core/config.py`):
- Environment file: `/Users/lazy_genius/Projects/trader/.env`
- Database: SQLite at `backend/trader.db`
- Redis: `redis://localhost:6379/0` for Celery
- Always production mode - no mock trading

**Signal Configuration JSON Schema**:
```json
{
  "RSI": {"enabled": true, "weight": 0.4, "period": 14, "buy_threshold": 35, "sell_threshold": 65},
  "moving_average": {"enabled": true, "weight": 0.4, "fast_period": 12, "slow_period": 26},
  "macd": {"enabled": true, "weight": 0.2, "fast_period": 12, "slow_period": 26, "signal_period": 9}
}
```

### 12. Reference Documentation
**Deep Dives**: `docs/IMPLEMENTATION_GUIDE.md` (patterns) • `docs/TROUBLESHOOTING_PLAYBOOK.md` (fixes) • `docs/PHASE_HISTORY.md` (evolution) • `PROJECT_STATUS.md` (current state)

**System Architecture**: FastAPI backend + React frontend + SQLite + Redis/Celery + Coinbase API integration with real-time polling and WebSocket broadcasting

Last Updated: 2025-09-11 (Comprehensive agent guide post-decommission analysis)

---

## System Architecture & AI Agent Guide

**Purpose**: Enable immediate, safe productivity. Keep changes small, test thoroughly, never break existing functionality.

### 1. Core Mental Model
Bot = single trading pair. Evaluation pipeline (every request / stream tick): market data → individual signal scores (RSI / MA / MACD) -1..+1 → weighted aggregate (Σ weights ≤ 1.0) → action intent → (confirmation window + safety checks) → trade (record + status sync). Temperatures (FROZEN/COOL/WARM/HOT) derive from absolute combined score thresholds (see `app/utils/temperature.py`). Always recompute; stored DB score is NOT authoritative.

### 2. Critical Directories & Files
backend/app/services/bot_evaluator.py (aggregation + auto-trade trigger)
backend/app/services/streaming_bot_evaluator.py (WebSocket market stream path)
backend/app/services/trading_service.py (execution + safety + status sync broadcast)
backend/app/services/coinbase_service.py (REST + portfolio breakdown; order status)
backend/app/services/trading_safety.py (limits / cooldown / balance checks)
backend/app/services/position_service.py (tranche & position summaries)
backend/app/api/bots.py (enhanced status endpoint) | api/trades.py (P&L, sync)
backend/app/models/models.py (Bot / Trade: size_usd, position_tranches, scores)
frontend/src/pages/Dashboard.tsx + components/Trading/* (real-time UI)
scripts/*.sh (ALWAYS use: start/stop/status/test/logs)

### 3. Mandatory Patterns (Do These or It’s a Bug)
Fresh evaluations ONLY: never trust `bot.current_combined_score` from DB.
P&L & sizing: ALWAYS use `trade.size_usd`; NEVER raw `size * price` (size_in_quote ambiguity).
Signal weights: reject / fail if enabled weights sum > 1.0.
React polling: 5s TanStack Query, staleTime=0 + reactive keys including score.
USD balance: use portfolio breakdown (not get_accounts()).
Cooldown logic: based on last FILLED trade (filled_at), not created_at.
WebSocket presence: streaming layer exists—don’t rebuild, reuse (`/ws/start-streaming/{bot_id}`).
Cleanup tests: remove created bots (prevent data pollution) – mimic existing fixtures.

### 4. Safe Workflow
1) `./scripts/status.sh` (all ✅)  2) `./scripts/start.sh` (if needed)  3) Edit
4) `./scripts/test.sh` (must stay green)  5) `./scripts/restart.sh` if runtime services need reload.
Before structural DB changes: stop services + backup (`cp backend/trader.db backend/trader_backup_$(date +%Y%m%d_%H%M%S).db`).

### 5. Key Endpoints (Use / Extend These)
GET /api/v1/bots/status/enhanced  (authoritative runtime state: trading_intent, confirmation, trade_readiness, last_trade)
POST /api/v1/bot-evaluation/{id}/evaluate (forces fresh evaluation + potential auto-trade)
POST /api/v1/trades/update-statuses (batch order status sync)
GET /api/v1/market/accounts (balance via portfolio breakdown)
WS /ws/trade-execution (execution progress stream) | POST /ws/start-streaming/{bot_id}

### 6. Typical Code Snippets
Python (fresh eval): `data = svc.get_historical_data(pair); meta = evaluator.calculate_bot_temperature(bot, data)`
Signal config parse: `cfg = json.loads(bot.signal_config); rsi = cfg.get('RSI', {});`
Frontend hook: refetchInterval=5000, key includes changing score: `key={bot.id + '-' + bot.current_combined_score}`
P&L loop: `val = float(t.size_usd) if t.size_usd is not None else t.size * t.price` (fallback only)

### 7. Pitfalls to Avoid
“COOL” vs “COLD” enum mismatch (frontend must use COOL).
Recomputing temperature from stale value instead of fresh market data.
Multiplying size*price → inflated or wrong USD metrics.
Forgetting test bot cleanup → polluted analytics.
Blocking UI updates by omitting reactive key changes.
Adding new signal without weight cap + JSON schema update.

### 8. When Adding Features
Locate existing service first (search in services/). Extend; do not fork logic.
Add minimal test mirroring pattern in backend/tests (reuse factories / cleanup).
Expose through existing enhanced status endpoint when adding runtime metrics.
Document only if pattern differs from above; otherwise keep file terse.

### 9. Fast Diagnostics
Health: `./scripts/status.sh` | API: `curl -s localhost:8000/health`
Runtime state: `curl -s localhost:8000/api/v1/bots/status/enhanced | jq '.[0] | {id,temperature,trading_intent,trade_readiness}'`
Pending trades: inspect `trades` where status='pending' (should be transient).

### 10. Deep Dives
See: docs/IMPLEMENTATION_GUIDE.md (patterns) • docs/TROUBLESHOOTING_PLAYBOOK.md (fixes) • docs/PHASE_HISTORY.md (evolution) • PROJECT_STATUS.md (current state).

Last Updated: 2025-09-07  (Condensed agent guide)
