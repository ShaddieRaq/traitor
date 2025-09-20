# GitHub Copilot Instructions for Auto-Trader System

## System Overview

This is a **production-ready autonomous cryptocurrency trading system** with 11 active trading bots managing $XXX+ across multiple cryptocurrency pairs. The system achieved significant returns through sophisticated signal processing and risk management.

### Core Architecture
- **Backend**: FastAPI + SQLAlchemy ORM + Celery/Redis for background tasks
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS with TanStack Query (5-second polling)
- **Database**: Single unified SQLite file (`/trader.db`) with models in `/backend/app/models/models.py`
- **API Structure**: RESTful with `/api/v1/` prefix, feature-organized routes in `/backend/app/api/`
- **Real-time Architecture**: 5-second polling (proven more reliable than WebSocket for this use case)
- **Testing**: 185+ comprehensive tests with signal validation and live API integration
- **Caching Layer**: Market data caching with 30-second TTL achieving 96%+ hit rates (eliminates rate limiting)

### Essential Development Context
- **Bot-Per-Pair Architecture**: Each `Bot` entity manages exactly one trading pair (11 active bots)
- **Smart Caching Pattern**: Market data cached with 30s TTL via `MarketDataCache` - 97% API call reduction
- **Balance Pre-Check Optimization**: Bots skip signal processing when insufficient balance (~60% API reduction)
- **Signal Factory Pattern**: Dynamic signal creation via `create_signal_instance()` in `/backend/app/services/signals/base.py`
- **Temperature-Based UI**: Real-time activity indicators (🔥HOT, 🌡️WARM, ❄️COOL, 🧊FROZEN) driven by signal scores
- **Unified Database**: Single `/trader.db` file - **CRITICAL: No longer multiple database files**
- **Consolidated Dashboard**: Single main dashboard at root route with stable charts and live data integration
- **Chart Stability**: Fixed oscillating behavior - all charts use deterministic data generation

## Bot-Centric Design Patterns

### Signal System Architecture
Each `Bot` entity manages one trading pair with:
- **Weighted Signal Aggregation**: RSI, Moving Average, MACD with configurable weights
- **Signal Confirmation**: Requires consistency over `confirmation_minutes` before trading
- **Position Management**: Multi-tranche position building in `Trade.position_tranches` (JSON)
- **Risk Controls**: Stop-loss, take-profit, cooldown periods, position limits

**Key Pattern**: Factory-based signal creation in `/backend/app/services/signals/base.py`:
```python
# Signal instances created dynamically from Bot.signal_config JSON
signal_instance = create_signal_instance(signal_type, parameters)
```

### Critical Data Models & Relationships
- **Bot**: Core entity with `signal_config` JSON field for dynamic signal configuration
- **BotSignalHistory**: Time-series signal scores for confirmation tracking
- **Trade**: Enhanced with `position_tranches`, `average_entry_price`, `tranche_number`
- **RawTrade**: Clean Coinbase transaction data (preferred for P&L calculations)
- **MarketData**: OHLCV candlestick data for technical analysis

### Signal Scoring System
- **Range**: -1.0 (strong sell) to +1.0 (strong buy)
- **Aggregation**: Weighted sum of individual signal scores
- **Thresholds**: Temperature-based (🔥🌡️❄️🧊) with testing vs production modes
- **Testing Thresholds**: 10x more sensitive (HOT ≥0.08, WARM ≥0.03, COOL ≥0.005)
- **Production Thresholds**: Conservative (HOT ≥0.3, WARM ≥0.15, COOL ≥0.05)

### Core Service Dependencies
- **BotSignalEvaluator**: Main signal aggregation in `/backend/app/services/bot_evaluator.py`
- **MarketDataCache**: Intelligent caching service (`/backend/app/services/market_data_cache.py`) - 30s TTL, LRU eviction
- **TradingService**: Order execution & position management 
- **CoinbaseService**: API integration with JWT authentication + caching layer
- **TradingSafetyService**: Risk management and circuit breakers

## Operational Commands & Scripts

### Management Scripts (`/scripts/`)
```bash
# Primary operational workflows
./scripts/setup.sh           # Initial environment setup
./scripts/start.sh            # Start all services (Redis, backend, frontend, Celery)
./scripts/stop.sh             # Stop all services
./scripts/status.sh           # Service health check
./scripts/logs.sh             # Application logs

# Testing workflows  
./scripts/test-workflow.sh    # Complete validation workflow (restart, test, sync, position check)
./scripts/quick-test.sh       # Rapid validation for development iterations
./scripts/position-reconcile.sh  # Position tracking validation and correction
```

### Key Development Commands
```bash
# Backend development (from /backend)
python -m app.main                    # Start FastAPI server
python tests/test_runner.py all      # Run comprehensive signal tests 
celery -A app.tasks.celery_app worker # Start background worker

# Frontend development (from /frontend)
npm run dev                          # Vite development server
npm run build                        # Production build

# Testing specific signal categories
python tests/test_runner.py rsi            # RSI signal tests only
python tests/test_runner.py aggregation    # Signal aggregation tests
```

### Critical API Endpoints for Debugging
```bash
# System health & status
curl "http://localhost:8000/api/v1/bot-evaluation/recent-evaluations" | jq
curl "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'
curl "http://localhost:8000/api/v1/bots/status/enhanced" | jq  # Real-time bot status

# Cache performance monitoring (NEW)
curl "http://localhost:8000/api/v1/cache/stats" | jq  # Cache hit rates, API savings
curl "http://localhost:8000/api/v1/cache/info" | jq   # Detailed cache entries
curl "http://localhost:8000/api/v1/cache/rate-limiting-status" | jq  # Rate limit health

# Trade & position management (CURRENT DATA)
curl "http://localhost:8000/api/v1/raw-trades/pnl-by-product" | jq  # Current performance data
curl "http://localhost:8000/api/v1/raw-trades/stats" | jq  # Overall trade statistics
curl "http://localhost:8000/api/v1/position-reconciliation/discrepancies" | jq  # Position sync issues

# Bot temperature & scoring
curl "http://localhost:8000/api/v1/bots/" | jq '.[] | {name, status, current_combined_score}'

# DEPRECATED (stale data)
# curl "/api/v1/trades/bot/{id}/performance"  # Uses deprecated Trade table
```

## Critical Service Integration Points

### Coinbase API Integration
- **Service Layer**: `/backend/app/services/coinbase_service.py` - Core API interactions
- **Authentication**: JWT-based for Coinbase Advanced Trade API
- **Caching Strategy**: MarketDataCache with 30s TTL achieving 96%+ hit rates
- **Rate Limiting**: **RESOLVED** - Intelligent caching eliminates 429 errors (97% API reduction)
- **Order Management**: `/backend/app/services/order_monitoring_service.py` for status sync

### Signal Processing Pipeline  
1. **Market Data Fetch**: REST API → `MarketData` model storage
2. **Signal Evaluation**: `/backend/app/services/bot_evaluator.py` aggregates weighted signals
3. **Confirmation Check**: Time-based validation via `BotSignalHistory` 
4. **Trade Execution**: `/backend/app/services/trading_service.py` → Coinbase API
5. **Position Tracking**: Multi-tranche support in `Trade.position_tranches`

### Background Job Architecture
- **Celery Tasks**: `/backend/app/tasks/` - 30-second interval order sync
- **Redis Queue**: Background processing for order monitoring, position reconciliation
- **Position Reconciliation**: `/backend/app/services/position_reconciliation_service.py`

### Frontend Real-time Architecture
- **Unified Main Dashboard**: Single dashboard at root route (`/`) with consolidated UX
- **Chart Stability**: All charts use deterministic data generation (no oscillating behavior)
- **Live Data Integration**: Real portfolio values from Coinbase API via `useLivePortfolio` hook
- **Enhanced Bot Cards**: Expandable cards with clear signal summaries instead of confusing charts
- **TanStack Query Polling**: 5-second intervals proven more reliable than WebSocket
- **Aggressive Polling Pattern**: `staleTime: 0`, `refetchIntervalInBackground: true`
- **Fresh Data Strategy**: No caching - backend calculates fresh signals on each request
- **State Management**: Server state via TanStack Query, minimal client state
- **Activity Feed**: Sticky panel (`StickyActivityPanel`) with live bot status updates
- **Error Handling**: Toast notifications with extended display for errors
- **Component Structure**: `/frontend/src/pages/DashboardRedesigned.tsx` as main dashboard
- **API Hooks**: Centralized in `/frontend/src/hooks/` using TanStack Query patterns

**Critical Frontend Pattern**: All data hooks use aggressive polling:
```typescript
export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: () => api.get('/bots/status/summary'),
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0  // Always fetch fresh data
  });
};
```

## Development Environment & Setup

### Essential First Steps for AI Agents
```bash
# 1. Configure Python environment (CRITICAL: Do this first)
# Use configure_python_environment tool before any Python operations

# 2. System health check
./scripts/status.sh

# 3. Start all services if needed
./scripts/start.sh

# 4. Verify database path
python -c "
from app.core.config import Settings
settings = Settings()
print(f'Database URL: {settings.database_url}')
"

# 5. Check bot visibility (should see 11 bots)
curl -s "http://localhost:8000/api/v1/bots/" | jq 'length'
```

### Development Workflow Patterns
- **Always use `./scripts/test-workflow.sh`** after any significant changes
- **Use `./scripts/quick-test.sh`** for rapid iteration during development
- **Check `./scripts/status.sh`** when services seem unresponsive
- **Monitor `./scripts/logs.sh`** for real-time debugging
- **Database changes**: Manual SQLAlchemy migrations only (no automatic migrations)

## Project-Specific Patterns & Conventions

### Signal Configuration Pattern
Bot signal weights stored as JSON in `Bot.signal_config`:
```json
{
  "RSI": {"weight": 0.4, "period": 14, "oversold": 30, "overbought": 70},
  "MA_Crossover": {"weight": 0.3, "short_period": 10, "long_period": 30},
  "MACD": {"weight": 0.3, "fast": 12, "slow": 26, "signal": 9}
}
```

### Temperature System Pattern
- **Calculation**: Single source in `/backend/app/utils/temperature.py`
- **Thresholds**: FROZEN (<0.05), COOL (≥0.05), WARM (≥0.15), HOT (≥0.3)
- **Usage**: Bot activity indicators with emoji mapping (🧊❄️🌡️🔥)

### Position Management Pattern
Enhanced multi-tranche position tracking:
```python
# Trade.position_tranches JSON structure
[
  {"entry_price": 50000, "size": 0.001, "timestamp": "2025-09-15T10:00:00Z"},
  {"entry_price": 49500, "size": 0.001, "timestamp": "2025-09-15T11:00:00Z"}
]
```

### API Conventions
- **Fresh Data Philosophy**: `/api/v1/bots/status/enhanced` recalculates all values on request
- **Error Tracking**: System errors auto-logged to `/api/v1/system-errors/errors`
- **Trade Sync**: Manual sync via `/api/v1/trades/update-statuses`
- **Health Checks**: Real-time status via `/api/v1/diagnosis/trading-diagnosis`

## Known Issues & Critical Context

### ⚠️ CRITICAL AI AGENT WARNINGS - UPDATED SEPTEMBER 20, 2025

**SYSTEM ARCHITECTURE STATUS**:
- ✅ **Single Database**: `/trader.db` is the authoritative database (no backend/trader.db split)
- ✅ **Unified Configuration**: All services use main database at project root
- ✅ **11 Active Bots**: All bots operational across major trading pairs (BTC, ETH, SOL, XRP, DOGE, AVNT, AERO, SUI, AVAX, TOSHI)
- ✅ **Rate Limiting Resolved**: Intelligent market data caching with 96%+ hit rates
- ✅ **Real-time P&L**: Live profit/loss tracking via clean `raw_trades` data

**CURRENT API USAGE GUIDELINES**:
- ✅ **Primary Data Source**: `/api/v1/raw-trades/pnl-by-product` for performance data
- ✅ **Bot Status**: `/api/v1/bots/status/enhanced` for real-time bot information  
- ✅ **Cache Monitoring**: `/api/v1/cache/stats` for performance metrics
- ✅ **Database Path**: Always use `/trader.db` (absolute: `/Users/lazy_genius/Projects/trader/trader.db`)
- ⚠️ **Legacy APIs**: Some `/api/v1/trades/` endpoints may have stale data - verify before use

**AI AGENT DEVELOPMENT GUIDELINES**:
- Always verify API endpoints return data before suggesting them
- Use `configure_python_environment` tool before Python operations
- Database schema changes require manual column additions via SQLAlchemy
- All 11 bots should be visible - if not, check unified database connection
- When debugging, start with `./scripts/status.sh` for service health

### Current Major Issues

**System Status**: ✅ **ALL MAJOR ISSUES RESOLVED**
- ✅ **Rate Limiting**: Intelligent market data caching eliminates 429 errors (97% API reduction)
- ✅ **Order Synchronization**: 30-second Celery task handles automatic updates
- ✅ **Database Integrity**: Single unified database with clean `raw_trades` data
- ✅ **Balance Pre-Check Optimization**: Bots skip signal processing when insufficient balance

**For Current Issues Check**:
```bash
# System health status
./scripts/status.sh

# Recent system errors  
curl "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'

# Cache performance (should show 90%+ hit rates)
curl "http://localhost:8000/api/v1/cache/stats" | jq
```

### Testing & Validation Approach

**Test Coverage**: 185+ tests with categories:
- **Signal Accuracy**: Mathematical validation for RSI, MA, MACD
- **Aggregation Logic**: Weighted signal combination correctness
- **Live API Integration**: Real Coinbase API connectivity tests
- **Position Reconciliation**: Database vs exchange position validation

**Test Execution Patterns**:
```bash
# Full system validation (required after changes)
./scripts/test-workflow.sh

# Development iteration testing
./scripts/quick-test.sh  

# Targeted signal testing
python tests/test_runner.py [rsi|ma|macd|aggregation|all]
```

### Trading Issue Resolution Tools

**Signal Lock Management**:
```bash
# Check for stuck signal confirmation states
python scripts/fix_signal_locks.py --check

# Auto-fix detected signal locks
python scripts/fix_signal_locks.py --fix

# Continuous monitoring mode
python scripts/fix_signal_locks.py --monitor
```

**Position Accuracy Tools**:
```bash
# Check position discrepancies
bash scripts/position-reconcile.sh check

# Fix position tracking issues
bash scripts/position-reconcile.sh fix
```

**System Health Monitoring**:
```bash
# Start continuous health monitoring
./scripts/health_monitor.sh

# Manual health check
./scripts/status.sh
```

## Key Files for AI Agent Context

**Core Data Models**: `/backend/app/models/models.py`  
**Signal Evaluation Logic**: `/backend/app/services/bot_evaluator.py`  
**Market Data Caching**: `/backend/app/services/market_data_cache.py`  
**Signal Implementations**: `/backend/app/services/signals/technical.py`  
**Main Bot API**: `/backend/app/api/bots.py`  
**Trading Safety**: `/backend/app/services/trading_safety.py`  
**Main Dashboard**: `/frontend/src/pages/DashboardRedesigned.tsx` (consolidated main dashboard)
**Frontend Components**: `/frontend/src/components/Dashboard/` (stable React components)  
**API Hooks**: `/frontend/src/hooks/` (TanStack Query patterns)  
**Trading Issue Troubleshooting**: `/docs/TRADING_ISSUES_TROUBLESHOOTING.md`  
**Dashboard Consolidation**: `/docs/DASHBOARD_CONSOLIDATION_SEPTEMBER_20_2025.md`
**Signal Lock Management**: `/scripts/fix_signal_locks.py`  
**Position Reconciliation**: `/scripts/position-reconcile.sh`  
**Health Monitoring**: `/scripts/health_monitor.sh`  
**Comprehensive Documentation**: `/docs/` with detailed status reports and guides

## Current System Context (September 20, 2025)

### Immediate System State
- **11 Active Bots**: BTC-USD, ETH-USD, SOL-USD, XRP-USD, DOGE-USD, AVNT-USD, AERO-USD, SUI-USD, AVAX-USD, TOSHI-USD, and one additional pair
- **Single Database**: `/trader.db` at project root (3,606+ trades)
- **Unified Dashboard**: Main dashboard at root route with stable charts and live data
- **Cache Performance**: 96%+ hit rates eliminating API rate limits
- **Real-time Updates**: 5-second polling across frontend components
- **Background Processing**: Celery workers handling order sync every 30 seconds

### Production-Ready Features
- **Dashboard Consolidation**: Single main dashboard with fixed oscillating charts
- **Live Data Integration**: Real portfolio values from Coinbase API ($1,266 accurate display)
- **Chart Stability**: Deterministic data generation eliminates visual noise
- **Signal Confirmation System**: Time-based validation prevents false signals
- **Balance Pre-Check Optimization**: ~60% reduction in unnecessary API calls
- **Multi-Tranche Position Management**: Enhanced `Trade.position_tranches` JSON tracking
- **Temperature-Based UI**: Real-time 🔥HOT/🌡️WARM/❄️COOL/🧊FROZEN indicators
- **Comprehensive Safety Systems**: Trading limits, cooldowns, emergency controls
- **Clean Data Architecture**: `RawTrade` model for authoritative P&L calculations
