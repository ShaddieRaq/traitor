# 🏗️ Current System Architecture
*Analysis of existing monolithic trading system - October 3, 2025*

## 📊 **System Overview**

### **Current State**
- **Architecture Pattern**: Monolithic FastAPI application
- **Database**: SQLite with dual-table pattern (Trade + RawTrade)
- **Caching**: Three overlapping cache systems (technical debt)
- **Bot Management**: 39 individual bot entities
- **Execution**: Naive market orders only
- **Performance**: 3/39 bots profitable (7.7% success rate)

### **Core Technology Stack**
```
Frontend: React 18 + TypeScript + TanStack Query + Tailwind
Backend:  FastAPI + SQLAlchemy + Pydantic + Python 3.10
Database: SQLite (dual location issue - /trader.db + backend/trader.db)
Cache:    Redis + multiple cache layers (MarketDataCache, MarketDataService, SharedCacheManager)
Queue:    Celery + Redis for background tasks
```

---

## 🏛️ **Component Architecture**

### **1. FastAPI Backend Structure**
```
backend/app/
├── main.py                 # Application entry point
├── core/
│   ├── config.py          # Settings and environment variables
│   ├── database.py        # SQLAlchemy setup and session management
│   └── dependencies.py    # Dependency injection patterns
├── models/
│   └── models.py          # All database models (Bot, Trade, RawTrade, etc.)
├── services/              # Business logic layer
│   ├── coinbase_service.py        # Coinbase API integration
│   ├── bot_evaluator.py           # Signal aggregation and scoring
│   ├── market_data_cache.py       # Legacy LRU cache (90s TTL)
│   ├── market_data_service.py     # Redis-based cache (60s TTL)
│   ├── shared_cache_manager.py    # Third cache system (unused?)
│   └── sync_coordinated_coinbase_service.py  # API coordination
├── api/                   # FastAPI route handlers
│   ├── bots.py           # Bot CRUD operations
│   ├── market.py         # Market data endpoints
│   ├── trades.py         # Trade history and management
│   └── [20+ other endpoint files]
└── tasks/                 # Celery background tasks
    ├── celery_app.py     # Celery configuration
    └── trading_tasks.py  # Bot evaluation and trading tasks
```

### **2. Database Schema (SQLAlchemy Models)**

#### **Core Trading Entities**
```python
# Bot Model - Individual trading bot configuration
class Bot(Base):
    id: int
    product_id: str                    # Trading pair (e.g., "BTC-USD")
    signal_config: str                 # JSON config for RSI, MA, MACD
    current_combined_score: float      # Latest signal strength (-1 to +1)
    last_evaluation: datetime
    is_active: bool
    
# Trade Model - Operational trading decisions
class Trade(Base):
    id: int
    bot_id: int
    product_id: str
    side: str                          # "buy" or "sell"
    size: str
    price: str
    created_at: datetime
    status: str
    
# RawTrade Model - Financial truth from Coinbase
class RawTrade(Base):
    id: int
    coinbase_order_id: str
    product_id: str
    side: str
    size: str
    price: str
    fill_fees: str
    created_at: datetime
    status: str
```

#### **Supporting Entities**
```python
# Market data and caching
class CachedMarketData(Base)
class ErrorLog(Base)
class SystemError(Base)

# Analytics and monitoring  
class TrendData(Base)
class IntelligenceMetrics(Base)
```

### **3. Signal Processing System**

#### **Signal Factory Pattern**
```python
# Located: backend/app/services/signals/base.py
def create_signal_instance(signal_type: str, parameters: dict):
    """
    Maps signal names to signal classes:
    'rsi' → RSISignal
    'moving_average' → MovingAverageSignal  
    'macd' → MACDSignal
    """
```

#### **Bot Signal Configuration**
```python
# Each Bot.signal_config contains JSON:
{
  "rsi": {
    "enabled": true,
    "weight": 0.4,
    "period": 14,
    "buy_threshold": 30,
    "sell_threshold": 70
  },
  "moving_average": {
    "enabled": true,
    "weight": 0.35,
    "fast_period": 10,
    "slow_period": 20
  },
  "macd": {
    "enabled": true,
    "weight": 0.25,
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9
  }
}
```

#### **Signal Aggregation Logic**
```python
# BotSignalEvaluator.evaluate_bot() process:
1. Load market data for trading pair
2. Create signal instances from Bot.signal_config
3. Calculate individual signal scores (-1 to +1)
4. Compute weighted average: combined_score = Σ(weight × signal_score)
5. Apply trading thresholds (±0.05 default)
6. Generate BUY/SELL/HOLD decision
7. Update Bot.current_combined_score in database
```

### **4. Market Data & Caching Architecture**

#### **Problem: Three Overlapping Cache Systems**

**MarketDataCache (Legacy)**
```python
# File: market_data_cache.py
# Type: Thread-safe LRU cache with 90-second TTL
# Hit Rate: ~80-85%
# Issues: Memory-only, not shared across processes
```

**MarketDataService (Phase 7)**
```python
# File: market_data_service.py  
# Type: Redis-based cache with 60-second TTL
# Hit Rate: 95%+ with batch refresh every 30 seconds
# Issues: Not consistently used throughout codebase
```

**SharedCacheManager**
```python
# File: shared_cache_manager.py
# Type: Unused/experimental cache system
# Status: Technical debt - should be removed
```

#### **Data Flow Issues**
```
API Request → Which cache? → Market data fetch → Cache inconsistency
```

### **5. Trading Execution System**

#### **Current Execution Pattern (Naive)**
```python
# All trades use market orders only
coinbase_service.place_market_order(
    product_id="BTC-USD",
    side="buy", 
    size="0.001"
)

# Problems:
# - 100% taker fees (0.5%)
# - No slippage control
# - No order size optimization
# - No regime awareness
```

#### **Risk Management (Minimal)**
```python
# Only individual bot thresholds
buy_threshold = -0.05   # Buy when signal < -0.05
sell_threshold = 0.05   # Sell when signal > 0.05

# Missing:
# - Portfolio-level risk
# - Correlation awareness
# - Position sizing rules
# - Drawdown controls
```

### **6. Frontend Architecture**

#### **React Component Structure**
```
frontend/src/
├── pages/
│   └── DashboardRedesigned.tsx     # Main dashboard (unified view)
├── components/
│   └── Dashboard/
│       ├── TieredBotsView.tsx      # Bot display grid
│       ├── PortfolioSummaryCard.tsx # P&L and metrics
│       └── [other components]
├── hooks/
│   ├── useBots.ts                  # Bot data fetching
│   ├── useMarketData.ts            # Market data hooks
│   └── [other hooks]
└── services/
    └── api.ts                      # API client functions
```

#### **Data Fetching Pattern**
```typescript
// Aggressive 5-second polling for real-time updates
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

---

## ⚠️ **Critical Problems Identified**

### **1. Architectural Issues**

**Monolithic Structure**
- All functionality in single FastAPI app
- Tight coupling between components
- Difficult to test individual features
- Cannot scale components independently

**Cache System Chaos**
- Three different caching implementations
- Inconsistent cache usage throughout codebase
- Cache invalidation conflicts
- Memory waste and confusion

**Database Design Issues**
- Data split between two SQLite files
- No clear data ownership boundaries
- Difficult to backup and migrate
- Single point of failure

### **2. Trading Logic Problems**

**No Regime Awareness**
- Same strategy in bull/bear/sideways markets
- No adaptation to market volatility
- No crisis detection and response

**Naive Execution**
- 100% market orders = 100% taker fees
- No consideration of order book depth
- No slippage protection
- No order size optimization

**Weak Risk Management**
- No portfolio-level risk controls
- No correlation analysis between pairs
- No position sizing based on volatility
- No automatic stop-loss or drawdown protection

### **3. Performance Issues**

**Rate Limiting**
- Still hitting Coinbase API limits despite caching
- No proper request queuing or throttling
- Inefficient data fetching patterns

**Poor Bot Performance**
- Only 3/39 bots profitable (7.7%)
- No clear edge in trading logic
- High transaction costs eating profits

---

## 📈 **System Metrics & KPIs**

### **Current Performance**
```python
# Bot Performance (as of October 2025)
Total Bots: 39
Profitable Bots: 3 (AVNT-USD +$61.17, USELESS-USD +$10.03, XTZ-USD +$2.75)
Losing Bots: 36
Success Rate: 7.7%
Net P&L: Minimal positive (transaction costs eating profits)
```

### **Technical Metrics**
```python
# Cache Performance
MarketDataCache Hit Rate: 80.94%
MarketDataService Hit Rate: 99.97%
API Rate Limit Breaches: Frequent
System Uptime: ~95% (manual restarts required)
```

### **Execution Metrics**
```python
# Trading Costs
Taker Fee Ratio: 100% (all market orders)
Average Spread Cost: 0.1-0.3% per trade
Slippage: Uncontrolled
Total Cost per Trade: ~0.6-0.8%
```

---

## 🔄 **Data Flow Analysis**

### **Current Trading Flow**
```
1. Celery Task Scheduler (every 5 minutes)
   ↓
2. BotSignalEvaluator.evaluate_bot()
   ↓
3. Fetch market data (cache miss = API call)
   ↓
4. Calculate RSI, MA, MACD signals
   ↓
5. Combine signals with weights
   ↓
6. Check ±0.05 thresholds
   ↓
7. Place market order (if signal strong enough)
   ↓
8. Update database with trade record
```

### **Problems in Current Flow**
- No regime check before trading
- No portfolio risk check
- No correlation analysis
- No execution optimization
- No post-trade risk monitoring

---

## 🛠 **Configuration Management**

### **Environment Variables**
```bash
# Core settings
DATABASE_URL="sqlite:////Users/lazy_genius/Projects/trader/trader.db"
COINBASE_API_KEY="[secrets]"
COINBASE_API_SECRET="[secrets]"
REDIS_URL="redis://localhost:6379"

# Feature flags
TRADING_ENABLED=true
CACHE_ENABLED=true
WEBSOCKET_ENABLED=false
```

### **Bot Configuration Pattern**
```python
# Each bot configured via Bot.signal_config JSON
# No centralized parameter management
# No A/B testing framework
# Manual configuration updates only
```

---

## 📊 **Service Dependencies**

### **Internal Dependencies**
```
FastAPI Main App
├── depends on: SQLAlchemy models
├── depends on: Coinbase service
├── depends on: Market data cache(s)
├── depends on: Bot evaluator
└── depends on: Celery tasks

Celery Workers
├── depends on: Database connection
├── depends on: Coinbase API
├── depends on: Cache systems
└── depends on: Bot signal logic
```

### **External Dependencies**
```
Coinbase API (REST + WebSocket)
├── Rate limits: 10 requests/second
├── Authentication: API key + secret + passphrase
└── Data: OHLCV, tickers, account info, order placement

Redis
├── Used for: Celery task queue + market data caching
├── Memory usage: Growing over time
└── Persistence: None (cache only)
```

---

## 🚨 **Technical Debt Summary**

### **High Priority Issues**
1. **Multiple cache systems** - Consolidate to single source of truth
2. **Monolithic architecture** - Break into microservices
3. **No regime detection** - Add market condition awareness
4. **Naive execution** - Implement smart order routing
5. **Weak risk management** - Add portfolio-level controls

### **Medium Priority Issues**
1. **Database split** - Consolidate to single database
2. **Manual configuration** - Add dynamic parameter management
3. **Poor error handling** - Improve resilience and recovery
4. **Limited monitoring** - Add comprehensive observability

### **Low Priority Issues**
1. **Code organization** - Improve module structure
2. **Documentation gaps** - Complete API documentation
3. **Test coverage** - Increase automated testing
4. **Performance optimization** - Optimize hot paths

---

## 🎯 **Refactoring Strategy**

### **Phase 1: Foundation Cleanup**
- Consolidate cache systems to single Redis-based solution
- Extract market data gateway as separate service
- Clean up database architecture

### **Phase 2: Core Intelligence**
- Add regime detection service
- Implement correlation analysis
- Build portfolio risk management

### **Phase 3: Execution Optimization**
- Replace market orders with smart execution
- Add maker/taker optimization
- Implement TWAP for large orders

### **Phase 4: Architecture Modernization**
- Convert to microservices
- Add service mesh and monitoring
- Implement automated deployment

---

*This document provides a complete analysis of the current system architecture. Use this as reference when planning refactoring efforts.*