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

This is a **production-ready cryptocurrency trading system** with **25 active bots** managing live funds across major trading pairs. The system features sophisticated 4-phase AI intelligence framework, triple-layer rate limiting protection, and evolving performance characteristics.

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

## Essential Development Patterns

### Bot-Per-Pair Architecture
Each `Bot` entity manages exactly one trading pair with dynamic signal configuration stored as JSON in `Bot.signal_config`. Signals are created via factory pattern in `/backend/app/services/signals/base.py`.

### Dual-Table Data Pattern (CRITICAL)
- **Trade Table**: Operational data (bot decisions, signals)  
- **RawTrade Table**: Financial truth (exact Coinbase fills) - AUTO-SYNCED
- **Database Location**: `/trader.db` at project root (NOT backend/trader.db)

### Signal Scoring System
- **Range**: -1.0 (BUY signal) to +1.0 (SELL signal)
- **Thresholds**: ±0.05 system-wide (optimized for sensitivity)
- **Temperature**: 🔥HOT/🌡️WARM/❄️COOL/🧊FROZEN based on signal scores

## Intelligence Framework Status (September 28, 2025)

✅ **ALL 4 BACKEND PHASES COMPLETED + RECENT EXPANSION**

### Recent Major Achievements (Sept 27-28, 2025)
1. **Dashboard Fixes**: Fixed Active Pairs count (now shows 25), eliminated React rendering errors, simplified bot display
2. **Backend Synchronization**: Fixed evaluate_bot_signals and fast_trading_evaluation to update database properly  
3. **17-Bot System Operational**: All 25 bots displaying correctly with proper signal data
4. **Rate Limiting Mastery**: Triple-layer protection (90s cache + circuit breaker + exponential backoff)
5. **Performance Optimization**: Trading thresholds optimized to ±0.05 for 2x sensitivity
6. **UI Simplification**: Removed complex categorization, all bots visible in simple list format

### Backend Intelligence (Complete & Enhanced)
1. **Market Regime Detection**: CHOPPY regime active (-0.146 strength, 0.75 confidence)
2. **Dynamic Position Sizing**: Enhanced with regime-based adjustments across 17 pairs
3. **Signal Performance Tracking**: 451,711+ predictions with outcome evaluation system
4. **Adaptive Signal Weighting**: All 17 bots eligible for AI-driven weight optimization

## Current Development Phase: System Optimization & Monitoring

**Status**: 25-bot system operational with simplified UI and fixed synchronization
**Goal**: Monitor and optimize the stable trading system for maximum profitability
**Focus**: Dashboard functionality restored, all bots visible, data properly synchronized
**Priority**: Maintain profitable operations with clear, functional user interface

### Recent Optimizations (September 28, 2025)
1. **Dashboard Restoration**: Fixed portfolio display, eliminated React errors, simplified bot view
2. **Backend Sync Fixed**: Celery evaluation tasks now properly update bot scores in database
3. **Enhanced Rate Limiting**: 90s cache TTL reducing API stress
4. **UI Simplification**: Removed confusing categorization, all 25 bots displayed clearly
5. **React Error Resolution**: Fixed object-as-children rendering issues preventing dashboard load

## Known Issues & Recovery

**Current Status**: ✅ All major issues resolved (September 28, 2025)

**Recent Solutions Implemented**:
1. **Rate Limiting**: Triple-layer protection eliminates 429 errors
2. **Signal Configuration**: Proper JSON structure for all 17 bots
3. **Performance Tracking**: Real-time P&L monitoring operational
4. **Threshold Optimization**: Increased trading frequency through sensitivity tuning
5. **Cache Enhancement**: 90s TTL improving API performance

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

## Current Development Phase: UI Intelligence Framework

**Status**: Moving from backend intelligence to user-facing features
**Goal**: Showcase the sophisticated 4-phase AI system through enhanced UI components
**Approach**: Enhance existing UI components rather than replacing them
**Priority**: Make 139,711+ predictions and AI capabilities visible to users

### Phase 5 Implementation Strategy
1. **Non-disruptive enhancements** - add intelligence panels to existing dashboard spaces
2. **Extend existing components** - enhance bot cards and status displays with AI data
3. **New visualization components** - market regime indicators and performance analytics
4. **API extensions** - expose intelligence framework data through existing endpoints

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
