# GitHub Copilot Instructions for Auto-Trader System

## 🚨 CRITICAL AGENT RULES 🚨

**NEVER MAKE CLAIMS WITHOUT VERIFICATION!** Always verify system state before declaring success.

**MANDATORY VERIFICATION WORKFLOW:**
1. Check health: `./scripts/status.sh`
2. Verify bots: `curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'` (should be 41)
3. Check errors: `curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'`
4. Always use actual API responses to confirm changes worked

**If system is slow/hanging:** Use timeouts (`curl -s --max-time 5`) and diagnose BEFORE restarting services.

## System Overview

**Production-ready cryptocurrency trading system** with **41 active bots** managing live funds across major trading pairs. Features sophisticated 4-phase AI intelligence and proven profitable performance.

**✅ CURRENT STATUS (October 2025)**: System fully operational with 41 bots, UI consolidation project completed. Clean 3-tab navigation with integrated bot management, comprehensive trade center, and optimized Portfolio card with P&L display.

### Core Architecture
- **Backend**: FastAPI + SQLAlchemy + Celery/Redis + MarketDataService
- **Frontend**: React 18 + TypeScript + TanStack Query with clean 3-tab navigation (Dashboard/Trades/Market Analysis)
- **Database**: Single SQLite file at `/trader.db` (NOT backend/trader.db)
- **Caching**: Phase 7 MarketDataService with Redis (60s TTL) + legacy MarketDataCache (90s TTL)
- **Bot Design**: One bot per trading pair, JSON signal configs, ±0.05 thresholds
- **UI Architecture**: Consolidated dashboard with integrated bot management, comprehensive Portfolio card with P&L tracking

### Key Architectural Principles
- **Dual-Table Pattern**: `Trade` (operational) + `RawTrade` (Coinbase truth)
- **Signal Factory Pattern**: Dynamic signal creation via `create_signal_instance()` in `/backend/app/services/signals/base.py`
  - Maps: `'rsi'` → `RSISignal`, `'moving_average'` → `MovingAverageSignal`, `'macd'` → `MACDSignal`
  - Parameters extracted from Bot.signal_config JSON, excluding 'enabled' and 'weight'
- **Centralized Market Data**: MarketDataService reduces (but doesn't eliminate) rate limiting
- **Real-Time Frontend**: 5-second polling more reliable than WebSocket
- **Service Coordination**: Global service instances with dependency injection pattern
- **Phase 7 Caching**: 30-second batch refresh cycles via Celery

## 🚨 CRITICAL FIRST STEPS FOR AI AGENTS

```bash
# 1. ALWAYS check system health first (before any changes)
./scripts/status.sh

# 2. Configure Python environment (REQUIRED before Python operations)  
# Use configure_python_environment tool

# 3. Start services if needed
./scripts/start.sh

# 4. Verify all 41 bots are operational
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Should return 41

# 5. Check for system errors before making any changes
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'  # Should be 0 or low

# 6. Understand API schema before making API calls
curl -s "http://localhost:8000/openapi.json" | jq '.components.schemas.BotUpdate'
```

## 🚨 RATE LIMITING TROUBLESHOOTING

**If experiencing rate limit errors:**

```bash
# 1. Check current error status
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq 'length'

# 2. Monitor cache performance 
curl -s "http://localhost:8000/api/v1/cache/stats" | jq

# 3. Check market data service status
curl -s "http://localhost:8000/api/v1/market-data/stats" | jq

# 4. If persistent, restart services
./scripts/restart.sh

# 5. Monitor logs for rate limit patterns
tail -f logs/backend.log | grep -i "rate\|limit\|429"
```

**Common Rate Limit Scenarios:**
- High bot activity during market volatility
- Coinbase API maintenance periods  
- Cache misses during system restarts
- Multiple concurrent bot evaluations

## Essential Project Startup

**Automated (Recommended):**
```bash
./scripts/start.sh    # Starts all services
./scripts/status.sh   # Verify health
./scripts/logs.sh     # Monitor logs
```

**Manual (For debugging):**
```bash
# Terminal 1: Redis
docker-compose up redis

# Terminal 2: Backend  
cd backend && source venv/bin/activate  
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Celery Worker
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 4: Celery Beat
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 5: Frontend
cd frontend && npm run dev
```

## Essential Development Patterns

### Phase 7 Market Data Service (Current Production)
```python
# Global service instance pattern (industry standard)
from backend.app.services.market_data_service import get_market_data_service
market_service = get_market_data_service()

# Centralized batch fetching every 30 seconds via Celery
# Redis cache with 60-second TTL achieving 95%+ hit rates
# API endpoints: /api/v1/market-data/stats, /api/v1/market-data/refresh
```

### Bot Configuration Pattern
```python
# Each Bot.signal_config contains JSON like:
{
  "rsi": {"enabled": true, "weight": 0.4, "period": 14},
  "moving_average": {"enabled": true, "weight": 0.35},
  "macd": {"enabled": true, "weight": 0.25},
  "trading_thresholds": {"buy_threshold": -0.05, "sell_threshold": 0.05}
}

# Signals created via factory pattern in /backend/app/services/signals/base.py
```

### Dual-Table Data Pattern (CRITICAL)
- **Trade Table**: Operational data (bot decisions, signals) 
- **RawTrade Table**: Financial truth (exact Coinbase fills) - AUTO-SYNCED
- **Database Location**: `/trader.db` at project root (NOT backend/trader.db)

### Signal Scoring System
- **Range**: -1.0 (BUY signal) to +1.0 (SELL signal)
- **Thresholds**: ±0.05 system-wide (optimized for sensitivity) 
- **Temperature**: 🔥HOT/🌡️WARM/❄️COOL/🧊FROZEN based on signal scores
- **Aggregation**: Weighted combination of RSI, Moving Average, and MACD

### API Response Pattern
```python
# Bot API returns computed fields not stored in DB
{
  "current_combined_score": -0.087,  # From bot_evaluator calculation
  "temperature": "🔥HOT",            # From temperature utils
  "trading_thresholds": {...},       # Extracted from signal_config JSON
  "signal_config": {...}             # Parsed from JSON string
}
```

## Development Workflows

### Essential Scripts
```bash
# Full validation after changes (REQUIRED)
./scripts/test-workflow.sh  # Restart → Health → API → Signal → Frontend tests

# Rapid iteration testing  
./scripts/quick-test.sh

# Real-time debugging
./scripts/logs.sh  # Tails all service logs simultaneously

# Signal testing by category
python backend/tests/test_runner.py [rsi|ma|macd|aggregation|all]

# Core service health checks
./scripts/status.sh  # Port checks, PID files, service status
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | jq
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
- **CRITICAL PATH**: `/trader.db` at project root (NEVER `backend/trader.db`)
  - Config: `DATABASE_URL="sqlite:////Users/lazy_genius/Projects/trader/trader.db"` (absolute path)
  - Engine: `from ..core.database import engine, Base` in main.py
  - Session: `SessionLocal` factory with dependency injection via `get_db()`
- **Manual Migrations**: SQLAlchemy schema changes only, no automatic migrations
- **Auto-Sync**: Both Trade and RawTrade tables update automatically
- **Service Architecture**: Global instances (MarketDataService, CoinbaseService) with session injection

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
- **Rate Limiting**: ⚠️ ONGOING ISSUE - Despite Phase 7 Market Data Service, still experiencing Coinbase API rate limits
  - Monitor with: `curl -s "http://localhost:8000/api/v1/cache/stats" | jq`
  - Check error logs: `curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq`
  - Restart services if persistent: `./scripts/restart.sh`
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
# Located: /backend/app/services/signals/base.py
from backend.app.services.signals.base import create_signal_instance

# Bot.signal_config JSON structure:
{
  "rsi": {"enabled": true, "weight": 0.4, "period": 14, "buy_threshold": 30, "sell_threshold": 70},
  "moving_average": {"enabled": true, "weight": 0.35, "fast_period": 10, "slow_period": 20},
  "macd": {"enabled": true, "weight": 0.25, "fast_period": 12, "slow_period": 26, "signal_period": 9}
}

# Factory usage in BotSignalEvaluator._create_signal_instance():
signal_type_map = {'rsi': 'RSI', 'moving_average': 'MA_Crossover', 'macd': 'MACD'}
parameters = {k: v for k, v in config.items() if k not in ['enabled', 'weight']}
signal_instance = create_signal_instance(signal_type_map[signal_name], parameters)
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

### Signal Factory Pattern
```python
# Located: /backend/app/services/signals/base.py
from backend.app.services.signals.base import create_signal_instance

# Bot.signal_config JSON structure:
{
  "rsi": {"enabled": true, "weight": 0.4, "period": 14, "buy_threshold": 30, "sell_threshold": 70},
  "moving_average": {"enabled": true, "weight": 0.35, "fast_period": 10, "slow_period": 20},
  "macd": {"enabled": true, "weight": 0.25, "fast_period": 12, "slow_period": 26, "signal_period": 9}
}

# Factory usage in BotSignalEvaluator._create_signal_instance():
signal_type_map = {'rsi': 'RSI', 'moving_average': 'MA_Crossover', 'macd': 'MACD'}
parameters = {k: v for k, v in config.items() if k not in ['enabled', 'weight']}
signal_instance = create_signal_instance(signal_type_map[signal_name], parameters)
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

## Previous Development Phase: UI Consolidation Project (COMPLETED)

**Status**: ✅ COMPLETED - October 3, 2025
**Goal**: Consolidate redundant UI elements and create clean 3-tab navigation
**Achievement**: Complete UI consolidation with integrated bot management and comprehensive trade center

### UI Consolidation Results (COMPLETED)
1. ✅ **Auto Bot Scanner Removal** - Eliminated redundant automation, added manual Create Bot buttons
2. ✅ **Market Analysis Enhancement** - Added Create Bot functionality to trading pairs
3. ✅ **System Health Optimization** - Compacted SystemHealthCard, fixed Redis connections
4. ✅ **Market Overview Elimination** - Removed redundant MarketTicker component
5. ✅ **Intelligence Framework Optimization** - Moved to top, reduced footprint, grid integration
6. ✅ **Portfolio Card Enhancement** - Added P&L display with 3-column layout

**Final State**: Clean 3-tab navigation (Dashboard/Trades/Market Analysis) with:
- **Dashboard**: Integrated bot management, portfolio summary with P&L, system health, AI intelligence
- **Trades**: Comprehensive trading center with 5,638+ trade history
- **Market Analysis**: Trading pairs analysis with manual bot creation capabilities

**NOTE**: UI Consolidation is complete. System ready for next phase development.

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

## Known Issues & Recovery

**Current Status**: ⚠️ Rate limiting issues persist despite Phase 7 optimizations (October 2025)

**CURRENT ISSUES**:
1. ⚠️ **Rate Limiting**: Still experiencing Coinbase API rate limits despite Phase 7 Market Data Service
   - Cache hit rates are high but not eliminating all API calls
   - Monitor with: `curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq`
   - Restart if persistent: `./scripts/restart.sh`

**RESOLVED ISSUES**:
1. ✅ **Threshold Configuration**: Fixed corrupted defaults from ±0.1 back to ±0.05 in both bot_evaluator.py and bots.py
2. ✅ **Signal Configuration Errors**: Eliminated "No signal configuration found" errors
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
- `/backend/app/services/market_data_service.py` - **Phase 7**: Centralized Redis-based market data with batch API calls
- `/backend/app/services/market_data_cache.py` - Thread-safe LRU cache (Phase 1 implementation, 90s TTL)
- `/backend/app/services/sync_coordinated_coinbase_service.py` - **Phase 6.4**: Synchronous API coordination wrapper
- `/backend/app/services/sync_api_coordinator.py` - Thread-safe request queuing with priority handling

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

**System Status**: Production-ready with 34 bots operational, but rate limiting issues require ongoing monitoring and occasional restarts.
