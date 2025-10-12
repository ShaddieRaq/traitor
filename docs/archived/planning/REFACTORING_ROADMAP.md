# 🛣️ Refactoring Roadmap
*Step-by-step transformation from monolithic to microservices architecture*

## 🎯 **Transformation Overview**

### **Current State → Target State**
```
BEFORE (Monolithic):                    AFTER (Microservices):
┌─────────────────────────┐            ┌──────────────┐ ┌──────────────┐
│                         │            │ Market Data  │ │ Regime       │
│   Single FastAPI App   │    →       │ Gateway      │ │ Detection    │
│                         │            │ :8001        │ │ :8002        │
│  - 39 Bot entities      │            └──────────────┘ └──────────────┘
│  - 3 cache systems     │                     │               │
│  - Naive execution     │            ┌──────────────┐ ┌──────────────┐
│  - No regime awareness │            │ Risk         │ │ Execution    │
│  - No risk management  │            │ Management   │ │ Engine       │
│                         │            │ :8003        │ │ :8004        │
└─────────────────────────┘            └──────────────┘ └──────────────┘
```

### **Success Criteria**
- **Performance**: 60%+ profitable bots (vs 7.7% current)
- **Costs**: 40% reduction in transaction fees
- **Reliability**: 99.5% uptime with graceful degradation
- **Architecture**: Zero circular dependencies, independent services

---

## 📅 **8-Week Implementation Schedule**

### **🔧 Phase 1: Foundation Stabilization (Weeks 1-2)**
*Fix critical infrastructure issues preventing refactoring*

#### **Week 1: Cache System Consolidation**

**Day 1-2: Cache Analysis & Planning**
```bash
# Audit current cache usage
grep -r "MarketDataCache\|MarketDataService\|SharedCacheManager" backend/
# Document all cache access patterns
# Create consolidation plan
```

**Day 3-4: Remove Dead Code**
```bash
# Tasks:
1. Delete SharedCacheManager completely
2. Remove unused cache imports
3. Clean up related configuration
4. Update documentation

# Files to modify:
- backend/app/services/shared_cache_manager.py (DELETE)
- backend/app/services/ (clean imports)
- Any references in main.py or dependencies
```

**Day 5-7: Consolidate to MarketDataService**
```bash
# Replace all MarketDataCache usage:
1. Update coinbase_service.py imports
2. Replace cache method calls
3. Update error handling patterns
4. Test cache consistency

# Critical Fix:
# File: backend/app/services/coinbase_service.py
# Change: self.market_data_cache → self.market_data_service
# Test: Verify no import errors on startup
```

**Week 1 Success Criteria:**
- ✅ System starts without import errors
- ✅ Single cache system (MarketDataService only)
- ✅ Cache hit rate >95%
- ✅ No circular dependency errors

#### **Week 2: Database Cleanup**

**Day 1-2: Database Analysis**
```bash
# Audit database files:
ls -la /Users/lazy_genius/Projects/trader/trader.db
ls -la /Users/lazy_genius/Projects/trader/backend/trader.db

# Compare schemas and data
sqlite3 trader.db ".schema"
sqlite3 backend/trader.db ".schema"

# Identify data differences and dependencies
```

**Day 3-5: Database Consolidation**
```bash
# Tasks:
1. Backup both database files
2. Merge data to single /trader.db
3. Update DATABASE_URL configuration
4. Remove backend/trader.db
5. Test all database operations

# Configuration update:
DATABASE_URL="sqlite:////Users/lazy_genius/Projects/trader/trader.db"
```

**Day 6-7: Schema Validation**
```bash
# Add proper constraints:
1. Foreign key relationships
2. Data validation rules
3. Index optimization
4. Migration scripts

# Test:
- All CRUD operations work
- Data integrity maintained
- Performance not degraded
```

**Week 2 Success Criteria:**
- ✅ Single database file at project root
- ✅ All services connect successfully
- ✅ Data integrity validated
- ✅ Backup and restore procedures tested

### **🏗️ Phase 2: Service Extraction (Weeks 3-4)**
*Extract first microservices from monolithic application*

#### **Week 3: Market Data Gateway Service**

**Day 1-2: Service Design**
```python
# Create service specification:
# File: market-data-gateway/README.md

"""
Market Data Gateway Service
- Port: 8001
- Purpose: Centralized market data with caching
- API: REST endpoints for OHLCV, tickers, prices
- Cache: Redis with 60-second TTL
- Rate Limiting: Respect Coinbase limits
"""

# API Design:
GET /api/v1/price/{symbol}          # Current price
GET /api/v1/ohlcv/{symbol}         # Historical candles
GET /api/v1/ticker/{symbol}        # Real-time ticker
GET /health                        # Health check
GET /metrics                       # Performance metrics
```

**Day 3-5: Service Implementation**
```bash
# Create new service:
mkdir market-data-gateway
cd market-data-gateway

# Create FastAPI app:
touch main.py requirements.txt Dockerfile

# Implement core functionality:
1. Redis caching layer
2. Coinbase API integration
3. Rate limiting and circuit breakers
4. Health checks and metrics
5. Error handling and logging
```

**Day 6-7: Integration & Testing**
```bash
# Test service independently:
1. Unit tests for cache logic
2. Integration tests with Coinbase API
3. Performance tests under load
4. Error scenarios (API down, cache miss)

# Integration with main app:
1. Update main app to call Market Data Gateway
2. Add circuit breaker for service calls
3. Test fallback behavior when service down
```

**Week 3 Success Criteria:**
- ✅ Market Data Gateway running on port 8001
- ✅ Main app successfully calls gateway service
- ✅ Cache hit rate >95% maintained
- ✅ Graceful degradation when service unavailable

#### **Week 4: Service Communication Framework**

**Day 1-2: Communication Patterns**
```python
# Implement service client pattern:
# File: backend/app/services/service_client.py

class ServiceClient:
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self.circuit_breaker = CircuitBreaker()
        
    async def get(self, endpoint: str, timeout: int = 5):
        # HTTP client with retries, timeouts, circuit breaker
        
    async def health_check(self):
        # Service health validation
```

**Day 3-4: Service Discovery**
```python
# Configuration-based service discovery:
# File: backend/app/core/services.py

SERVICES = {
    "market_data": "http://localhost:8001",
    "regime_detection": "http://localhost:8002",  # Future
    "risk_management": "http://localhost:8003",   # Future
}

def get_service_client(service_name: str) -> ServiceClient:
    return ServiceClient(service_name, SERVICES[service_name])
```

**Day 5-7: Monitoring & Observability**
```python
# Add distributed tracing:
1. Request correlation IDs
2. Service call logging
3. Performance metrics collection
4. Error tracking and alerting

# Health check endpoints:
GET /health/dependencies  # Check all service dependencies
GET /health/detailed      # Detailed health information
```

**Week 4 Success Criteria:**
- ✅ Service communication framework implemented
- ✅ Circuit breaker pattern working
- ✅ Distributed tracing and correlation IDs
- ✅ Service health monitoring in place

### **🧠 Phase 3: Intelligence Services (Weeks 5-6)**
*Add regime detection and risk management services*

#### **Week 5: Regime Detection Service**

**Day 1-2: Regime Detection Logic**
```python
# Service implementation:
# File: regime-detection/main.py

class RegimeDetector:
    def classify_regime(self, symbol: str, timeframe: str = "1h") -> dict:
        """
        Returns:
        {
            "symbol": "BTC-USD",
            "regime": "TRENDING|RANGING|CHOPPY|CRISIS",
            "confidence": 0.85,
            "indicators": {
                "adx": 28.5,
                "choppiness": 35.2,
                "atr_normalized": 0.025
            },
            "timestamp": "2025-10-03T10:30:00Z"
        }
        """
        
    def calculate_adx(self, highs, lows, closes, period=14):
        # Average Directional Index implementation
        
    def calculate_choppiness(self, highs, lows, closes, period=20):
        # Choppiness Index implementation
        
    def detect_crisis(self, symbols: list) -> bool:
        # Crisis detection via correlation spikes
```

**Day 3-4: API Implementation**
```python
# REST API endpoints:
GET /api/v1/regime/{symbol}                    # Current regime
GET /api/v1/regime/{symbol}/history           # Historical regimes
POST /api/v1/regime/batch                     # Multiple symbols
GET /api/v1/regime/market-overview            # Overall market state
```

**Day 5-7: Integration with Trading Logic**
```python
# Update bot evaluation to check regime:
# File: backend/app/services/bot_evaluator.py

async def evaluate_bot(self, bot_id: int):
    # Get current regime
    regime_client = get_service_client("regime_detection")
    regime = await regime_client.get(f"/api/v1/regime/{bot.product_id}")
    
    # Skip trading in choppy/crisis markets
    if regime["regime"] in ["CHOPPY", "CRISIS"]:
        return {"action": "HOLD", "reason": "regime_block"}
    
    # Adjust strategy based on regime
    if regime["regime"] == "TRENDING":
        # Use momentum strategies
    elif regime["regime"] == "RANGING":
        # Use mean reversion strategies
```

**Week 5 Success Criteria:**
- ✅ Regime Detection Service running on port 8002
- ✅ Accurate regime classification (>80% accuracy)
- ✅ Bot evaluation integrated with regime checks
- ✅ Trading blocked in choppy/crisis conditions

#### **Week 6: Risk Management Service**

**Day 1-3: Portfolio Risk Engine**
```python
# Service implementation:
# File: risk-management/main.py

class RiskManager:
    def calculate_portfolio_var(self, positions: list, confidence: float = 0.95):
        """Calculate portfolio Value at Risk"""
        
    def check_position_limits(self, symbol: str, size: float, portfolio: dict):
        """Validate position against limits"""
        
    def calculate_correlation_matrix(self, symbols: list, lookback_days: int = 30):
        """Dynamic correlation calculation"""
        
    def kelly_position_size(self, edge: float, win_rate: float, volatility: float):
        """Kelly criterion position sizing"""
```

**Day 4-5: Risk API & Integration**
```python
# API endpoints:
POST /api/v1/risk/approve-trade    # Pre-trade risk check
GET /api/v1/risk/portfolio-var     # Current portfolio VaR
GET /api/v1/risk/correlation       # Correlation matrix
POST /api/v1/risk/position-size    # Optimal position sizing

# Integration with trading:
async def place_trade(self, bot_id: int, signal: dict):
    # Risk check before execution
    risk_client = get_service_client("risk_management")
    approval = await risk_client.post("/api/v1/risk/approve-trade", {
        "symbol": bot.product_id,
        "side": signal["action"],
        "size": signal["size"],
        "portfolio": await self.get_current_portfolio()
    })
    
    if not approval["approved"]:
        return {"status": "blocked", "reason": approval["reason"]}
```

**Day 6-7: Risk Monitoring & Alerts**
```python
# Real-time risk monitoring:
1. Portfolio VaR calculation every 15 minutes
2. Correlation spike detection
3. Position concentration alerts
4. Drawdown monitoring and circuit breakers
```

**Week 6 Success Criteria:**
- ✅ Risk Management Service running on port 8003
- ✅ Portfolio VaR calculated and monitored
- ✅ Position limits enforced before trades
- ✅ Correlation matrix updated hourly

### **⚡ Phase 4: Execution Optimization (Weeks 7-8)**
*Implement smart execution and complete strategy refactoring*

#### **Week 7: Smart Execution Engine**

**Day 1-3: Execution Algorithms**
```python
# Service implementation:
# File: execution-engine/main.py

class ExecutionEngine:
    def plan_execution(self, order: dict, market_conditions: dict) -> dict:
        """
        Choose execution strategy:
        - Small orders (<$1000): Market order
        - Medium orders ($1000-$5000): Post-only limit
        - Large orders (>$5000): TWAP execution
        """
        
    def execute_limit_order(self, symbol: str, side: str, size: float):
        """Post-only limit order execution"""
        
    def execute_twap(self, symbol: str, side: str, total_size: float, duration_minutes: int):
        """Time-weighted average price execution"""
        
    def calculate_execution_cost(self, fills: list) -> dict:
        """Calculate total execution cost including fees and slippage"""
```

**Day 4-5: Fee Optimization**
```python
# Maker/taker optimization:
1. Default to post-only limit orders (maker fees)
2. Upgrade to market orders only when urgent
3. Monitor fill rates and adjust spreads
4. Target 60%+ maker order ratio

# Cost tracking:
1. Track fees paid per trade
2. Monitor slippage and market impact
3. Calculate total cost per trade
4. Optimize order sizing and timing
```

**Day 6-7: Integration & Testing**
```python
# Replace naive market orders:
# File: backend/app/services/bot_evaluator.py

async def execute_trade(self, bot_id: int, signal: dict):
    # Use smart execution instead of direct market orders
    execution_client = get_service_client("execution_engine")
    
    execution_plan = await execution_client.post("/api/v1/execution/plan", {
        "symbol": bot.product_id,
        "side": signal["action"],
        "size": signal["size"],
        "urgency": signal.get("urgency", "normal")
    })
    
    result = await execution_client.post("/api/v1/execution/execute", execution_plan)
    return result
```

**Week 7 Success Criteria:**
- ✅ Execution Engine running on port 8004
- ✅ 60%+ of orders are maker orders (vs 0% current)
- ✅ TWAP execution for large orders working
- ✅ Total execution costs reduced by 40%

#### **Week 8: Strategy Engine & Final Integration**

**Day 1-3: Strategy Pattern Implementation**
```python
# Convert Bot entities to Strategy pattern:
# File: strategy-engine/strategies.py

class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, market_data: dict, regime: dict) -> dict:
        """Generate trading signal based on market conditions"""
        
class RSIMeanReversion(Strategy):
    def __init__(self, rsi_period: int = 14, buy_threshold: float = 30):
        self.rsi_period = rsi_period
        self.buy_threshold = buy_threshold
        
    def generate_signal(self, market_data: dict, regime: dict) -> dict:
        if regime["regime"] != "RANGING":
            return {"action": "HOLD", "confidence": 0.0}
            
        rsi = self.calculate_rsi(market_data["close"], self.rsi_period)
        if rsi < self.buy_threshold:
            return {"action": "BUY", "confidence": (self.buy_threshold - rsi) / self.buy_threshold}
```

**Day 4-5: Strategy Allocation & Management**
```python
# Dynamic strategy allocation:
class StrategyManager:
    def allocate_strategies(self, regime: dict, portfolio: dict) -> dict:
        """Allocate capital to strategies based on regime"""
        
        if regime["regime"] == "TRENDING":
            return {
                "momentum": 0.6,
                "trend_following": 0.3,
                "arbitrage": 0.1
            }
        elif regime["regime"] == "RANGING":
            return {
                "mean_reversion": 0.5,
                "pairs_trading": 0.3,
                "arbitrage": 0.2
            }
```

**Day 6-7: System Integration & Testing**
```python
# Complete end-to-end flow:
1. Market Data Gateway provides data
2. Regime Detection classifies market
3. Strategy Engine generates signals
4. Risk Management approves trades
5. Execution Engine optimizes execution
6. Portfolio Manager tracks positions

# Full system testing:
1. End-to-end trading flow tests
2. Service failure recovery tests
3. Performance and latency tests
4. Load testing with multiple strategies
```

**Week 8 Success Criteria:**
- ✅ All 5 microservices operational
- ✅ Strategy pattern implemented and tested
- ✅ End-to-end trading flow working
- ✅ System performance meets targets

---

## 📊 **Progress Tracking**

### **Weekly Checkpoints**

**Week 1 Checkpoint:**
- [ ] Cache system consolidated
- [ ] No circular dependencies
- [ ] System startup time <30 seconds
- [ ] Cache hit rate >95%

**Week 2 Checkpoint:**
- [ ] Single database operational
- [ ] All services connect successfully
- [ ] Data integrity validated
- [ ] Backup procedures tested

**Week 3 Checkpoint:**
- [ ] Market Data Gateway operational
- [ ] Service communication working
- [ ] Graceful degradation tested
- [ ] Performance benchmarks met

**Week 4 Checkpoint:**
- [ ] Service framework complete
- [ ] Monitoring and tracing active
- [ ] Circuit breakers functional
- [ ] Health checks comprehensive

**Week 5 Checkpoint:**
- [ ] Regime Detection operational
- [ ] Trading blocked in crisis/choppy
- [ ] Classification accuracy >80%
- [ ] Integration with bot evaluation

**Week 6 Checkpoint:**
- [ ] Risk Management operational
- [ ] Portfolio VaR calculated
- [ ] Position limits enforced
- [ ] Correlation monitoring active

**Week 7 Checkpoint:**
- [ ] Smart execution operational
- [ ] Maker order ratio >60%
- [ ] TWAP execution working
- [ ] Cost reduction achieved

**Week 8 Checkpoint:**
- [ ] Strategy pattern implemented
- [ ] All services integrated
- [ ] End-to-end flow tested
- [ ] Performance targets met

### **Success Metrics Tracking**

**Technical Metrics:**
```python
# Week 1-2: Foundation
Cache Consistency: 100%
Service Independence: 100%
Startup Reliability: >99%

# Week 3-4: Services
Service Uptime: >99.5%
API Latency: <100ms p95
Circuit Breaker Functionality: 100%

# Week 5-6: Intelligence  
Regime Classification Accuracy: >80%
Risk Check Latency: <1s
Portfolio VaR Accuracy: >85%

# Week 7-8: Execution
Maker Order Ratio: >60%
Execution Cost Reduction: >40%
End-to-End Latency: <2s
```

**Business Metrics:**
```python
# Trading Performance
Profitable Strategy Ratio: Track weekly
Risk-Adjusted Returns: Calculate Sharpe ratio
Maximum Drawdown: Monitor portfolio level
Transaction Cost per Trade: Track reduction

# System Reliability
System Uptime: 99.5% target
Manual Interventions: Minimize to zero
Error Recovery Time: <30 seconds
Service Deployment Time: <5 minutes
```

---

## ⚠️ **Risk Management**

### **Technical Risks & Mitigation**

**Service Communication Failures**
```python
Risk: Network issues between services
Mitigation: Circuit breakers, retries, fallback strategies
Testing: Chaos engineering, network partition tests
```

**Data Consistency Issues**
```python
Risk: Eventual consistency problems
Mitigation: Idempotent operations, reconciliation processes
Testing: Consistency checks, data validation
```

**Performance Degradation**
```python
Risk: Microservices slower than monolith
Mitigation: Performance benchmarking, optimization
Testing: Load testing, latency monitoring
```

### **Business Risks & Mitigation**

**Trading Interruption**
```python
Risk: System downtime during refactoring
Mitigation: Blue-green deployment, parallel systems
Testing: Rollback procedures, data migration validation
```

**Performance Regression**
```python
Risk: New system performs worse
Mitigation: A/B testing, gradual migration
Testing: Performance comparison, profitability tracking
```

**Operational Complexity**
```python
Risk: Microservices harder to operate
Mitigation: Comprehensive monitoring, automation
Testing: Operational runbooks, disaster recovery
```

### **Rollback Procedures**

**Service-Level Rollback**
```bash
# Each service can be rolled back independently
docker-compose stop market-data-gateway
docker-compose up -d market-data-gateway-v1
# Update service discovery to point to old version
```

**System-Level Rollback**
```bash
# Complete system rollback if needed
git checkout previous-stable-tag
./scripts/deploy-rollback.sh
# Restore database from backup if necessary
```

---

## 🎯 **Final Success Criteria**

### **Architecture Quality**
- ✅ Zero circular dependencies between services
- ✅ Each service deployable independently
- ✅ Service communication via well-defined APIs
- ✅ Comprehensive test coverage (>90%)

### **Performance Targets**
- ✅ Profitable bot ratio >60% (vs 7.7% current)
- ✅ Transaction cost reduction >40%
- ✅ System uptime >99.5%
- ✅ API response time <100ms p95

### **Business Value**
- ✅ Risk-adjusted returns (Sharpe ratio >1.5)
- ✅ Portfolio correlation to BTC <0.3
- ✅ Maximum drawdown <10%
- ✅ Ability to rapidly deploy new strategies

---

*This roadmap provides a detailed, week-by-week plan for transforming the monolithic trading system into a high-performance microservices architecture. Follow this plan to achieve institutional-grade trading system performance.*