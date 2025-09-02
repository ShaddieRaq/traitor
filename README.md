# Signal-Based Coinbase Trading Bot

A modern, signal-based cryptocurrency trading bot with a web dashboard, built with Python (FastAPI) backend and React frontend.

## Features

- 🎯 **Signal-Based Trading**: Configurable trading signals with individual enable/disable controls
- 📊 **Web Dashboard**: Modern React interface for monitoring and management
- 🔄 **Real-Time Data**: Live market data and signal processing
- 🏦 **Coinbase Integration**: Direct integration with Coinbase Advanced Trade API
- ⚡ **Background Processing**: Celery-based async task processing
- 📈 **Technical Analysis**: Built-in RSI, Moving Average, and extensible signal framework

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery
- **Frontend**: React, TypeScript, TailwindCSS
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Queue**: Redis
- **API**: Coinbase Advanced Trade API

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

### Default Signals

The bot comes with two pre-configured signals:

- **RSI**: Relative Strength Index (14 period, 30/70 levels)
- **MA Crossover**: Moving Average crossover (10/20 period)

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

- `GET /api/v1/signals` - List all signals
- `POST /api/v1/signals/{id}/toggle` - Enable/disable signal
- `GET /api/v1/market/ticker/{product_id}` - Get price ticker
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

1. Create signal class in `backend/app/services/signals/`
2. Inherit from `BaseSignal`
3. Implement `calculate()` method
4. Register in signal factory

### Running Tests

```bash
# Backend tests
cd backend && source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test
```

## Safety Features

⚠️ **Important**: This bot is for educational purposes. Always:

- Test with small amounts
- Use paper trading first
- Monitor positions closely
- Set appropriate risk limits

## License

MIT License - see LICENSE file for details
