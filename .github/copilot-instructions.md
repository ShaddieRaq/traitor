# Copilot Instructions for Auto-Trader System

## Architecture Overview

This is a **bot-centric cryptocurrency trading system** with one bot per trading pair. The system uses FastAPI + React with SQLite, implementing a signal-based trading approach with weighted aggregation.

### Core Architecture
- **Backend**: FastAPI with SQLAlchemy ORM, Celery for background tasks, Redis for queuing
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS with TanStack Query (5-second polling)
- **Database**: SQLite with models in `/backend/app/models/models.py`
- **API Structure**: RESTful with `/api/v1/` prefix, organized by feature in `/backend/app/api/`

## Critical System Characteristics

### Bot-Centric Design Pattern
Each `Bot` entity represents one trading pair with:
- Weighted signal aggregation (RSI, Moving Average, MACD)
- Position sizing and risk management parameters
- Signal confirmation system requiring consistency over time
- Trade step percentages and cooldown periods

### Signal System Architecture
- **Base Signal Class**: `/backend/app/services/signals/base.py` - Abstract signal interface
- **Technical Signals**: `/backend/app/services/signals/technical.py` - RSI, MA, MACD implementations
- **Factory Pattern**: `create_signal_instance()` for dynamic signal creation
- **Scoring Range**: -1 (strong sell) to +1 (strong buy) with weighted aggregation

### Data Flow Pattern
1. **Market Data**: Coinbase Advanced Trade API → `MarketData` model
2. **Signal Evaluation**: `bot_evaluator.py` → weighted signal scores → `BotSignalHistory` 
3. **Trade Execution**: `trading_service.py` → Coinbase API → `Trade` model
4. **Frontend Updates**: 5-second polling via TanStack Query → real-time dashboard

## Development Workflows

### Running the System
```bash
# Backend (from /backend)
python -m app.main

# Frontend (from /frontend) 
npm run dev

# Redis (required for background tasks)
docker-compose up redis

# WebSocket monitoring (verify real-time feeds)
curl http://localhost:8000/api/v1/websocket-prices/price-streaming-status

# Quick automated setup/start (from root)
./scripts/setup.sh   # First time setup
./scripts/start.sh   # Start all services
./scripts/status.sh  # Check system health
```

### Critical Debugging Commands
```bash
# Check system errors
curl -s "http://localhost:8000/api/v1/system-errors/errors" | jq '.[0:5]'

# Monitor WebSocket health
curl "http://localhost:8000/api/v1/websocket-prices/price-streaming-status" | jq

# Sync pending orders manually
curl -X POST "http://localhost:8000/api/v1/trades/update-statuses"

# View recent bot evaluations
curl "http://localhost:8000/api/v1/bot-evaluation/recent-evaluations" | jq

# Check raw trades (new system)
curl -s "http://localhost:8000/api/v1/raw-trades/" | jq 'length'
curl -s "http://localhost:8000/api/v1/raw-trades/" | jq '.[] | select(.product_id == "SUI-USD")'

# Common Issue: Bot shows 0 trades but Coinbase has trades
# PROBLEM: System moved from trades to raw-trades model, sync missing
# SOLUTION: Use working sync scripts (check /scripts/ and /docs/legacy_scripts/)
```

### Testing Approach
- **Comprehensive Test Suite**: 185+ tests in `/backend/tests/`
- **Custom Test Runner**: `python test_runner.py [category]` for targeted testing
  - Categories: `rsi`, `ma`, `macd`, `aggregation`, `configurations`, `all`
- **Signal Validation**: Mathematical precision validation for technical indicators
- **Live API Integration**: WebSocket connection tests with real Coinbase data
- **Order Sync Testing**: Validates trade status synchronization pipeline

### Database Patterns
- **Single SQLite File**: `trader.db` for production simplicity
- **Model Relationships**: Bot → BotSignalHistory, Bot → Trade with proper foreign keys
- **Timestamp Tracking**: All models use `DateTime(timezone=True)` with `func.now()`

## Project-Specific Conventions

### API Route Organization
Routes are organized by feature with consistent patterns:
- `/api/v1/bots` - Bot CRUD operations
- `/api/v1/bot-evaluation` - Signal evaluation endpoints
- `/api/v1/trades` - Trade execution and history
- `/api/v1/market` - Market data and analysis

### Configuration Management
- **Bot Signal Config**: JSON string in `Bot.signal_config` with format:
  ```json
  {"RSI": {"weight": 0.4, "period": 14}, "MA_Crossover": {"weight": 0.3}}
  ```
- **Environment**: Settings in `/backend/app/core/config.py`

### Frontend State Management
- **No Global State**: TanStack Query handles all server state
- **5-Second Polling**: Consistent across all data-fetching hooks in `/frontend/src/hooks/`
- **Real-time Updates**: Sticky activity panel with live bot status
- **WebSocket Integration**: Trade execution toasts and live price updates

## Critical Integration Points

### Coinbase API Integration
- **Service Layer**: `/backend/app/services/coinbase_service.py`
- **Authentication**: JWT-based for Advanced Trade API
- **WebSocket Service**: `/backend/app/services/simple_websocket.py` - Real-time price feeds (WORKING)
- **Price Cache Service**: `/backend/app/services/websocket_price_cache.py` - Price caching layer
- **Price Flow**: WebSocket cache → `get_product_ticker()` → Bot evaluations (no more rate limiting)

### Signal Evaluation System
- **Entry Point**: `/backend/app/services/bot_evaluator.py`
- **Streaming Version**: `/backend/app/services/streaming_bot_evaluator.py` (real-time)
- **Confirmation Logic**: Signals must be consistent over `confirmation_minutes`
- **Factory Pattern**: Signal creation in `/backend/app/services/signals/base.py`

### Background Services Architecture
- **Celery Tasks**: `/backend/app/tasks/` - Order sync, trade monitoring
- **Redis Queue**: Background job processing with 30-second intervals
- **Position Reconciliation**: `/backend/app/services/position_reconciliation_service.py`
- **Order Monitoring**: `/backend/app/services/order_monitoring_service.py` for sync issues

### Safety and Risk Management
- **Trading Safety**: `/backend/app/services/trading_safety.py`
- **Position Limits**: `max_positions`, `position_size_usd` per bot
- **Circuit Breakers**: Stop-loss and take-profit percentages

## Known Issues & Context

### ⚠️ CRITICAL AI AGENT WARNINGS
**Documentation/Code Mismatches**: This codebase has evolved rapidly with multiple system migrations. Be aware:
- **API endpoints may be deprecated** but still referenced in code/docs
- **"Legacy" scripts may be the only working solution** for some operations
- **Trade system migration**: Moved from `trades` model to `raw_trades` model, sync may be incomplete
- **Always verify endpoints work** before suggesting them to users
- **Check both `/scripts/` and `/docs/legacy_scripts/` for working solutions**

### WebSocket Implementation Status
**COMPLETED**: WebSocket price feeds FULLY OPERATIONAL as of September 15, 2025. Rate limiting issues (429 errors) completely eliminated.
- **Production Implementation**: `/backend/app/services/simple_websocket.py` - Stable, real-time WebSocket service
- **Real-time Bot Evaluations**: Sub-50ms bot decision latency via streaming ticker data
- **Price Architecture**: WebSocket cache → `get_product_ticker()` → Bot evaluations (zero rate limiting)
- **Connection Monitoring**: Check via `/api/v1/websocket-prices/price-streaming-status`
- **Streaming Bot Evaluator**: `/backend/app/services/streaming_bot_evaluator.py` - Real-time market reactions

### Order Synchronization Issue  
**IDENTIFIED**: Order status sync between Coinbase and database requires monitoring. Orders may show "pending" in database while "FILLED" on Coinbase.
- **Detection**: Use `/api/v1/trades/update-statuses` endpoint for manual sync
- **Background Service**: Celery task runs every 30 seconds for automatic updates
- **Impact**: Can temporarily block bots from new trades despite available funds

### Trade Data Migration Issue
**CRITICAL**: System migrated from `trades` to `raw_trades` model. Bots may show 0 trades even when Coinbase has trades.
- **Symptom**: Bot dashboard shows 0 trades but user has trades on Coinbase
- **Root Cause**: Trades exist on Coinbase but not in `raw_trades` table
- **Check**: `curl -s "http://localhost:8000/api/v1/raw-trades/" | jq '.[] | select(.product_id == "SUI-USD")'`
- **Solution**: Look for working sync scripts in `/scripts/` or `/docs/legacy_scripts/`
- **Warning**: Many sync endpoints are deprecated - verify before recommending

### Position Management
Enhanced position tracking with tranches in `Trade.position_tranches` (JSON field) for multi-entry position building.

### Temperature System
Bot "temperature" indicators (🔥🌡️❄️🧊) based on recent trading activity and market responsiveness.

## Key Files for Context
- `/backend/app/models/models.py` - Core data models
- `/backend/app/services/bot_evaluator.py` - Signal aggregation logic  
- `/backend/app/api/bots.py` - Main bot management API
- `/frontend/src/components/` - React component library
- `/docs/` - Extensive documentation including recent status reports
