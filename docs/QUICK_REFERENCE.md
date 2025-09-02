# Quick Reference Visual Guide

This document provides quick visual references for common development tasks and project navigation.

## Project Structure Overview

```
trader/
├── 📊 docs/                          # Visual documentation
│   ├── VISUAL_ARCHITECTURE.md        # Main architectural diagrams
│   ├── DEVELOPMENT_WORKFLOWS.md      # Development process diagrams
│   └── QUICK_REFERENCE.md            # This file
├── 🐍 backend/                       # Python FastAPI backend
│   ├── app/
│   │   ├── 🔌 api/                   # REST API endpoints
│   │   │   ├── signals.py            # Signal management API
│   │   │   ├── trades.py             # Trading operations API
│   │   │   ├── market.py             # Market data API
│   │   │   └── schemas.py            # Pydantic models
│   │   ├── ⚙️ core/                  # Core configuration
│   │   │   ├── config.py             # Settings & environment
│   │   │   └── database.py           # SQLAlchemy setup
│   │   ├── 📝 models/                # Database models
│   │   │   └── models.py             # SQLAlchemy models
│   │   ├── 🔧 services/              # Business logic
│   │   │   ├── coinbase_service.py   # Coinbase API client
│   │   │   └── signals/              # Signal implementations
│   │   │       ├── base.py           # Abstract base signal
│   │   │       └── technical.py      # RSI & MA signals
│   │   ├── ⚡ tasks/                 # Background tasks
│   │   │   ├── celery_app.py         # Celery configuration
│   │   │   ├── data_tasks.py         # Data collection tasks
│   │   │   └── trading_tasks.py      # Signal evaluation tasks
│   │   └── main.py                   # FastAPI application
│   └── requirements.txt              # Python dependencies
├── ⚛️ frontend/                      # React TypeScript frontend
│   ├── src/
│   │   ├── 📱 pages/                 # Main page components
│   │   │   ├── Dashboard.tsx         # Main overview page
│   │   │   ├── Signals.tsx           # Signal management page
│   │   │   ├── Trades.tsx            # Trade history page
│   │   │   └── Market.tsx            # Market data page
│   │   ├── 🪝 hooks/                 # Custom React hooks
│   │   │   ├── useSignals.ts         # Signal API hooks
│   │   │   └── useMarket.ts          # Market data hooks
│   │   ├── 🎯 types/                 # TypeScript definitions
│   │   │   └── index.ts              # API response types
│   │   ├── App.tsx                   # Main application
│   │   └── main.tsx                  # React entry point
│   ├── package.json                  # Node dependencies
│   └── tailwind.config.js            # TailwindCSS config
├── 🐳 docker-compose.yml             # Redis service
├── 📋 .env.example                   # Environment template
└── 📖 README.md                      # Project documentation
```

## Quick Command Reference

### Development Startup Commands
```bash
# Backend Setup (Terminal 1)
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend Setup (Terminal 2)
cd /Users/lazy_genius/Projects/trader/frontend
npm install
npm run dev

# Background Services (Terminal 3)
cd /Users/lazy_genius/Projects/trader
docker-compose up redis

# Celery Worker (Terminal 4)
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Scheduler (Terminal 5)
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

## Signal Development Quick Guide

### Adding a New Signal
```mermaid
flowchart LR
    CREATE[Create Signal Class] --> INHERIT[Inherit from BaseSignal]
    INHERIT --> IMPLEMENT[Implement calculate() method]
    IMPLEMENT --> REGISTER[Register in signal factory]
    REGISTER --> DATABASE[Add to database]
    DATABASE --> TEST[Test signal logic]
    TEST --> UI[Update frontend if needed]
    
    style CREATE fill:#e3f2fd
    style TEST fill:#c8e6c9
    style UI fill:#f3e5f5
```

### Signal Implementation Template
```python
# backend/app/services/signals/my_signal.py
from typing import Dict, Any
import pandas as pd
from .base import BaseSignal

class MySignal(BaseSignal):
    def __init__(self, param1: float = 10, param2: float = 0.5, **kwargs):
        super().__init__(
            name="MySignal",
            description="Description of what this signal does",
            param1=param1,
            param2=param2,
            **kwargs
        )
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.is_valid_data(data):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {}}
        
        # Your signal calculation logic here
        param1 = self.parameters["param1"]
        param2 = self.parameters["param2"]
        
        # Calculate your indicator
        # Example: moving_average = data['close'].rolling(param1).mean()
        
        # Generate score (-1 to 1)
        score = 0.0  # Your calculation
        
        # Determine action
        if score > param2:
            action = "buy"
        elif score < -param2:
            action = "sell"
        else:
            action = "hold"
        
        # Calculate confidence (0 to 1)
        confidence = abs(score)
        
        return {
            "score": score,
            "action": action, 
            "confidence": confidence,
            "metadata": {
                "param1_value": param1,
                "param2_value": param2,
                # Add any additional debug info
            }
        }
```

## API Quick Reference

### Key Endpoints
```mermaid
graph LR
    subgraph "Signal Management"
        GET_SIG[GET /api/v1/signals<br/>List all signals]
        PUT_SIG[PUT /api/v1/signals/{id}<br/>Update signal config]
        GET_RESULTS[GET /api/v1/signals/results<br/>Latest signal scores]
    end
    
    subgraph "Trading Operations"
        GET_TRADES[GET /api/v1/trades<br/>Trade history]
        POST_TRADE[POST /api/v1/trades<br/>Manual trade execution]
        GET_STATUS[GET /api/v1/trades/status<br/>Current positions]
    end
    
    subgraph "Market Data"
        GET_PRICE[GET /api/v1/market/price<br/>Current prices]
        GET_CANDLES[GET /api/v1/market/candles<br/>Historical OHLCV]
        WS_FEED[WebSocket /ws<br/>Real-time updates]
    end
    
    style GET_SIG fill:#e3f2fd
    style GET_TRADES fill:#fff3e0
    style GET_PRICE fill:#f3e5f5
    style WS_FEED fill:#e8f5e8
```

### Request/Response Examples
```typescript
// Signal Configuration Update
PUT /api/v1/signals/1
{
  "enabled": true,
  "weight": 1.5,
  "parameters": {
    "period": 14,
    "oversold": 25,
    "overbought": 75
  }
}

// Signal Results Response
GET /api/v1/signals/results
{
  "signals": [
    {
      "id": 1,
      "name": "RSI",
      "score": 0.8,
      "action": "buy",
      "confidence": 0.9,
      "timestamp": "2025-09-02T10:30:00Z"
    }
  ]
}

// Market Data Response
GET /api/v1/market/price?product_id=BTC-USD
{
  "product_id": "BTC-USD",
  "price": 65432.10,
  "timestamp": "2025-09-02T10:30:00Z",
  "volume_24h": 1234567.89
}
```

## Frontend Component Quick Reference

### Component Architecture
```mermaid
graph TB
    APP[App.tsx] --> ROUTER[React Router]
    ROUTER --> DASH[Dashboard.tsx]
    ROUTER --> SIG[Signals.tsx]
    ROUTER --> TRADES[Trades.tsx]
    ROUTER --> MARKET[Market.tsx]
    
    subgraph "Shared Hooks"
        USE_SIG[useSignals.ts]
        USE_MARKET[useMarket.ts]
    end
    
    subgraph "TanStack Query"
        CACHE[Query Cache]
        MUTATIONS[Mutations]
    end
    
    DASH --> USE_SIG
    SIG --> USE_SIG
    MARKET --> USE_MARKET
    
    USE_SIG --> CACHE
    USE_MARKET --> CACHE
    
    style APP fill:#e3f2fd
    style USE_SIG fill:#c8e6c9
    style CACHE fill:#fff9c4
```

### Adding a New Page
```bash
# 1. Create page component
touch frontend/src/pages/MyPage.tsx

# 2. Add route in App.tsx
# Add to imports: import MyPage from './pages/MyPage';
# Add to routes: <Route path="/mypage" element={<MyPage />} />

# 3. Add navigation link
# Add to navigation section with appropriate icon

# 4. Create custom hook if needed
touch frontend/src/hooks/useMyData.ts
```

## Database Quick Reference

### Model Relationships
```mermaid
erDiagram
    Signal ||--o{ SignalResult : "has many"
    Signal {
        id int PK
        name string
        enabled boolean
        weight float
        parameters json
    }
    
    SignalResult {
        id int PK
        signal_id int FK
        product_id string
        score float
        action string
        confidence float
        timestamp datetime
    }
    
    Trade {
        id int PK
        product_id string
        side string
        size float
        price float
        order_id string
        status string
        signal_scores json
    }
    
    MarketData {
        id int PK
        product_id string
        timestamp datetime
        timeframe string
        open_price float
        high_price float
        low_price float
        close_price float
        volume float
    }
```

### Common Database Operations
```python
# Get all enabled signals
enabled_signals = db.query(Signal).filter(Signal.enabled == True).all()

# Get latest signal results
latest_results = db.query(SignalResult)\
    .filter(SignalResult.product_id == "BTC-USD")\
    .order_by(SignalResult.timestamp.desc())\
    .limit(10).all()

# Get recent trades
recent_trades = db.query(Trade)\
    .filter(Trade.status == "filled")\
    .order_by(Trade.filled_at.desc())\
    .limit(20).all()

# Get market data for calculation
market_data = db.query(MarketData)\
    .filter(MarketData.product_id == "BTC-USD")\
    .filter(MarketData.timeframe == "1h")\
    .order_by(MarketData.timestamp.desc())\
    .limit(100).all()
```

## Troubleshooting Quick Guide

### Common Issues & Solutions
```mermaid
flowchart TD
    ISSUE[Issue Encountered] --> TYPE{Issue Type?}
    
    TYPE -->|Frontend Build Error| FE_ISSUE[Frontend Issue]
    TYPE -->|Backend API Error| BE_ISSUE[Backend Issue]
    TYPE -->|Database Error| DB_ISSUE[Database Issue]
    TYPE -->|Celery Task Error| CELERY_ISSUE[Celery Issue]
    
    FE_ISSUE --> FE_CHECK[Check npm install<br/>Check TypeScript errors<br/>Check import paths]
    BE_ISSUE --> BE_CHECK[Check virtual environment<br/>Check pip install<br/>Check .env file]
    DB_ISSUE --> DB_CHECK[Check database file exists<br/>Check SQLAlchemy models<br/>Restart FastAPI]
    CELERY_ISSUE --> CELERY_CHECK[Check Redis running<br/>Check worker logs<br/>Restart Celery services]
    
    FE_CHECK --> SOLUTION[Apply Solution]
    BE_CHECK --> SOLUTION
    DB_CHECK --> SOLUTION
    CELERY_CHECK --> SOLUTION
    
    SOLUTION --> TEST[Test Fix]
    TEST --> SUCCESS{Fixed?}
    SUCCESS -->|Yes| DONE[Continue Development]
    SUCCESS -->|No| ESCALATE[Check Logs & Documentation]
    
    style ISSUE fill:#ffcdd2
    style DONE fill:#c8e6c9
    style ESCALATE fill:#fff9c4
```

### Log Locations
```bash
# FastAPI logs (in terminal where uvicorn is running)
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Celery worker logs
cd /Users/lazy_genius/Projects/trader/backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# React development logs (in terminal where npm run dev is running)
cd /Users/lazy_genius/Projects/trader/frontend
npm run dev

# Browser console for frontend errors
# Open browser dev tools (F12) and check Console tab
```

## Performance Monitoring

### Key Metrics to Watch
```mermaid
graph TD
    subgraph "Frontend Performance"
        FE_LOAD[Page Load Time<br/>Target: < 2s]
        FE_INT[Interaction Response<br/>Target: < 100ms]
        FE_BUILD[Build Time<br/>Target: < 30s]
    end
    
    subgraph "Backend Performance"
        API_RESP[API Response Time<br/>Target: < 500ms]
        DB_QUERY[Database Query Time<br/>Target: < 100ms]
        SIGNAL_CALC[Signal Calculation<br/>Target: < 5s]
    end
    
    subgraph "Trading Performance"
        TRADE_LAT[Trade Execution<br/>Target: < 2s]
        SIGNAL_ACC[Signal Accuracy<br/>Target: > 60%]
        UPTIME[System Uptime<br/>Target: > 99%]
    end
    
    style FE_LOAD fill:#e3f2fd
    style API_RESP fill:#c8e6c9
    style TRADE_LAT fill:#fff9c4
```

This quick reference guide provides immediate access to the most common development tasks and navigation points for leading the trading bot project effectively.
