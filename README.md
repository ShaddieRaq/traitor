# Bot-Centric Coinbase Trading System

A modern, bot-centric cryptocurrency trading system with advanced signal evaluation and real-time market data integration, built with Python (FastAPI) backend and React frontend.

## Features

- 🤖 **Bot-Centric Trading**: One bot per trading pair with intelligent signal aggregation
- 📊 **Web Dashboard**: Modern React interface for bot monitoring and management  
- 🔄 **Real-Time Bot Evaluation**: WebSocket-driven bot processing on market data updates
- 🏦 **Coinbase Integration**: Direct integration with Coinbase Advanced Trade API
- ⚡ **Background Processing**: Celery-based async task processing with Redis
- 📈 **Advanced Signals**: Enhanced RSI, Moving Average, MACD with -1 to +1 scoring
- 🎯 **Risk Management**: Sophisticated position sizing, stop-loss, and trade controls
- ✅ **Signal Confirmation**: Time-based signal verification to prevent false signals
- 🌡️ **Bot Temperature**: Hot 🔥/warm 🌡️/cool ❄️/frozen 🧊 indicators with sensitive testing thresholds
- 🚀 **HFT Ready**: High-frequency trading infrastructure foundation

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery, Redis, Pydantic V2, Real-time Polling, Fresh Evaluations
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, TanStack Query (5-second polling)
- **Database**: SQLite (single-user, production-ready)
- **Queue**: Redis for background task processing
- **API**: Coinbase Advanced Trade API with JWT authentication + Market Data
- **Real-time**: Proven polling architecture with fresh backend evaluations (no WebSocket complexity)
- **Testing**: 104 comprehensive tests with 100% pass rate, live API validation

## Bot-Centric Architecture

This system uses a **bot-centric approach** where:
- **One bot per trading pair** (e.g., "BTC Scalper" for BTC-USD)
- **Weighted signal aggregation** using configurable RSI, Moving Average, and MACD signals
- **Signal confirmation system** requiring consistency over time before trading
- **Advanced scoring** with -1 (strong sell) to +1 (strong buy) signal ranges
- **Trade controls** including step percentages, cooldown periods, and position limits
- **Real-time evaluation** automatically triggered by 5-second polling with fresh backend calculations
- **Proven polling architecture** combining WebSocket stability with responsive UI updates
- **Testing thresholds** (10x more sensitive) for rapid development feedback, production thresholds ready
- **Live market responsiveness** with automatic temperature and score updates

### Current Status (Phase 4.1 Active - Sept 3, 2025)
- ✅ **Real-Time Polling Architecture**: Proven 5-second polling with fresh backend evaluations  
- ✅ **Live Bot Temperatures**: BTC Scalper HOT 🔥 (0.522), ETH Momentum WARM 🌡️ (0.064)
- ✅ **Automatic UI Updates**: Values update without manual refresh, reactive components operational
- ✅ **Fresh Data Pipeline**: Backend performs live market calculations on each API request
- ✅ **Performance Optimized**: <100ms response times, efficient polling with TanStack Query
- ✅ **Temperature System Unified**: Single calculation source with testing/production thresholds
- ✅ **Signal Confirmation System**: Time-based validation prevents false signals
- ✅ **2 Production Bots** configured and actively showing live market responses
- ✅ **Weight Validation**: Signal weights properly enforced (≤ 1.0)  
- ✅ **104/104 tests passing** including comprehensive temperature and polling system validation
- ✅ **Pydantic V2 Migration**: Modern validation with enhanced schemas
- ✅ **Pristine Codebase**: No duplicate code, development artifacts, or temporary files
- ✅ **Proven Architecture**: Polling-based real-time updates more reliable than WebSocket for UI

## Quick Start

### Automated Setup (Recommended)

```bash
# First time setup
./scripts/setup.sh

# Start all services
./scripts/start.sh

# Open dashboard
open http://localhost:3000
```

### Management Commands

| Command | Description |
|---------|-------------|
| `./scripts/setup.sh` | Initial environment setup |
| `./scripts/start.sh` | Start all services |
| `./scripts/stop.sh` | Stop all services |
| `./scripts/restart.sh` | Restart all services |
| `./scripts/status.sh` | Check service status |
| `./scripts/logs.sh` | View application logs |

### Access Points

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc Documentation**: http://localhost:8000/api/redoc

### Manual Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

#### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

#### 1. Environment Setup
```bash
git clone <your-repo>
cd trader
cp .env.example .env
# Edit .env with your Coinbase API credentials
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
```

#### 4. Start Services Manually
```bash
# Terminal 1: Start Redis
docker-compose up redis

# Terminal 2: Start backend API
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Celery worker
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 4: Start Celery beat
cd backend && source venv/bin/activate  
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 5: Start frontend
cd frontend
npm run dev
```

</details>

## Configuration

### Coinbase API Setup

1. Visit [Coinbase Developer Portal](https://portal.cdp.coinbase.com/)
2. Create a new API key with trading permissions
3. Add credentials to `.env` file:

```env
COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END EC PRIVATE KEY-----\n"
```

### Current Bot Configuration (Phase 4.1)

The system currently has 2 production bots with live temperature monitoring:

**Production Bots (Live Status):**
- **BTC Scalper** (BTC-USD): RSI-focused bot with HOT 🔥 temperature (score: -0.756)
- **ETH Momentum Bot** (ETH-USD): Multi-signal bot with WARM 🌡️ temperature (score: -0.166)

**Temperature System:**
- **Unified Calculation**: Single source of truth in `app/utils/temperature.py`
- **Realistic Thresholds**: FROZEN (<0.05), COOL (≥0.05), WARM (≥0.15), HOT (≥0.3)
- **Real-time Updates**: Live temperature changes via WebSocket dashboard integration

### Enhanced Signal Processing (Phase 4.1)

Each bot uses the **BotSignalEvaluator** service with advanced signal types and unified temperature calculation:

**Signal Types:**
- **RSI**: Enhanced with -1 to +1 scoring, soft neutral zones, configurable thresholds
- **Moving Average**: Crossover detection with separation-based scoring algorithms
- **MACD**: Multi-factor analysis including histogram and zero-line crossover detection

**Signal Features:**
- **Weighted Aggregation**: Signal weights must total ≤ 1.0 (API enforced)
- **Score Range**: -1 (strong sell) to +1 (strong buy) with precise decimal scoring
- **Action Determination**: "buy", "sell", "hold" based on configurable thresholds
- **Confirmation System**: Time-based verification prevents false signal execution
- **Temperature Calculation**: Unified system with realistic thresholds for production trading

## Documentation

- **Management Scripts**: [scripts/README.md](scripts/README.md) - Detailed script documentation and troubleshooting
- **Visual Architecture**: [docs/VISUAL_ARCHITECTURE.md](docs/VISUAL_ARCHITECTURE.md) - Comprehensive system diagrams
- **Development Workflows**: [docs/DEVELOPMENT_WORKFLOWS.md](docs/DEVELOPMENT_WORKFLOWS.md) - Development process flows
- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Daily development guide
- **AI Instructions**: [.github/copilot-instructions.md](.github/copilot-instructions.md) - AI development guide

## Project Structure

```
trader/
├── scripts/          # Management scripts
│   ├── setup.sh      # Environment setup
│   ├── start.sh      # Start all services
│   ├── stop.sh       # Stop all services
│   ├── restart.sh    # Restart all services
│   ├── status.sh     # Service status check
│   ├── logs.sh       # Log management
│   └── README.md     # Script documentation
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Configuration and database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   │   └── signals/  # Trading signals
│   │   └── tasks/        # Celery background tasks
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Dashboard pages
│   │   ├── hooks/        # API hooks
│   │   └── types/        # TypeScript definitions
│   └── public/
├── docs/             # Visual documentation
│   ├── VISUAL_ARCHITECTURE.md
│   ├── DEVELOPMENT_WORKFLOWS.md
│   └── QUICK_REFERENCE.md
├── logs/             # Application logs (created by scripts)
├── .github/
│   └── copilot-instructions.md  # AI development guide
└── docker-compose.yml
```

## API Endpoints

### Bot Management API
- `GET /api/v1/bots/` - List all bots
- `POST /api/v1/bots/` - Create new bot
- `GET /api/v1/bots/{id}` - Get bot details
- `PUT /api/v1/bots/{id}` - Update bot configuration
- `DELETE /api/v1/bots/{id}` - Delete bot
- `POST /api/v1/bots/{id}/start` - Start bot
- `POST /api/v1/bots/{id}/stop` - Stop bot
- `GET /api/v1/bots/{id}/confirmation-status` - Get signal confirmation status

### WebSocket API (Phase 3.3)
- `POST /api/v1/ws/websocket/start` - Start live market data stream
- `POST /api/v1/ws/websocket/stop` - Stop market data stream
- `GET /api/v1/ws/websocket/status` - Check WebSocket connection health

### Bot Temperature API (Phase 3.3)
- `GET /api/v1/bot-temperatures/` - Get all running bot temperatures (unified system)
- `GET /api/v1/bot-temperatures/dashboard` - Get temperature summary dashboard
- `GET /api/v1/bot-temperatures/{id}` - Get individual bot temperature status

### Market Data
- `GET /api/v1/market/products` - List trading pairs
- `GET /api/v1/market/ticker/{product_id}` - Get price ticker
- `GET /api/v1/market/accounts` - Get account balances

### Trading
- `GET /api/v1/trades` - Get trade history

## Development

### Daily Workflow

```bash
# Start your development session
./scripts/start.sh

# Check everything is running
./scripts/status.sh

# Follow logs during development  
./scripts/logs.sh -f all

# End your session
./scripts/stop.sh
```

### Debugging

```bash
# Check service health
./scripts/status.sh

# View specific service logs
./scripts/logs.sh backend
./scripts/logs.sh frontend  
./scripts/logs.sh worker
./scripts/logs.sh beat

# Restart after changes
./scripts/restart.sh
```

For detailed troubleshooting, see [scripts/README.md](scripts/README.md).

### Adding New Signals

Signals are now configured within bots rather than as standalone entities:

1. Create signal class in `backend/app/services/signals/`
2. Inherit from `BaseSignal` 
3. Implement `calculate()` method returning score (-1 to 1)
4. Register in signal factory (`signals/base.py`)
5. Add to bot's `signal_config` JSON with weight ≤ 1.0

### Bot Configuration Example

```json
{
  "name": "BTC Strategy Bot",
  "pair": "BTC-USD", 
  "position_size_usd": 250,
  "signal_config": {
    "rsi": {
      "enabled": true,
      "weight": 0.4,
      "period": 14,
      "buy_threshold": 30,
      "sell_threshold": 70
    },
    "moving_average": {
      "enabled": true,
      "weight": 0.6,
      "fast_period": 10,
      "slow_period": 20
    }
  }
}
```

### Key API Endpoints (Phase 3.3)

**Bot Management:**
- `GET /api/v1/bots/` - List all bots with live status
- `POST /api/v1/bots/` - Create new bot with signal configuration
- `PUT /api/v1/bots/{bot_id}` - Update bot parameters
- `POST /api/v1/bots/{bot_id}/start` - Start bot trading
- `POST /api/v1/bots/{bot_id}/stop` - Stop bot trading
- `GET /api/v1/bots/{bot_id}/confirmation-status` - Get signal confirmation status

**Signal Evaluation:**
- `POST /api/v1/bot-evaluation/{bot_id}/evaluate` - Evaluate bot signals with live market data
- `GET /api/v1/bot-evaluation/test/{bot_id}` - Test bot evaluation with mock data

**Bot Temperature (Unified System):**
- `GET /api/v1/bot-temperatures/` - Get all running bot temperatures
- `GET /api/v1/bot-temperatures/dashboard` - Temperature dashboard summary
- `GET /api/v1/bot-temperatures/{bot_id}` - Individual bot temperature details

**WebSocket Market Data:**
- `POST /api/v1/ws/websocket/start` - Start live market data stream
- `POST /api/v1/ws/websocket/stop` - Stop market data stream
- `GET /api/v1/ws/websocket/status` - Check WebSocket connection health

**Market Data:**
- `GET /api/v1/market/ticker/{product_id}` - Live price data
- `GET /api/v1/market/candles/{product_id}` - Historical candlestick data
- `GET /api/v1/market/products` - Available trading pairs

**Documentation:**
- `GET /api/docs` - Interactive Swagger UI
- `GET /api/redoc` - ReDoc documentation

### Running Tests

```bash
# Backend tests (104 tests - 100% passing)
cd backend && source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test
```

## Phase 4 Ready: Position Management

With Phase 3.3 complete, the system is ready for Phase 4.1:
- **Real Trading Engine**: Direct implementation with micro-positions and safety systems
- **Position Tracking**: Monitor current positions with P&L calculation  
- **Risk Management**: Automated stop-loss using the unified temperature system
- **Real-time Trading Dashboard**: Enhanced polling integration for live position updates

## Latest Achievements (September 3, 2025)

### **Real-Time System Performance (Verified Working)**
- ✅ **Live Bot Status**: BTC Scalper showing HOT 🔥 (0.522), ETH Momentum showing WARM 🌡️ (0.064)
- ✅ **Automatic Updates**: UI refreshes every 5 seconds without manual page refresh
- ✅ **Fresh Data**: Backend performs live market calculations on each API request (no stale data)
- ✅ **Responsive Architecture**: Temperature changes reflect live market conditions immediately
- ✅ **Performance**: Sub-100ms API response times with efficient polling patterns

### **Development Insights for Future Enhancement**
- **Polling > WebSocket**: Simple polling architecture proved more reliable than complex WebSocket implementations
- **Fresh Backend Evaluations**: Critical to perform live calculations rather than using cached database values
- **Temperature Enum Consistency**: Frontend-backend alignment essential ('COOL' not 'COLD')
- **Reactive UI Patterns**: TanStack Query with aggressive polling settings provides smooth real-time experience
- **Test Hygiene**: Automated test bot cleanup prevents data pollution during development

### **Technical Foundation Ready for Phase 4**
- **Clean Production State**: 2 production bots, 104/104 tests passing, no development artifacts
- **Unified Temperature System**: Single source of truth with realistic production thresholds
- **Signal Confirmation**: Time-based validation prevents false trading signals
- **Modern Architecture**: React 18, FastAPI, Pydantic V2, TanStack Query optimized for rapid development

## Safety Features

⚠️ **Important**: This bot is for educational purposes. Always:

- Start with small micro-positions ($5-10)
- Use comprehensive safety systems and limits
- Monitor positions closely
- Set appropriate risk limits

## License

MIT License - see LICENSE file for details
