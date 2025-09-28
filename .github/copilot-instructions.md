# GitHub Copilot Instructions for Auto-Trader System

## System Overview

This is a **production-ready cryptocurrency trading system** with **17 active bots** managing live funds across major trading pairs. The system features sophisticated 4-phase AI intelligence framework, triple-layer rate limiting protection, and proven profitable performance (+$87.52 in 24hrs excluding outliers).

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

# 4. Verify all 17 bots are operational
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'  # Should return 17
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
1. **17-Bot Expansion**: Added LINK, MATIC, LTC, DOT, UNI pairs successfully
2. **Rate Limiting Mastery**: Triple-layer protection (90s cache + circuit breaker + exponential backoff)
3. **Performance Optimization**: Trading thresholds optimized to ±0.05 for 2x sensitivity
4. **Profitable Operations**: +$87.52 net profit in 24hrs (excluding AVNT-USD outlier)
5. **AI Framework Active**: 451K+ predictions, 65% accuracy, 139 evaluated outcomes

### Backend Intelligence (Complete & Enhanced)
1. **Market Regime Detection**: CHOPPY regime active (-0.146 strength, 0.75 confidence)
2. **Dynamic Position Sizing**: Enhanced with regime-based adjustments across 17 pairs
3. **Signal Performance Tracking**: 451,711+ predictions with outcome evaluation system
4. **Adaptive Signal Weighting**: All 17 bots eligible for AI-driven weight optimization

## Current Development Phase: System Optimization & Monitoring

**Status**: 17-bot system operational with AI intelligence and performance optimization
**Goal**: Monitor and optimize the expanded trading system for maximum profitability
**Focus**: Performance analysis, threshold tuning, and system stability monitoring
**Priority**: Maintain profitable operations while scaling system capabilities

### Recent Optimizations (September 28, 2025)
1. **Enhanced Rate Limiting**: 90s cache TTL reducing API stress
2. **Threshold Optimization**: ±0.05 thresholds for increased trading sensitivity  
3. **Performance Monitoring**: Real-time profitability tracking and analysis
4. **System Expansion**: Successfully added 5 new pairs with proper configurations
5. **AI Framework Integration**: Full 4-phase intelligence operational across all pairs

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
- `/backend/app/services/bot_evaluator.py` - Main signal aggregation logic
- `/backend/app/models/models.py` - Database models (Bot, Trade, RawTrade)
- `/backend/app/services/market_data_cache.py` - Intelligent caching (prevents rate limits)

### Frontend Architecture  
- `/frontend/src/pages/DashboardRedesigned.tsx` - Main unified dashboard
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

## Known Issues & Recovery

**Current Status**: ✅ All major issues resolved (September 27, 2025)

**If System Issues Arise**:
1. **Always check health first**: `./scripts/status.sh` 
2. **Verify Docker**: System requires Docker for Redis
3. **Check database path**: Must use `/trader.db` (not backend/trader.db)
4. **Verify bot count**: Should always show 12 active bots
5. **Safe restart**: `./scripts/stop.sh && ./scripts/start.sh`

For current system errors: `curl "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'`
