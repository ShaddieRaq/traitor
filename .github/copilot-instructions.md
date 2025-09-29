# GitHub Copilot Instructions for Auto-Trader System

## 🚨 TOP PRIORITY - CRITICAL AGENT WARNING 🚨

**NEVER MAKE CLAIMS ABOUT SYSTEM STATE WITHOUT VERIFICATION!**

❌ **DO NOT SAY**: "Fixed", "Resolved", "System is healthy", "Errors cleared"  
✅ **ALWAYS VERIFY**: Check actual API responses, error counts, system status AFTER making changes

**MANDATORY VERIFICATION STEPS:**
1. Run `./scripts/status.sh` to check service health
2. Check error count: `curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'`  
3. Check system status: `curl -s "http://localhost:8000/api/v1/system-errors/health"`
4. Verify specific claims with actual API calls before declaring success

**Failure to verify leads to false claims and user frustration!**

## 🚨 DEBUGGING & DIAGNOSTIC RULES - CRITICAL 🚨

**NEVER RESTART SERVICES AS FIRST RESPONSE TO ISSUES!**

❌ **FORBIDDEN PATTERNS**:
- Restarting services when API calls hang or timeout
- Running `./scripts/stop.sh && ./scripts/start.sh` without diagnosis
- Assuming system is "deadlocked" without evidence
- Making reactive decisions based on slow responses

✅ **PROPER DIAGNOSTIC SEQUENCE**:
1. **Use timeouts**: `curl -s --max-time 5` to avoid infinite hangs
2. **Check process status**: `ps aux | grep -E "(python.*main|uvicorn)"`
3. **Check port binding**: `lsof -i :8000` to verify listener
4. **Check recent logs**: `tail -n 20 /Users/lazy_genius/Projects/trader/logs/backend.log`
5. **Try simple endpoints first**: Test `/health` before complex queries
6. **Check Celery worker status**: Heavy task processing can cause slowdowns

**IF API IS SLOW/HANGING:**
- System may be processing Celery task backlog (normal during error storms)
- Backend might be rate-limited by external APIs (also normal)
- Database might be busy with bulk operations (expected behavior)
- **PATIENCE REQUIRED** - system often recovers naturally

**ONLY RESTART IF:**
- Process is confirmed dead (`ps aux` shows no backend process)
- Port 8000 is not listening (`lsof -i :8000` returns nothing)
- Logs show fatal errors with no recovery
- User explicitly requests restart

**REMEMBER**: Restarting destroys diagnostic evidence and can mask root causes!

## System Overview

This is a **production-ready cryptocurrency trading system** with **25 active bots** managing live funds across major trading pairs. The system features sophisticated 4-phase AI intelligence framework, triple-layer rate limiting protection, and proven profitable performance (+$265.77 over 63 days, ~42% annualized return).

### Key Architectural Principles
- **Bot-Per-Pair Design**: Each bot manages exactly one trading pair (e.g., BTC-USD, ETH-USD)
- **JSON-Driven Configuration**: Signal weights and parameters stored as JSON in `Bot.signal_config`
- **Dual-Table Trade Pattern**: `Trade` (operational) + `RawTrade` (financial truth from Coinbase)
- **Celery Background Processing**: 5-minute evaluation cycles with Redis queue
- **Intelligent Caching**: 90s TTL market data cache achieving 80%+ hit rates
- **Real-Time Frontend**: 5-second TanStack Query polling with aggressive refresh

## Core Architecture

- **Backend**: FastAPI + SQLAlchemy ORM + Celery/Redis + 4-phase AI intelligence framework
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS with TanStack Query (5-second polling)
- **Database**: Single unified SQLite file (`/trader.db`) with dual-table pattern (Trade + RawTrade)
- **API Structure**: RESTful with `/api/v1/` prefix, feature-organized routes in `/backend/app/api/`
- **Real-time Architecture**: 5-second polling with 90s backend cache (proven more reliable than WebSocket)
- **Testing**: 185+ comprehensive tests with signal validation and live API integration

## 🚨 CRITICAL FIRST STEPS FOR AI AGENTS

```bash
# 1. ALWAYS check system health first (before any changes)
./scripts/status.sh

# 2. Configure Python environment (REQUIRED before Python operations)  
# Use configure_python_environment tool

# 3. Start services if needed
./scripts/start.sh

# 4. Verify all 25 bots are operational
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Should return 25
```

## Essential Project Startup (Manual Alternative)

For debugging or when scripts fail, use manual startup sequence:
```bash
# Terminal 1: Start Redis
docker-compose up redis

# Terminal 2: Start Backend (from backend/ directory)
cd backend && source venv/bin/activate  
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Celery Worker (from backend/ directory)
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 4: Start Celery Beat Scheduler (from backend/ directory)  
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 5: Start Frontend (from frontend/ directory)
cd frontend && npm run dev
```

## Essential Development Patterns

### Bot-Per-Pair Architecture
Each `Bot` entity manages exactly one trading pair with dynamic signal configuration stored as JSON in `Bot.signal_config`. Signals are created via factory pattern in `/backend/app/services/signals/base.py`.

### Dual-Table Data Pattern (CRITICAL)
- **Trade Table**: Operational data (bot decisions, signals) in `/backend/app/models/models.py`  
- **RawTrade Table**: Financial truth (exact Coinbase fills) - AUTO-SYNCED from Coinbase API
- **Database Location**: `/trader.db` at project root (NOT backend/trader.db)

### Signal Scoring System
- **Range**: -1.0 (BUY signal) to +1.0 (SELL signal)
- **Thresholds**: ±0.05 system-wide (optimized for sensitivity) 
- **Temperature**: 🔥HOT/🌡️WARM/❄️COOL/🧊FROZEN based on signal scores
- **Aggregation**: Weighted combination of RSI, Moving Average, and MACD in `bot_evaluator.py`

### Celery Task Architecture
- **Main Evaluation**: `fast_trading_evaluation()` every 5 minutes with automatic trading
- **Market Data**: `fetch_market_data_task()` every 5 minutes with intelligent caching  
- **Trade Sync**: `update_trade_statuses()` every 60 seconds for pending order monitoring
- **Configuration**: `/backend/app/tasks/celery_app.py` with Redis broker

### API Response Patterns
```python
# Bot API returns computed fields not stored in DB
{
  "id": 1,
  "current_combined_score": -0.087,  # From bot_evaluator calculation
  "temperature": "🔥HOT",            # From temperature utils
  "trading_thresholds": {...},       # Extracted from signal_config JSON
  "signal_config": {...}             # Parsed from JSON string
}
```

## Intelligence Framework Status (September 28, 2025)

✅ **ALL 4 BACKEND PHASES COMPLETED + RECENT EXPANSION**

### Recent Major Achievements (Sept 27-28, 2025)
1. **25-Bot System Operational**: All bots displaying correctly with proper signal data across major pairs
2. **Backend Synchronization**: Fixed evaluate_bot_signals and fast_trading_evaluation to update database properly  
3. **Dashboard Fixes**: Fixed Active Pairs count (now shows 25), eliminated React rendering errors, simplified bot display
4. **Rate Limiting Mastery**: Triple-layer protection (90s cache + circuit breaker + exponential backoff)
5. **Performance Optimization**: Trading thresholds optimized to ±0.05 for 2x sensitivity, +$87.52 profit in 24hrs
6. **UI Simplification**: Removed complex categorization, all bots visible in simple list format

### Backend Intelligence (Complete & Enhanced)
1. **Market Regime Detection**: CHOPPY regime active (-0.146 strength, 0.75 confidence)
2. **Dynamic Position Sizing**: Enhanced with regime-based adjustments across 25 pairs
3. **Signal Performance Tracking**: 451,711+ predictions with outcome evaluation system
4. **Adaptive Signal Weighting**: All 25 bots eligible for AI-driven weight optimization

## Current Development Phase: CRITICAL ARCHITECTURAL REBUILD - NO MORE RATE LIMITS

**Status**: IMMEDIATE PRIORITY - Rate limiting issues have persisted despite multiple fixes
**Goal**: Complete elimination of rate limiting through centralized data management architecture
**Focus**: Rebuild data layer to support 25+ bots without API rate limit conflicts
**Priority**: ZERO TOLERANCE for rate limiting errors - architectural solution required

**🚨 CRITICAL DECISION (September 29, 2025)**: The current system has grown too complex with multiple processes making independent API calls. Band-aid caching solutions have failed repeatedly. Time for proper architectural rebuild.

### Phase 6: Centralized Data Management Architecture
**OBJECTIVE**: Build bulletproof system that can handle 100+ bots without rate limits

**Core Components**:
1. **Centralized Market Data Service**: Single service fetches ALL market data 
2. **Shared Cache Layer**: All bots read from unified cache, ZERO individual API calls
3. **Intelligent Data Refresh**: Dynamic refresh rates based on market volatility
4. **Distributed Data Storage**: Redis/memory cache with database persistence
5. **API Call Coordination**: Global rate limiter with priority queuing

**Implementation Strategy**:
- **Phase 6.1**: Design centralized data service architecture
- **Phase 6.2**: Implement shared cache layer with Redis
- **Phase 6.3**: Migrate all bots to read from shared cache
- **Phase 6.4**: Remove all individual API calls from bot evaluation
- **Phase 6.5**: Add intelligent refresh logic and monitoring

### Previous Optimizations (September 28, 2025) - NOW OBSOLETE
1. **Dashboard Restoration**: Fixed portfolio display, eliminated React errors, simplified bot view  
2. **Backend Sync Fixed**: Celery evaluation tasks now properly update bot scores in database
3. **Enhanced Rate Limiting**: ❌ 90s cache TTL - FAILED TO SOLVE PERSISTENT RATE LIMITS
4. **UI Simplification**: Removed confusing categorization, all 25 bots displayed clearly
5. **React Error Resolution**: Fixed object-as-children rendering issues preventing dashboard load

## Known Issues & Recovery - RATE LIMITING PERSISTENT FAILURE

**Current Status**: ⚠️ CRITICAL ARCHITECTURAL ISSUE IDENTIFIED (September 29, 2025)

**ROOT CAUSE ANALYSIS**:
Rate limiting has been a persistent problem because the system architecture is fundamentally flawed:
- **5 independent processes** making simultaneous API calls (Backend, Celery Worker, Celery Beat, Signal Tracking, Market Regime Detection)
- **No centralized coordination** of API requests across system components  
- **Multiple competing cache layers** that don't communicate
- **25 bots × 3-4 API calls each** = 75-100 API calls every 5 minutes exceeds Coinbase limits

**FAILED SOLUTIONS** (All band-aids that didn't address root cause):
1. ❌ **Rate Limiting**: Triple-layer protection - FAILED, still getting 100+ 429 errors nightly
2. ❌ **Cache Enhancement**: 90s TTL - FAILED, multiple processes still make independent calls
3. ❌ **Circuit Breakers**: FAILED, doesn't reduce total API call volume
4. ❌ **Exponential Backoff**: FAILED, just delays the inevitable rate limit hits

**NEXT STEPS**: Phase 6 Centralized Data Management (see Current Development Phase above)

## Development Workflows

### Essential Scripts
```bash
# Full validation after changes (REQUIRED)
./scripts/test-workflow.sh

# Rapid iteration testing  
./scripts/quick-test.sh

# Real-time debugging
./scripts/logs.sh

# Signal testing by category
python tests/test_runner.py [rsi|ma|macd|aggregation|all]
```

### Critical API Endpoints
```bash
# System health & bot status
curl "http://localhost:8000/api/v1/bots/status/enhanced" | jq
curl "http://localhost:8000/api/v1/diagnosis/trading-diagnosis" | jq

# Performance data (CURRENT - use these)
curl "http://localhost:8000/api/v1/raw-trades/pnl-by-product" | jq
curl "http://localhost:8000/api/v1/cache/stats" | jq  # Should show 80%+ hit rates
```

## Key Architecture Constraints

### Database Rules
- **Single Source**: `/trader.db` at project root (never use backend/trader.db)
- **Manual Migrations**: SQLAlchemy schema changes only, no automatic migrations
- **Auto-Sync**: Both Trade and RawTrade tables update automatically

### Performance Patterns  
- **Market Data Cache**: 30s TTL achieving 80%+ hit rates via `MarketDataCache`
- **Balance Pre-Check**: Bots skip signal processing when insufficient funds (~60% API reduction)
- **Frontend Polling**: Aggressive 5-second TanStack Query with `staleTime: 0`

### Configuration Details
- **Backend Entry Point**: `backend/app/main.py` with FastAPI app initialization
- **Frontend Dev Server**: Vite config with proxy to port 8000 for `/api` routes
- **Environment File**: `.env` at project root (not in backend/) - requires COINBASE_API_KEY/SECRET
- **Celery Configuration**: `backend/app/tasks/celery_app.py` with Redis broker
- **Python Environment**: Virtual environment required in `backend/venv/`

### Trading Constraints & Error Patterns
- **Market vs Limit Orders**: System uses `place_market_order()` only - some pairs require limit orders
- **Limit-Only Pairs**: ZEC-USD returns "Orderbook is in limit only mode" - replace with MATIC-USD  
- **Size Validation**: All trades $10+ USD minimum, precision handled by `base_increment` from Coinbase
- **Rate Limiting**: 90s cache + circuit breaker prevents 429 errors from Coinbase API
- **Balance Checking**: Bots skip evaluation when insufficient funds to reduce API calls

### Recovery Procedures
```bash
# NEVER restart blindly - diagnose first
./scripts/status.sh  

# Verify Docker dependency (required for Redis)
docker --version && docker-compose --version

# Safe restart sequence
./scripts/stop.sh && ./scripts/start.sh
```

## Critical Code Patterns

### Signal Factory Pattern
```python
# Signals created dynamically from Bot.signal_config JSON
signal_instance = create_signal_instance(signal_type, parameters)
```

### Frontend Real-time Data Pattern
```typescript
// All hooks use aggressive polling for real-time updates
export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: fetchBotsStatus,
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0  // Always fetch fresh data
  });
};
```

### Temperature System Pattern
```python
# Single source calculation
from ..utils.temperature import calculate_bot_temperature, get_temperature_emoji
temperature = calculate_bot_temperature(abs(combined_score))  
emoji = get_temperature_emoji(temperature)  # 🔥🌡️❄️🧊
```

## Essential File Reference

### Core Services
- `/backend/app/services/bot_evaluator.py` - Main signal aggregation logic (FIXED: database updates)
- `/backend/app/tasks/trading_tasks.py` - Celery evaluation tasks (FIXED: current_combined_score updates)
- `/backend/app/models/models.py` - Database models (Bot, Trade, RawTrade)
- `/backend/app/services/market_data_cache.py` - Intelligent caching (prevents rate limits)

### Frontend Architecture  
- `/frontend/src/pages/DashboardRedesigned.tsx` - Main unified dashboard
- `/frontend/src/components/Dashboard/TieredBotsView.tsx` - Simplified bot display (all 25 bots)
- `/frontend/src/components/Dashboard/PortfolioSummaryCard.tsx` - Fixed active pairs count
- `/frontend/src/hooks/` - TanStack Query patterns for real-time data
- `/frontend/src/components/Dashboard/` - Stable React components

### Intelligence Framework
- `/backend/app/services/trend_detection_engine.py` - Market regime detection
- `/backend/app/services/position_sizing_engine.py` - Dynamic position sizing  
- Signal performance tracking integrated in bot evaluator

## Development Philosophy

🚨 **CRITICAL RULES**:
- **Never move to next phase with broken code** - fix bugs immediately
- **Test every new API endpoint** with actual HTTP calls  
- **Pydantic schemas must match** API response structure exactly
- **Always run** `./scripts/status.sh` before making changes
- **Use tools** `configure_python_environment` before Python operations

🚨 **CRITICAL RULES FOR ALL AGENTS**:
- **NEVER MAKE CLAIMS WITHOUT VERIFICATION** - Always verify system state before declaring success
- **Check actual API responses** after making changes to confirm fixes worked
- **Verify error counts** and system health before claiming issues are resolved
- **Use commands like** `curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'` to verify claims

## Previous Development Phase: UI Intelligence Framework (COMPLETED)

**Status**: ✅ COMPLETED - UI now showcases the sophisticated 4-phase AI system
**Goal**: Showcase the sophisticated 4-phase AI system through enhanced UI components
**Approach**: Enhanced existing UI components rather than replacing them
**Achievement**: 1,007,430+ predictions and AI capabilities now visible to users

### Phase 5 Implementation Results (COMPLETED)
1. ✅ **Intelligence panels** - added to existing dashboard spaces
2. ✅ **Enhanced bot cards** - bot cards and status displays with AI data
3. ✅ **Visualization components** - market regime indicators and performance analytics
4. ✅ **API extensions** - intelligence framework data exposed through endpoints

**NOTE**: UI Intelligence Framework is complete. Current focus is Phase 6 Centralized Data Management.

## 🛠️ API DEBUGGING BEST PRACTICES - MANDATORY 🛠️

**When API calls hang or are slow:**

❌ **NEVER DO THIS**:
- Assume the system is broken
- Restart services immediately 
- Wait indefinitely without timeouts
- Make multiple parallel slow requests

✅ **ALWAYS DO THIS**:
```bash
# 1. Use timeouts on ALL API calls
curl -s --max-time 5 "http://localhost:8000/api/endpoint"

# 2. Test simple endpoints first
curl -s --max-time 3 "http://localhost:8000/health"

# 3. Check backend logs for activity
tail -n 10 /Users/lazy_genius/Projects/trader/logs/backend.log

# 4. Check if system is processing heavy tasks
tail -n 5 /Users/lazy_genius/Projects/trader/logs/celery-worker.log

# 5. Use lightweight queries for troubleshooting
curl -s --max-time 5 "http://localhost:8000/api/v1/bots/" | jq 'length'
```

**Common Error Patterns:**
- **"Coinbase order placement returned None"**: Check logs for "limit only mode" - replace pair with market-order compatible one
- **Frontend shows "missing bots"**: Check if backend is running and bot count with `curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'`
- **Temperature display "undefined"**: Bot evaluation hasn't run yet - wait for Celery task cycle
- **Signal configuration errors**: Ensure JSON structure matches `SignalConfigurationSchema` in schemas.py

**Common Causes of Slow APIs:**
- Celery task backlog processing (normal during error cleanup)
- Database busy with bulk operations (expected)
- External API rate limiting (Coinbase throttling)
- Cache warming after restart (temporary)

**When to escalate to restart:**
- No response from simple `/health` endpoint after 30s
- Backend process not found in `ps aux`
- User explicitly requests restart
- Fatal errors in logs with no recovery

## Known Issues & Recovery

**Current Status**: ✅ All major dashboard and backend issues resolved (September 28, 2025)

**Recent Fixes Applied**:
- ✅ **Dashboard Display Fixed**: Portfolio now correctly shows "Active Pairs: 25" instead of 1
- ✅ **Bot Synchronization Fixed**: Backend evaluation tasks now properly update bot.current_combined_score in database
- ✅ **React Rendering Fixed**: Eliminated object-as-children errors in TieredBotsView component
- ✅ **Filtering Removed**: Simplified bot display to show all 25 bots without complex categorization
- ✅ **Signal Configuration**: Fixed "No enabled signals with valid weights" error in bot_evaluator.py
- ✅ **Trading Intent Display**: Fixed object rendering for trading_intent.next_action and confidence

**If System Issues Arise**:
1. **Always check health first**: `./scripts/status.sh` 
2. **Verify Docker**: System requires Docker for Redis
3. **Check database path**: Must use `/trader.db` (not backend/trader.db)
4. **Verify bot count**: Should always show 25 active bots
5. **Diagnose before restart**: Use debugging steps above
6. **Last resort restart**: `./scripts/stop.sh && ./scripts/start.sh`

For current system errors: `curl -s --max-time 10 "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'`
