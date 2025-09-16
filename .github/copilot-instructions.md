# GitHub Copilot Instructions for Auto-Trader System

## System Overview

This is a **production-ready autonomous cryptocurrency trading system** that achieved 37,000% returns. The architecture is **bot-centric** with one bot per trading pair, using weighted signal aggregation for decision-making.

### Core Architecture
- **Backend**: FastAPI + SQLAlchemy ORM + Celery/Redis for background tasks
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS with TanStack Query (5-second polling)
- **Database**: Single SQLite file (`trader.db`) with models in `/backend/app/models/models.py`
- **API Structure**: RESTful with `/api/v1/` prefix, feature-organized routes in `/backend/app/api/`
- **Real-time Architecture**: 5-second polling (proven more reliable than WebSocket for this use case)
- **Testing**: 185+ comprehensive tests with signal validation and live API integration

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

### Critical Data Models
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

# Trade & position management
curl -X POST "http://localhost:8000/api/v1/trades/update-statuses"  # Sync order statuses
curl "http://localhost:8000/api/v1/raw-trades/" | jq '.[] | select(.product_id == "BTC-USD")'
curl "http://localhost:8000/api/v1/trades/pending" | jq  # Check stuck orders

# Bot temperature & scoring
curl "http://localhost:8000/api/v1/bots/" | jq '.[] | {name, status, current_combined_score}'
```

## Critical Service Integration Points

### Coinbase API Integration
- **Service Layer**: `/backend/app/services/coinbase_service.py` - Core API interactions
- **Authentication**: JWT-based for Coinbase Advanced Trade API
- **Rate Limiting**: Current issue - REST API calls causing 429 errors
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
- **No WebSocket**: Uses 5-second TanStack Query polling (proven more reliable)
- **State Management**: Server state via TanStack Query, no global state
- **Activity Feed**: Sticky panel with live bot status updates
- **Error Handling**: Toast notifications with extended display for errors
- **Component Structure**: `/frontend/src/pages/` for routes, `/components/` for reusables
- **API Hooks**: Centralized in `/frontend/src/hooks/` using TanStack Query patterns

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

## Known Issues & Critical Context

### ⚠️ CRITICAL AI AGENT WARNINGS

**Documentation vs Reality**: This system evolved rapidly with multiple migrations. Key warnings:
- **WebSocket Claims vs Reality**: Documentation may claim WebSocket success, but implementation failed
- **API Endpoint Evolution**: Many endpoints deprecated, check `/scripts/` for working solutions  
- **Trade Model Migration**: System migrated from `trades` to `raw_trades` model - sync gaps exist
- **Rate Limiting**: Still an active issue due to failed WebSocket implementation
- **Always verify endpoints work** before suggesting them to users

### Current Major Issues

**Rate Limiting (429 Errors)**  
- **Cause**: Failed WebSocket implementation, still using REST API
- **Impact**: Bot evaluations throttled, reduced trading frequency
- **Status**: Unresolved, requires proper WebSocket implementation or request spacing

**Order Synchronization Gaps**  
- **Symptom**: Orders show "pending" in DB while "FILLED" on Coinbase
- **Detection**: Use `/api/v1/trades/update-statuses` for manual sync
- **Background Fix**: 30-second Celery task handles automatic updates

**Trade Data Migration Issue**
- **Symptom**: Bots show 0 trades despite actual Coinbase trading history
- **Cause**: Data exists in Coinbase but not in `raw_trades` table
- **Solution**: Check `/scripts/` and `/docs/legacy_scripts/` for working sync solutions

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
**Signal Implementations**: `/backend/app/services/signals/technical.py`  
**Main Bot API**: `/backend/app/api/bots.py`  
**Trading Safety**: `/backend/app/services/trading_safety.py`  
**Frontend Components**: `/frontend/src/components/` (React + TypeScript)  
**Trading Issue Troubleshooting**: `/docs/TRADING_ISSUES_TROUBLESHOOTING.md`  
**Signal Lock Management**: `/scripts/fix_signal_locks.py`  
**Position Reconciliation**: `/scripts/position-reconcile.sh`  
**Health Monitoring**: `/scripts/health_monitor.sh`  
**Comprehensive Documentation**: `/docs/` with detailed status reports and guides
