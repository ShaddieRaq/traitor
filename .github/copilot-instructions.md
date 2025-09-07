## Autonomous Trading System — AI Agent Quick Guide

Purpose: Enable immediate, safe productivity. Keep changes small, test via scripts, never break live trading assumptions.

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
