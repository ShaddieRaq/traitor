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
```

### Testing Approach
- **Comprehensive Test Suite**: 185+ tests in `/backend/tests/`
- **Test Runner**: `python test_runner.py [category]` for targeted testing
- **Signal Validation**: Mathematical precision validation for technical indicators
- **API Integration**: Live Coinbase API validation tests

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
- **5-Second Polling**: Consistent across all data-fetching hooks
- **Real-time Updates**: Sticky activity panel with live bot status

## Critical Integration Points

### Coinbase API Integration
- **Service Layer**: `/backend/app/services/coinbase_service.py`
- **Authentication**: JWT-based for Advanced Trade API
- **WebSocket Service**: `/backend/app/services/simple_websocket.py` - Real-time price feeds (WORKING)
- **Price Flow**: WebSocket cache → `get_product_ticker()` → Bot evaluations (no more rate limiting)

### Signal Evaluation System
- **Entry Point**: `/backend/app/services/bot_evaluator.py`
- **Streaming Version**: `/backend/app/services/streaming_bot_evaluator.py` (real-time)
- **Confirmation Logic**: Signals must be consistent over `confirmation_minutes`

### Safety and Risk Management
- **Trading Safety**: `/backend/app/services/trading_safety.py`
- **Position Limits**: `max_positions`, `position_size_usd` per bot
- **Circuit Breakers**: Stop-loss and take-profit percentages

## Known Issues & Context

### WebSocket Implementation Status
**FIXED**: WebSocket price feeds now WORKING as of September 15, 2025. Rate limiting issues (429 errors) eliminated.
- **New Implementation**: `/backend/app/services/simple_websocket.py` - Functional WebSocket service
- **Price Source**: Bots now use WebSocket cached prices instead of REST API calls
- **Connection Status**: Check via `/api/v1/websocket-prices/price-streaming-status`

### Trade Sync Issue
**CURRENT ISSUE**: Trades execute successfully on Coinbase but may not immediately appear in UI. This is a database sync issue, not a trading problem.

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
