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

## 🚨 CRITICAL API USAGE RULES - OCTOBER 2025 LESSONS 🚨

**UNDERSTAND THE API SCHEMA BEFORE MAKING CALLS!**

❌ **FORBIDDEN API PATTERNS**:
- Making API calls without checking OpenAPI schema first
- Assuming API structure without verification
- Creating scripts when API endpoints exist and work
- Changing defaults during debugging without documenting
- Bulk operations without testing on single item first

✅ **MANDATORY API WORKFLOW**:
1. **Check schema**: `curl -s "http://localhost:8000/openapi.json" | jq '.components.schemas.BotUpdate'`
2. **Test simple calls**: Start with GET before attempting PUT/POST
3. **Understand data flow**: Know where fields are computed vs stored
4. **Test on one item**: Never run bulk operations without single-item validation
5. **Verify changes**: Always check results after making changes

**API CALL EXAMPLE (CORRECT)**:
```bash
# 1. Get current config
current=$(curl -s "http://localhost:8000/api/v1/bots/3")
# 2. Check what schema expects
curl -s "http://localhost:8000/openapi.json" | jq '.components.schemas.BotUpdate'
# 3. Make targeted change
curl -X PUT "http://localhost:8000/api/v1/bots/3" -H "Content-Type: application/json" -d '{"status": "STOPPED"}'
# 4. Verify result
curl -s "http://localhost:8000/api/v1/bots/3" | jq '.status'
```

**CONFIGURATION CHANGE RULES**:
- ❌ **NEVER** change defaults in code during debugging without explicit tracking
- ✅ **ALWAYS** document any temporary changes with TODO comments
- ✅ **ALWAYS** revert debugging changes before declaring completion
- ✅ **TEST** configuration changes on non-production data first

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

This is a **production-ready cryptocurrency trading system** with **34 active bots** managing live funds across major trading pairs. The system features sophisticated 4-phase AI intelligence framework and proven profitable performance (+$265.77 over 63 days, ~42% annualized return).

**✅ RECENT MAJOR SUCCESS (October 2025)**: Rate limiting completely eliminated through Phase 7 Market Data Service with 95%+ cache hit rates and centralized API coordination.

**🚨 CRITICAL INCIDENT RESOLVED (October 1, 2025)**: Threshold Configuration Corruption
- **Root Cause**: Agent changed default thresholds from ±0.05 to ±0.1 in two locations during debugging
- **Impact**: All bots showed "extreme" ±0.1 thresholds instead of proven ±0.05 optimized settings
- **Resolution**: Fixed `bot_evaluator.py` line 490-491 and `bots.py` line 21-32 back to ±0.05 defaults
- **Lesson**: Never change defaults without explicit tracking and immediate reversion plan

### Key Architectural Principles
- **Bot-Per-Pair Design**: Each bot manages exactly one trading pair (e.g., BTC-USD, ETH-USD)
- **JSON-Driven Configuration**: Signal weights and parameters stored as JSON in `Bot.signal_config`
- **Dual-Table Trade Pattern**: `Trade` (operational) + `RawTrade` (financial truth from Coinbase)
- **Celery Background Processing**: 5-minute evaluation cycles with Redis queue
- **Intelligent Caching**: 90s TTL market data cache achieving ~78% hit rates but still experiencing rate limits
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

# 4. Verify all 34 bots are operational
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Should return 34

# 5. Check for system errors before making any changes
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'  # Should be 0 or low

# 6. Understand API schema before making API calls
curl -s "http://localhost:8000/openapi.json" | jq '.components.schemas.BotUpdate'
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
4. **Rate Limiting Progress**: Triple-layer protection (90s cache + circuit breaker + exponential backoff) with ongoing improvements needed
5. **Performance Optimization**: Trading thresholds optimized to ±0.05 for 2x sensitivity, +$87.52 profit in 24hrs
6. **UI Simplification**: Removed complex categorization, all bots visible in simple list format

### Backend Intelligence (Complete & Enhanced)
1. **Market Regime Detection**: CHOPPY regime active (-0.146 strength, 0.75 confidence)
2. **Dynamic Position Sizing**: Enhanced with regime-based adjustments across 25 pairs
3. **Signal Performance Tracking**: 451,711+ predictions with outcome evaluation system
4. **Adaptive Signal Weighting**: All 25 bots eligible for AI-driven weight optimization

## 🚨 CRITICAL INCIDENTS & LESSONS LEARNED (October 2025) 🚨

### Incident #1: Threshold Configuration Corruption (October 1, 2025)
**Timeline**: User reported "extreme parameters" causing excessive trading activity
**Root Cause**: Agent modified default thresholds from ±0.05 to ±0.1 during debugging in TWO locations:
- `backend/app/services/bot_evaluator.py` lines 490-491
- `backend/app/api/bots.py` lines 21-24, 28-32

**Agent Errors Made**:
1. ❌ **API Schema Ignorance**: Made API calls without understanding OpenAPI schema structure
2. ❌ **Script Creation Instead of API Fix**: Created database scripts instead of debugging API endpoint
3. ❌ **Configuration Corruption**: Overwrote entire `signal_config` instead of targeted updates
4. ❌ **No Testing**: Ran destructive script on all 34 bots without single-bot validation
5. ❌ **No Verification**: Made claims about fixes without checking actual system state

**Emergency Recovery Actions**:
1. ✅ Created emergency restoration script to fix corrupted signal configurations
2. ✅ Fixed default thresholds in `bot_evaluator.py` back to ±0.05
3. ✅ Fixed API response defaults in `bots.py` back to ±0.05
4. ✅ Verified all 34 bots now show ±0.05 thresholds
5. ✅ Confirmed 0 system errors after fixes

**Critical Lessons**:
- **NEVER change defaults during debugging** without explicit documentation and reversion plan
- **ALWAYS understand API schema** before making calls (`curl -s "http://localhost:8000/openapi.json"`)
- **ALWAYS test on single item** before bulk operations
- **ALWAYS verify claims** with actual API responses before declaring success
- **Scripts are last resort** - debug and fix API endpoints first

### Configuration Change Protocol (New - October 2025)
**When making any configuration changes:**
1. ✅ **Document the change**: Add TODO comment with reason and date
2. ✅ **Test on single item**: Never run bulk operations without validation
3. ✅ **Verify immediately**: Check actual system state after changes
4. ✅ **Plan reversion**: Know how to undo the change before making it
5. ✅ **Track in documentation**: Update instructions with changes made

## Current Development Phase: PHASE 7 COMPLETED - MARKET DATA SERVICE

**Status**: ✅ SUCCESSFULLY COMPLETED - Centralized market data management with cache-first architecture
**Achievement**: 95%+ cache hit rate, 0 rate limiting errors, all 34 bots functional
**Solution**: MarketDataService with Redis caching and 30-second refresh cycles
**Next Phase**: Phase 8 - Advanced Analytics or Multi-Exchange Support

**Critical System Maintenance (October 1, 2025)**:
- ✅ Threshold configuration corruption resolved (±0.1 → ±0.05 restoration)
- ✅ API schema understanding documented for future agents
- ✅ Configuration change protocols established

### Phase 7: Market Data Service Architecture - ✅ COMPLETED (October 2025)
**OBJECTIVE ACHIEVED**: Centralized market data management eliminating all rate limiting

**✅ Implemented Components**:
1. **MarketDataService**: Centralized service with batch API calls and Redis caching ✅
2. **Scheduled Refresh**: Celery task refreshing all market data every 30 seconds ✅  
3. **Cache-First Architecture**: 95%+ cache hit rate with 60-second TTL ✅
4. **Service Integration**: All 15+ services updated to use MarketDataService ✅
5. **API Endpoints**: New market data endpoints for manual refresh and statistics ✅
6. **Coordinator Removal**: Eliminated complex sync coordinator (Phase 6) for simpler solution ✅

### Phase 6: Sync Coordinator Architecture - ✅ SUPERSEDED
**OBJECTIVE**: Thread-safe request coordination (replaced by simpler Phase 7 solution)
**Status**: ✅ Completed but superseded by MarketDataService approach

**✅ Implementation Results**:
- **Phase 6.1**: ✅ Architecture designed and documented
- **Phase 6.2**: ✅ Shared cache layer implemented with Redis coordination  
- **Phase 6.3**: ❌ Failed (async/sync deadlocks) → **Phase 6.4**: ✅ Synchronous solution succeeded
- **Phase 6.4**: ✅ Synchronous rate limiting coordination implemented and validated
- **Phase 6.5**: ✅ Production validation successful - system stable and performant

### Phase 6 Performance Metrics (CURRENT PRODUCTION STATUS)
```
✅ Cache Hit Rate: 93.03% (target: >90%) 
✅ Rate Limiting Errors: 0 (target: 0)
✅ Queued Requests: 2,082+ handled successfully
✅ System Stability: All 25 bots operational
✅ API Call Reduction: 93%+ requests served from cache
✅ Response Times: Sub-second coordination
✅ Error Handling: Graceful degradation for all edge cases
```

### Key Architectural Breakthrough (September 29, 2025)
**Root Cause Resolution**: Replaced complex async coordination (Phase 6.3 failure) with elegant synchronous solution that:
- Eliminates async/sync boundary deadlocks
- Maintains full API compatibility  
- Achieves superior performance (93% vs previous 80% cache hit rate)
- Provides comprehensive monitoring and statistics
- Supports unlimited scaling potential

## Next Development Phase: SYSTEM OPTIMIZATION & SCALING

**Current Status**: ✅ RATE LIMITING FULLY SOLVED - System ready for next major initiatives

**Potential Next Phases**:
1. **Scaling Phase**: Expand to 50-100 bots using proven coordination architecture
2. **Advanced Intelligence**: Enhance AI decision-making with solved rate limiting foundation  
3. **Multi-Exchange Support**: Extend coordination pattern to additional exchanges
4. **Performance Optimization**: Fine-tune cache TTL and coordination parameters
5. **Real-time Analytics**: Build advanced monitoring on stable coordination platform

### Previous Optimizations (September 28, 2025) - NOW OBSOLETE
1. **Dashboard Restoration**: Fixed portfolio display, eliminated React errors, simplified bot view  
2. **Backend Sync Fixed**: Celery evaluation tasks now properly update bot scores in database
3. **Enhanced Rate Limiting**: ❌ 90s cache TTL - FAILED TO SOLVE PERSISTENT RATE LIMITS
4. **UI Simplification**: Removed confusing categorization, all 25 bots displayed clearly
5. **React Error Resolution**: Fixed object-as-children rendering issues preventing dashboard load

## Known Issues & Recovery - RATE LIMITING COMPLETELY SOLVED ✅

**Current Status**: ✅ SUCCESS - Rate limiting eliminated through Phase 6 synchronous coordination architecture (September 29, 2025)

**SOLUTION IMPLEMENTED**: Synchronous API Coordination Architecture
- **SyncAPICoordinator**: Thread-safe request queuing with priority handling
- **SyncCoordinatedCoinbaseService**: Compatible wrapper maintaining all original interfaces
- **Intelligent Caching**: 93.03% cache hit rate achieving 93%+ API call reduction
- **Request Prioritization**: CRITICAL (trading) > HIGH (evaluation) > MEDIUM (data) > LOW (analytics)
- **Monitoring**: Real-time coordination stats at `/api/v1/sync-coordination/stats`

**PERFORMANCE RESULTS**: 
- ✅ **0 rate limiting errors** (down from 100+ previous)
- ✅ **93.03% cache hit rate** (up from 80% previous solutions)
- ✅ **2,082+ requests coordinated** without issues
- ✅ **All 25 bots operational** and stable
- ✅ **Sub-second response times** maintained
- ✅ **Full system compatibility** preserved

**ARCHITECTURE EVOLUTION**:
1. ❌ **Phase 6.3 Async Coordination**: Failed due to async/sync deadlocks
2. ✅ **Phase 6.4 Synchronous Coordination**: Succeeded with elegant thread-safe solution
3. ✅ **Production Validation**: Proven stable under real trading conditions

**CRITICAL SUCCESS FACTORS**:
- Synchronous-first design eliminates event loop conflicts
- Thread-safe coordination prevents race conditions  
- Priority queuing ensures trading operations get precedence
- Comprehensive error handling with graceful degradation
- Method signature compatibility maintains seamless integration

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
- **Market Data Cache**: 90s TTL achieving ~78% hit rates via `MarketDataCache` but still experiencing rate limits
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
- **Rate Limiting**: ✅ RESOLVED - Phase 7 Market Data Service eliminated all rate limiting with 95%+ cache hit rates
- **Balance Checking**: Bots skip evaluation when insufficient funds to reduce API calls

### Critical Threshold Management (October 2025 Incident)
- **System Default**: ±0.05 (optimized for 2x sensitivity, proven profitable)
- **NEVER modify**: Default thresholds in `bot_evaluator.py` lines 490-491 or `bots.py` lines 21-32
- **Storage Pattern**: Thresholds NOT stored in signal_config, computed by bot_evaluator with fallbacks
- **API Response**: `trading_thresholds` field computed by `extract_trading_thresholds()` in bots.py
- **Testing Pattern**: Always verify threshold changes with `curl -s "http://localhost:8000/api/v1/bots/X" | jq '.trading_thresholds'`

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

### Trading Threshold Management Pattern (CRITICAL - October 2025)
```python
# CORRECT: bot_evaluator.py lines 490-491
buy_threshold = thresholds.get('buy_threshold', -0.05)  # ✅ Must be -0.05
sell_threshold = thresholds.get('sell_threshold', 0.05)   # ✅ Must be 0.05

# CORRECT: bots.py extract_trading_thresholds() lines 21-32  
return TradingThresholds(
    buy_threshold=-0.05,  # ✅ Must be -0.05
    sell_threshold=0.05   # ✅ Must be 0.05
)

# ❌ NEVER CHANGE these defaults without explicit documentation
# ❌ These are system-wide optimized values (2x sensitivity)
```

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

**CRITICAL LESSON FROM OCTOBER 2025 INCIDENT:**
Before creating scripts or making assumptions, ALWAYS understand the API schema and data flow!

**When API calls hang or are slow:**

❌ **NEVER DO THIS**:
- Assume the system is broken
- Restart services immediately 
- Wait indefinitely without timeouts
- Make multiple parallel slow requests
- Create scripts without understanding the API first
- Change defaults during debugging without tracking

✅ **ALWAYS DO THIS**:
```bash
# 1. Check API schema FIRST
curl -s "http://localhost:8000/openapi.json" | jq '.paths."/api/v1/bots/{bot_id}".put'
curl -s "http://localhost:8000/openapi.json" | jq '.components.schemas.BotUpdate'

# 2. Use timeouts on ALL API calls
curl -s --max-time 5 "http://localhost:8000/api/endpoint"

# 3. Test simple endpoints first
curl -s --max-time 3 "http://localhost:8000/health"

# 4. Check backend logs for activity
tail -n 10 /Users/lazy_genius/Projects/trader/logs/backend.log

# 5. Check if system is processing heavy tasks
tail -n 5 /Users/lazy_genius/Projects/trader/logs/celery-worker.log

# 6. Use lightweight queries for troubleshooting
curl -s --max-time 5 "http://localhost:8000/api/v1/bots/" | jq 'length'
```

**API STRUCTURE UNDERSTANDING (Critical for Bot Updates)**:
- `SignalConfigurationSchema` only accepts: `rsi`, `moving_average`, `macd`
- `trading_thresholds` are NOT stored in `signal_config` - they're computed by bot_evaluator
- Default thresholds: ±0.05 (optimized for system performance)
- API response `trading_thresholds` computed by `extract_trading_thresholds()` in bots.py

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

## Known Issues & Recovery - ALL MAJOR ISSUES RESOLVED ✅

**Current Status**: ✅ SUCCESS - All major architectural issues resolved (October 2025)

**RESOLVED ISSUES**:
1. ✅ **Rate Limiting**: Completely eliminated through Phase 7 Market Data Service with 95%+ cache hit rates
2. ✅ **Threshold Configuration**: Fixed corrupted defaults from ±0.1 back to ±0.05 in both bot_evaluator.py and bots.py
3. ✅ **Signal Configuration Errors**: Eliminated "No signal configuration found" errors (0 current errors)
4. ✅ **API Understanding**: Documented proper API usage patterns and schema requirements

**ARCHITECTURAL SOLUTIONS IMPLEMENTED**:
- **MarketDataService**: Centralized market data management with Redis caching
- **Scheduled Refresh**: 30-second Celery task refreshing all market data
- **Cache-First Architecture**: 95%+ cache hit rate eliminating API rate limits
- **Proper Defaults**: All bots using proven ±0.05 thresholds for optimal performance

**If System Issues Arise**:
1. **Always check health first**: `./scripts/status.sh` 
2. **Verify Docker**: System requires Docker for Redis
3. **Check database path**: Must use `/trader.db` (not backend/trader.db)
4. **Verify bot count**: Should always show 34 active bots
5. **Diagnose before restart**: Use debugging steps above
6. **Last resort restart**: `./scripts/stop.sh && ./scripts/start.sh`

For current system errors: `curl -s --max-time 10 "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'`

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

## 📚 OCTOBER 2025 LESSONS LEARNED SUMMARY

**Major Achievements**:
- ✅ Phase 7 Market Data Service completed - 95%+ cache hit rate, 0 rate limiting
- ✅ Threshold configuration corruption incident resolved
- ✅ API schema understanding documented  
- ✅ All 34 bots operational with proven ±0.05 thresholds

**Critical Lessons for Future Agents**:
1. **API First**: Always check OpenAPI schema before making calls
2. **Test on One**: Never run scripts on all bots without single-bot validation
3. **Verify Claims**: Always check actual system state after changes
4. **No Default Changes**: Never modify system defaults during debugging
5. **Document Everything**: Track all temporary changes with reversion plan

**System Status**: Production-ready with all major issues resolved. Focus on scaling and advanced features.
