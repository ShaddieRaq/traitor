# Signal-Based Coinbase Trading Bot Development Guide

## 🚀 QUICK START FOR AI AGENTS

### Essential Commands (Use These First):
```bash
./scripts/status.sh   # Check current service status
./scripts/start.sh    # Start all services (if not running)
./scripts/logs.sh     # View logs if issues occur
./scripts/test.sh     # Run tests to verify functionality
```

### Essential Code Discovery:
```bash
# Before referencing ANY code, run these:
python scripts/generate_class_diagram.py  # Get current class structure
cat docs/current_class_diagram.md         # View all classes and methods
grep -r "class.*Signal" backend/app/services/signals/  # Find signal classes
grep -r "@router\." backend/app/api/       # Find API routes
```

### Current System State (2025-09-02):
- ✅ All services running and healthy
- ✅ Coinbase API integration functional  
- ✅ 2 default signals: RSI and Moving Average
- ✅ API endpoints: http://localhost:8000/api/docs
- ✅ Frontend dashboard: http://localhost:3000
- ✅ **USD Fiat Account Access**: Portfolio breakdown method implemented for complete account access

## 🔄 CRITICAL UPDATE: USD Fiat Account Access (2025-09-02)

### ⚠️ COINBASE API LIMITATION DISCOVERED
**The Coinbase Advanced Trade API `get_accounts()` method ONLY returns crypto accounts, NOT fiat (USD) accounts.**

### Portfolio Breakdown Method - REQUIRED for USD Access
To access USD fiat balances, you MUST use the portfolio breakdown pattern:

```python
# ❌ WRONG: Only returns crypto accounts (BTC, ETH, etc.)
accounts = client.get_accounts()

# ✅ CORRECT: Returns both crypto AND fiat accounts
portfolios = client.get_portfolios()
breakdown = client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])
# Access fiat accounts via breakdown['spot_positions'] where is_cash=True
```

### Updated CoinbaseService Implementation
**File**: `backend/app/services/coinbase_service.py`
- ✅ **Method**: `get_accounts()` completely rewritten to use portfolio breakdown
- ✅ **Returns**: Both crypto and fiat accounts in unified format
- ✅ **Fallback**: Original method maintained for resilience
- ✅ **Verified**: $465.29 USD balance now accessible in Live Portfolio Overview

### Key Implementation Pattern
```python
class CoinbaseService:
    def get_accounts(self) -> List[dict]:
        """Get all accounts including fiat using portfolio breakdown method"""
        try:
            # Portfolio breakdown method for complete account access
            portfolios = self.client.get_portfolios()
            breakdown = self.client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])
            
            # Process both crypto and fiat accounts from spot_positions
            accounts = []
            for position in breakdown.get('spot_positions', []):
                # Fiat accounts identified by is_cash=True
                # Crypto accounts have is_cash=False
                accounts.append({
                    'currency': position.get('asset', ''),
                    'available_balance': float(position.get('total_balance_fiat', 0)),
                    'hold': float(position.get('total_balance_fiat', 0)) - float(position.get('available_balance_fiat', 0)),
                    'is_cash': position.get('is_cash', False)
                })
            return accounts
        except Exception as e:
            # Fallback to original method for resilience
            return self._get_accounts_fallback()
```

### Frontend Impact
- ✅ **Portfolio Overview**: Now displays real USD fiat balances
- ✅ **Manual Workarounds**: All removed and cleaned up
- ✅ **Live Updates**: Real-time portfolio calculations include USD

### Testing Verification
- ✅ **Integration Tests**: Updated to validate both crypto and fiat account access
- ✅ **Live API Testing**: All tests run against real portfolio breakdown endpoints
- ✅ **Performance**: Optimized to avoid slow SDK introspection (70+ second delays)

## ⚠️ CRITICAL CODE VERIFICATION RULES

### NEVER Reference Non-Existent Code
**ALWAYS verify classes, functions, and modules exist before referencing them:**

1. **Check imports and class names** with `grep_search` or `read_file` before using them
2. **Verify API endpoints** exist by checking route definitions in `app/api/` 
3. **Confirm database models** by reading `app/models/models.py`
4. **Validate service methods** by checking the actual service files

### Code Discovery Process
**Before writing any code that references existing classes/functions:**

1. **Search first**: Use `semantic_search` or `grep_search` to find existing implementations
2. **Read the actual files**: Use `read_file` to see exact class/function names and signatures  
3. **Verify imports**: Check what's actually imported in existing files
4. **Test assumptions**: If unsure about something, run a quick test to verify it works

### Common Verification Commands
```bash
# Find signal classes
grep -r "class.*Signal" backend/app/services/signals/

# Check API routes  
grep -r "@router\." backend/app/api/

# Find database models
grep -r "class.*(" backend/app/models/

# Verify imports
grep -r "from.*import" backend/app/
```

### Examples of What NOT To Do
❌ **Don't assume class names**: `MovingAverageCrossoverSignal` vs actual `MovingAverageSignal`  
❌ **Don't assume method names**: `get_ticker()` vs actual `get_product_ticker()`  
❌ **Don't assume file locations**: `signals/technical_indicators.py` vs actual `signals/technical.py`  
❌ **Don't assume API routes**: `/api/signals/` vs actual `/api/v1/signals/`

### When Adding New Code
1. **Check if it already exists** before creating duplicates
2. **Use exact naming conventions** from existing codebase
3. **Follow existing patterns** for imports, class structure, etc.
4. **Verify your additions work** by testing them
5. **Update this documentation** with new class names and import patterns

## Architecture Overview
This is a signal-based trading bot with a web dashboard that uses Python backend (FastAPI) and React frontend. The system follows a modular architecture with separate components for signal management, market data processing, trading execution, and portfolio tracking. The bot operates on spot trading using configurable signals that can be enabled/disabled individually.

### Management Scripts - ALWAYS USE THESE
⚠️ **CRITICAL**: Use these scripts instead of manual commands to avoid deployment issues:

- `./scripts/setup.sh` - One-time environment setup with prerequisite checking
- `./scripts/start.sh` - Start all services with health verification (RECOMMENDED)
- `./scripts/stop.sh` - Stop all services gracefully with cleanup  
- `./scripts/restart.sh` - Stop and start all services with delay
- `./scripts/status.sh` - Check service status, health, and resource usage
- `./scripts/logs.sh` - View logs with filtering and real-time following
- `./scripts/test.sh` - Run test suite with multiple options

### Successful Launch Sequence (Tested 2025-09-02):
**Use automated scripts** - they handle all the complexity:
```bash
./scripts/start.sh  # Starts all services: Redis, Backend, Frontend, Celery Worker, Celery Beat
./scripts/status.sh # Verify everything is running
```

**📊 VISUAL DOCUMENTATION**: Comprehensive visual architecture diagrams are available in `/docs/` directory:
- `VISUAL_ARCHITECTURE.md` - Complete system diagrams from multiple perspectives and depths
- `DEVELOPMENT_WORKFLOWS.md` - Development processes, testing, deployment, and monitoring flows  
- `QUICK_REFERENCE.md` - Day-to-day development reference with commands and templates

## Project Structure
- **Backend**: FastAPI + SQLAlchemy + Celery for background tasks
- **Frontend**: React + TypeScript + TailwindCSS for dashboard
- **Database**: SQLite (local development, single user)
- **Real-time**: Socket.IO for live updates
- **Trading**: Coinbase Advanced Trade API integration

## Coinbase API Key Information
- **API Type**: Coinbase Developer Platform (CDP) API Keys
- **Authentication**: JWT-based authentication with EC private keys
- **Rate Limits**: Private endpoints more generous than public; implement rate limit headers tracking
- **Base URL**: Uses Advanced Trade API endpoints under `/api/v3/brokerage/`
- **Environment Setup**: API credentials stored in `.env` file in project root
- **Integration Status**: ✅ Live connection verified and functional

## Critical API Patterns

### Authentication Setup
```python
from coinbase.rest import RESTClient
# Environment variables preferred for security
client = RESTClient()  # Uses COINBASE_API_KEY and COINBASE_API_SECRET
# Or pass directly (testing only)
client = RESTClient(api_key="organizations/{org_id}/apiKeys/{key_id}", 
                   api_secret="-----BEGIN EC PRIVATE KEY-----\n...")
```

### Core Trading Operations
- `client.market_order_buy()` / `client.market_order_sell()` - Market orders
- `client.limit_order_gtc()` - Good-till-cancelled limit orders  
- **`client.get_accounts()`** - ⚠️ **CRYPTO ONLY** - Does NOT return fiat (USD) accounts
- **`client.get_portfolios()` + `client.get_portfolio_breakdown()`** - ✅ **REQUIRED** for complete account access including USD fiat
- `client.list_orders()` - Order history and status
- `client.get_product(product_id)` - Product details and current price

### Account Access Pattern (CRITICAL)
```python
# ❌ INCOMPLETE: Only crypto accounts
accounts = client.get_accounts()

# ✅ COMPLETE: Both crypto and fiat accounts
portfolios = client.get_portfolios()
breakdown = client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])
# USD accounts found in breakdown['spot_positions'] where is_cash=True
```

### Real-time Data Streaming
```python
from coinbase.websocket import WSClient
client = WSClient(api_key=key, api_secret=secret, on_message=handler)
client.subscribe(product_ids=["BTC-USD"], channels=["ticker", "level2"])
```

## Development Workflows

### Local Development Setup
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm run dev

# Start background services
docker-compose up redis  # For Celery task queue
```

### Verified Working Deployment
The project has been successfully deployed and tested with all services running:

**Service Status** (as of 2025-09-02):
- ✅ Redis: Running in Docker container
- ✅ FastAPI Backend: http://localhost:8000 
- ✅ React Frontend: http://localhost:3000
- ✅ Celery Worker: Background task processing active
- ✅ Celery Beat: Periodic task scheduling active
- ✅ Database: SQLite auto-created with default signals
- ✅ Coinbase Integration: Live API connection verified and functional

**API Endpoints**:
- API Documentation: http://localhost:8000/api/docs
- ReDoc Documentation: http://localhost:8000/api/redoc  
- Root API: http://localhost:8000/
- Health Check: http://localhost:8000/health
- Signals API: http://localhost:8000/api/v1/signals
- Market Data API: http://localhost:8000/api/v1/market
- Trades API: http://localhost:8000/api/v1/trades

**Coinbase API Endpoints** (verified working):
- Products: http://localhost:8000/api/v1/market/products
- Accounts: http://localhost:8000/api/v1/market/accounts
- Ticker: http://localhost:8000/api/v1/market/ticker/{product_id}

### Key Development Commands
- `cd backend && uvicorn app.main:app --reload` - Start FastAPI dev server
- `cd frontend && npm run dev` - Start React dev server  
- `cd backend && celery -A app.tasks.celery_app worker --loglevel=info` - Start background worker
- `cd backend && celery -A app.tasks.celery_app beat --loglevel=info` - Start task scheduler
- `cd backend && pytest` - Run backend tests
- `cd frontend && npm test` - Run frontend tests

## EXACT API ROUTES REFERENCE

⚠️ **CRITICAL**: These are the ONLY routes that exist. Never attempt to call routes not listed here.

### Core Application Routes
- `GET /` - Root endpoint (returns API info)
- `GET /health` - Health check endpoint
- `GET /api/docs` - Swagger UI documentation  
- `GET /api/redoc` - ReDoc documentation

### Signals API (`/api/v1/signals`)
- `GET /api/v1/signals/` - Get all signals
- `POST /api/v1/signals/` - Create new signal
- `GET /api/v1/signals/{signal_id}` - Get specific signal
- `PUT /api/v1/signals/{signal_id}` - Update signal
- `DELETE /api/v1/signals/{signal_id}` - Delete signal
- `GET /api/v1/signals/results/` - Get signal calculation results
- `POST /api/v1/signals/{signal_id}/evaluate` - Manually evaluate signal

### Market Data API (`/api/v1/market`)
- `GET /api/v1/market/products` - Get available trading products
- `GET /api/v1/market/ticker/{product_id}` - Get current ticker for product
- `GET /api/v1/market/candles/{product_id}` - Get historical candlestick data (params: timeframe, limit)
- `GET /api/v1/market/accounts` - Get account balances
- `POST /api/v1/market/fetch-data/{product_id}` - Manually trigger data fetch (params: timeframe)

### Trades API (`/api/v1/trades`)
- `GET /api/v1/trades/` - Get trade history (params: product_id, limit)
- `GET /api/v1/trades/stats` - Get trading statistics
- `POST /api/v1/trades/trigger-evaluation` - Manually trigger signal evaluation

### Route Usage Notes
- Routes ending with `/` require the trailing slash
- Product ID format: "BTC-USD", "ETH-USD", etc.
- All POST/PUT requests require proper Content-Type: application/json
- Query parameters are optional unless specified

## EXACT CLASS AND MODULE REFERENCE

⚠️ **CRITICAL**: Always use current class information. Run `python scripts/generate_class_diagram.py` to get the most up-to-date class structure.

### Quick Class Discovery
**📋 Current classes are documented in auto-generated UML**: `docs/current_class_diagram.md`

**🔄 To update class documentation**: `python scripts/generate_class_diagram.py`

### Discovery-First Approach
**ALWAYS use one of these methods before referencing any code:**

#### Method 1: Auto-Generated Class Diagram (Recommended)
```bash
# Generate current class diagram from live codebase
python scripts/generate_class_diagram.py

# View the generated documentation
cat docs/current_class_diagram.md
```

#### Method 2: Manual Discovery Commands
```bash
# Find ALL signal classes (may be more than listed below)
grep -r "class.*Signal" backend/app/services/signals/

# Find ALL service classes
grep -r "class.*Service" backend/app/services/

# Find ALL database models  
grep -r "class.*(" backend/app/models/models.py

# Find ALL API routes
grep -r "@router\." backend/app/api/
```

### Known Classes (As of 2025-09-02)
**⚠️ This list may be incomplete - use discovery commands above for current state**

### Signal Classes (app/services/signals/)
```python
# File: app/services/signals/base.py
class BaseSignal(ABC)  # Abstract base class
def create_signal_instance(signal_type: str, parameters: Dict[str, Any]) -> Optional['BaseSignal']

# File: app/services/signals/technical.py  
class RSISignal(BaseSignal)  # NOT "RSI_Signal" or "RSIIndicator"
class MovingAverageSignal(BaseSignal)  # NOT "MovingAverageCrossoverSignal" or "MASignal"
```

### Service Classes (app/services/)
```python
# File: app/services/coinbase_service.py
class CoinbaseService:
    def get_products(self) -> List[dict]
    def get_product_ticker(self, product_id: str) -> Optional[dict]  # NOT "get_ticker"
    def get_accounts(self) -> List[dict]  # ✅ UPDATED: Uses portfolio breakdown for fiat access
    def get_historical_data(self, product_id: str, granularity: int = 3600, limit: int = 100) -> pd.DataFrame
    def _get_accounts_fallback(self) -> List[dict]  # Fallback method for resilience

# Global instance
coinbase_service = CoinbaseService()
```

### Database Models (app/models/models.py)
```python
# File: app/models/models.py
class Signal(Base)
class MarketData(Base)  
class Trade(Base)
class SignalResult(Base)
```

### API Router Files (app/api/)
```python
# File: app/api/signals.py
router = APIRouter()

# File: app/api/market.py  
router = APIRouter()

# File: app/api/trades.py
router = APIRouter()
```

### Configuration (app/core/)
```python
# File: app/core/config.py
class Settings(BaseSettings)
settings = Settings()

# File: app/core/database.py
def get_db()
```

### Common Import Patterns
```python
# Signals
from app.services.signals.technical import RSISignal, MovingAverageSignal
from app.services.signals.base import BaseSignal, create_signal_instance

# Services  
from app.services.coinbase_service import coinbase_service, CoinbaseService

# Models
from app.models.models import Signal, MarketData, Trade, SignalResult

# Config
from app.core.config import settings
from app.core.database import get_db
```

### Route Usage Notes
- All POST/PUT requests require proper Content-Type: application/json
- Query parameters are optional unless specified

### Database Management
- Database auto-creates on first run with default signals (RSI, MA Crossover)
- SQLAlchemy models in `backend/app/models/models.py`
- Migrations handled by Alembic (future enhancement)
- Default signals created in `app/main.py` startup event

### Testing Strategy
- Live API testing with real Coinbase endpoints (no mocking for integration tests)
- Integration tests for signal processing logic
- Component testing for React dashboard
- End-to-end testing for critical trading flows
- **Performance Critical**: Avoid `'property' in coinbase_object` - causes 70+ second delays
- **Use instead**: `hasattr(object, 'property')` for fast attribute checking

### Technical Implementation Notes
- RSI calculation uses pure pandas/numpy (no TA-Lib dependency)
- Modern React setup without explicit React imports for JSX
- Pydantic-settings for environment configuration
- Celery Beat for scheduled signal evaluation tasks

## Project-Specific Conventions

### Signal Management
- Each signal is a separate class inheriting from `BaseSignal`
- Signals stored in `backend/app/services/signals/` directory
- Signal configuration stored in database with enable/disable flags
- Real-time signal evaluation through Celery background tasks
- Default signals: RSI (14-period, 30/70 levels) and MA Crossover (10/20 periods)
- Signal factory pattern in `create_signal_instance()` function
- Pure pandas/numpy implementation for technical indicators (no TA-Lib dependency)

### API Structure
- FastAPI routes organized by functionality: `/api/v1/signals/`, `/api/v1/trades/`, `/api/v1/market/`
- Pydantic models for request/response validation
- SQLAlchemy models for database entities
- Service layer pattern for business logic separation

### Frontend Patterns
- React components in `frontend/src/components/`
- Custom hooks for API calls and WebSocket connections
- TypeScript interfaces matching backend Pydantic models
- TailwindCSS for consistent styling

### Error Handling
- Exponential backoff for Coinbase API rate limits
- WebSocket auto-reconnection with retry logic
- Structured logging with JSON format for all trading decisions
- Graceful degradation when external services unavailable

### Data Management
- Historical market data stored in SQLite database
- Candlestick data cached for multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Signal calculation results cached to avoid recomputation
- Trade execution history with detailed order tracking

### Configuration Management
- Environment variables in `.env` file (never committed)
- Signal parameters configurable through database
- Risk management limits stored in configuration table
- Feature flags for enabling/disabling signals individually

## Integration Points

### External Dependencies
- **Database**: SQLAlchemy for ORM, supports multiple backends
- **Scheduling**: Celery Beat for periodic tasks
- **Queue**: Redis for Celery task queue
- **HTTP Client**: Axios for frontend API calls
- **State Management**: TanStack Query for React data fetching
- **Styling**: TailwindCSS utility classes
- **Icons**: Lucide React icons
- **Notifications**: React Hot Toast for user feedback

### WebSocket Channels
- `ticker` - Real-time price updates
- `level2` - Order book data
- `user` - Order updates and fills (authenticated)
- `heartbeats` - Connection health monitoring

## Command Execution Guidelines

⚠️ **CRITICAL**: Use management scripts to avoid deployment failures and service disruption.

### Primary Rule: Use Management Scripts First
**ALWAYS prefer these scripts over manual commands:**
```bash
./scripts/start.sh    # Start all services automatically
./scripts/stop.sh     # Stop all services cleanly  
./scripts/restart.sh  # Restart all services safely
./scripts/status.sh   # Check service health
./scripts/logs.sh     # View application logs
./scripts/test.sh     # Run tests
```

### Manual Commands (Only When Scripts Don't Work)
**If you must use manual commands, follow these strict patterns:**

### Directory Navigation Rules
- **ALWAYS** use `cd` to change to the correct directory BEFORE running commands
- **NEVER** assume the current working directory
- **ALWAYS** use absolute paths: `/Users/lazy_genius/Projects/trader/backend`
- **VERIFY** directory before running commands with `pwd` if uncertain

### Service Management Commands
```bash
# Backend Service (FastAPI)
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend Service (React)
cd /Users/lazy_genius/Projects/trader/frontend
npm run dev

# Celery Worker
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat Scheduler
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info

# Redis (Docker)
cd /Users/lazy_genius/Projects/trader
docker-compose up redis -d
```

### Virtual Environment Activation
- **ALWAYS** activate venv before Python commands: `source venv/bin/activate`
- **VERIFY** activation worked with `which python` (should show venv path)
- **NEVER** run Python commands without activating venv first

### Service Health Checking
```bash
# Check if services are running
lsof -i :8000  # FastAPI backend
lsof -i :3000  # React frontend
lsof -i :6379  # Redis

# Test API connectivity
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/signals/
```

### Process Management
```bash
# Kill services cleanly
pkill -f "uvicorn app.main:app"    # Kill FastAPI
pkill -f "celery"                  # Kill all Celery processes
docker-compose down                # Stop Redis

# Check running processes
ps aux | grep uvicorn
ps aux | grep celery
docker ps
```

### Command Validation Patterns
- **BEFORE** running any command, verify the working directory
- **BEFORE** Python commands, ensure virtual environment is activated
- **BEFORE** API calls, ensure the service is actually running
- **AFTER** starting services, wait 2-3 seconds before testing connectivity

### Common Error Prevention
- **Exit Code 127**: Usually means command not found or wrong directory
- **Connection Refused**: Service not running or wrong port
- **Module Not Found**: Virtual environment not activated
- **Permission Denied**: Check file permissions or process conflicts

### Terminal Session Management
- Use separate terminals for each long-running service (FastAPI, Celery Worker, Celery Beat)
- Keep one terminal free for ad-hoc commands and testing
- Use `screen` or `tmux` for persistent sessions if needed

## Security Considerations
- Never log API secrets or private keys
- Use environment variables for all credentials
- Implement proper JWT token rotation
- Monitor for unusual API activity
- Set position limits and stop-loss mechanisms

## Performance Optimization
- Use connection pooling for REST requests
- Batch API calls where possible
- Implement local caching for static data
- Monitor memory usage for long-running processes
- Use async operations for WebSocket handling

## File Structure Patterns

### Backend Key Files
- `app/main.py` - FastAPI application entry point with startup initialization
- `app/core/config.py` - Pydantic settings with environment variable loading
- `app/core/database.py` - SQLAlchemy setup and session management
- `app/models/models.py` - Database models (Signal, MarketData, Trade, SignalResult)
- `app/services/coinbase_service.py` - Coinbase API client wrapper
- `app/services/signals/base.py` - Abstract base class for all signals
- `app/services/signals/technical.py` - RSI and MA signal implementations
- `app/tasks/trading_tasks.py` - Celery tasks for signal evaluation
- `app/tasks/data_tasks.py` - Celery tasks for market data fetching

### Frontend Key Files
- `src/App.tsx` - Main application with routing and providers
- `src/lib/api.ts` - Axios client configuration with interceptors
- `src/hooks/useSignals.ts` - React Query hooks for signals API
- `src/hooks/useMarket.ts` - React Query hooks for market data API
- `src/types/index.ts` - TypeScript interfaces matching backend schemas
- `src/pages/Dashboard.tsx` - Main dashboard with status overview
- `src/pages/Signals.tsx` - Signal management with toggle controls

### Documentation Files
- `docs/VISUAL_ARCHITECTURE.md` - Comprehensive system architecture diagrams covering:
  - System overview and technical architecture
  - Business logic flow and signal processing pipelines
  - User experience journey and component hierarchies
  - Bot functionality deep dive with trading execution flows
  - App responsiveness architecture with real-time data patterns
  - Development roadmap and feature priority matrix
- `docs/DEVELOPMENT_WORKFLOWS.md` - Development process diagrams including:
  - Local environment setup flows
  - Testing strategy and CI/CD pipelines
  - Monitoring, observability, and error handling
  - Deployment architecture and security measures
- `docs/QUICK_REFERENCE.md` - Day-to-day development reference with:
  - Project structure overview with visual file tree
  - Quick command reference for all services
  - Signal development templates and API examples
  - Troubleshooting guide and performance monitoring
- `docs/current_class_diagram.md` - Auto-generated UML class diagram (always current)
  - Generated by: `python scripts/generate_class_diagram.py`
  - Shows all classes, methods, inheritance relationships
  - Includes file locations for each class
  - Updates automatically to reflect code changes

### Project Scripts
- `scripts/generate_class_diagram.py` - Auto-generates UML class diagram from codebase

## Development Setup Notes

### Dependencies and Installation
- **TA-Lib**: Commented out in requirements.txt due to system library dependencies
- Use pure pandas/numpy for technical analysis instead
- Frontend: All React imports removed (modern JSX transform)
- Backend: Virtual environment recommended for isolated dependencies

### Common Issues and Solutions
- **React TypeScript**: Remove `import React` statements for modern React
- **TA-Lib Installation**: Requires system-level TA-Lib library, use pandas alternative
- **Directory Navigation**: Always use absolute paths in terminal commands
- **Signal Implementation**: Use pandas rolling calculations for technical indicators
- **SQLAlchemy Metadata**: Avoid `metadata` column name (reserved word), use `signal_metadata`
- **Pydantic Settings**: Use `pydantic-settings` package for BaseSettings (Pydantic v2)
- **API Documentation**: Available at `/api/docs` not `/docs` (configured with api_v1_prefix)
- **USD Account Missing**: Use portfolio breakdown method, NOT `get_accounts()` - see Portfolio Breakdown section above
- **Slow Coinbase Tests**: Avoid `'property' in coinbase_object` - use `hasattr()` instead (70+ second difference)
- **Exit Code 127**: Command not found - check directory and virtual environment activation
- **Connection Refused on API calls**: Backend service not running - start uvicorn first
- **Module Import Errors**: Virtual environment not activated - run `source venv/bin/activate`
- **Wrong Working Directory**: Use `cd` to navigate before running commands
- **Service Conflicts**: Check for existing processes with `lsof -i :PORT` before starting services

### Deployment Troubleshooting Checklist
1. **Verify Working Directory**: Run `pwd` to confirm location
2. **Check Virtual Environment**: Run `which python` (should show venv path)
3. **Verify Dependencies**: Run `pip list` to confirm packages installed
4. **Check Service Status**: Use `lsof -i :PORT` to verify service availability
5. **Test Connectivity**: Use `curl` commands to verify API endpoints respond
6. **Review Logs**: Check terminal output for specific error messages
7. **Environment Variables**: Verify `.env` file exists in project root with required credentials

## Deployment Verification Notes

### Current Working Status (Verified 2025-09-02):
✅ **All Services Operational**:
- Redis: Running in Docker container
- FastAPI Backend: http://localhost:8000 (health check passing)
- React Frontend: http://localhost:3000 (accessible)
- Celery Worker: Background task processing active
- Celery Beat: Periodic task scheduling active
- Database: SQLite with default signals loaded
- Coinbase Integration: Live API connection functional

### Launch Verification Steps:
1. **Start Services**: Run `./scripts/start.sh` (handles everything)
2. **Verify Status**: Run `./scripts/status.sh` (shows detailed health)
3. **Check Access**: Open http://localhost:3000 for dashboard
4. **Test API**: Visit http://localhost:8000/api/docs for API documentation

### Troubleshooting Common Issues:
- **PID file conflicts**: Run `./scripts/stop.sh` then `./scripts/start.sh`
- **Port conflicts**: Check `lsof -i :PORT` and kill conflicting processes
- **Environment issues**: Verify `.env` file exists in project root

## Testing Strategy and Philosophy

### Core Testing Principle
**Tests should only fail when there's an actual break in delivered application features.** This requires creating smart tests that validate real functionality, not just code execution.

### Current Test Coverage (As of 2025-09-02)
Our tests cover the features we're **actually delivering now**:

#### ✅ **Delivered Features Being Tested:**
1. **Signal Processing Engine** (`tests/test_signals.py`)
   - RSI calculation accuracy with known data patterns
   - Moving Average crossover logic validation
   - Signal score ranges (-1 to 1) and action types (buy/sell/hold)
   - Signal factory pattern for creating signal instances

2. **Coinbase API Integration** (`tests/test_coinbase.py`)
   - Live authentication with real API credentials
   - Product data retrieval (775+ trading pairs)
   - Account balance fetching
   - Ticker price data for specific products (BTC-USD)

3. **API Endpoints** (`tests/test_api.py`)
   - FastAPI route functionality
   - Database integration for signals CRUD
   - Market data endpoints with live Coinbase data
   - Proper HTTP status codes and response structures

#### ❌ **Undelivered Features NOT Tested:**
- Actual trade execution (not implemented yet)
- Risk management systems (not implemented yet)
- Real-time WebSocket data feeds (not implemented yet)
- Signal-triggered trading decisions (not implemented yet)
- Portfolio position tracking (not implemented yet)

### Testing Approach: Live API Testing
**No Mocking Strategy**: All tests run against live services to ensure real-world functionality:
- **Coinbase Tests**: Use actual Coinbase Advanced Trade API with real credentials
- **Database Tests**: Use real SQLite database with actual data
- **API Tests**: Use FastAPI TestClient against full application stack

### Test Performance Optimizations
**Lesson Learned**: Avoid slow SDK object introspection
- **Problem**: `'product_id' in coinbase_product_object` triggered slow `__getitem__` operation (70+ seconds)
- **Solution**: Use `hasattr(product, 'product_id')` for fast attribute checking
- **Result**: Full Coinbase test suite runs in <2 seconds

### Test Organization
```
backend/tests/
├── conftest.py          # Test configuration and fixtures
├── test_signals.py      # Signal calculation and factory tests
├── test_api.py          # FastAPI endpoint integration tests
├── test_coinbase.py     # Live Coinbase API integration tests
└── __init__.py
```

### Test Execution Commands
- `./scripts/test.sh --unit` - Run signal processing tests only
- `./scripts/test.sh --integration` - Run API and Coinbase tests
- `./scripts/test.sh --coinbase` - Run Coinbase connection tests only
- `./scripts/test.sh` - Run all tests (default)

### When to Add New Tests
**Feature-Driven Testing**: Create tests when implementing new features, not before:
1. **Implement the feature** in the codebase
2. **Verify it works** manually 
3. **Write tests** that would fail if that feature breaks
4. **Run tests** to ensure they pass with working feature

### Test Quality Guidelines
#### ✅ **Good Tests** (Indicate Real Application Breaks):
- Signal calculation accuracy with known input/output patterns
- API authentication and data retrieval from external services
- Database operations with actual data persistence
- End-to-end workflows that users actually perform

#### ❌ **Poor Tests** (Don't Indicate Real Problems):
- Object instantiation checks (`assert service is not None`)
- Type checking without business logic validation
- Testing external API response structures (Coinbase's responsibility)
- Mocked responses that don't reflect real API behavior

### Test Failure Investigation Process
When a test fails:
1. **Check if it's a real application break** - Can users still use the feature?
2. **Verify external dependencies** - Is Coinbase API down?
3. **Check recent code changes** - Did we break business logic?
4. **Update test if needed** - Has the feature legitimately changed?

This approach ensures our test suite serves as a reliable indicator of application health for the features we're actually delivering to users.

## Visual Documentation Usage

### For New AI Agents
- Start with `docs/VISUAL_ARCHITECTURE.md` for complete system understanding
- Reference `docs/QUICK_REFERENCE.md` for immediate development tasks
- Use `docs/DEVELOPMENT_WORKFLOWS.md` for process understanding

### For Development Leadership
- Use visual diagrams for strategic planning and architecture decisions
- Reference signal processing pipelines for bot functionality improvements
- Monitor real-time data flow patterns for responsiveness optimization
- Follow development roadmap and priority matrix for feature planning

### Diagram Technology
- All diagrams use Mermaid syntax for universal compatibility
- Renders in GitHub, VS Code, and most markdown viewers
- Update diagrams as system evolves to maintain accuracy
- Multiple perspective levels: overview → detailed → implementation
