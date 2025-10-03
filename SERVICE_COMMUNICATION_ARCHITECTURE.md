# Service Communication Architecture
## Preventing the "How Do Services Talk?" Gap

### **Service Interaction Map**

```
┌─────────────────┐    HTTP/REST     ┌──────────────────┐
│  Market Data    │ ◄─────────────── │ Regime Detection │
│  Gateway        │                  │ Service          │
│  :8001          │                  │ :8002            │
└─────────────────┘                  └──────────────────┘
         ▲                                     │
         │ HTTP/REST                           │ HTTP/REST
         │                                     ▼
┌─────────────────┐                  ┌──────────────────┐
│  Execution      │                  │ Risk Management  │
│  Service        │ ◄────────────────┤ Service          │
│  :8004          │    HTTP/REST     │ :8003            │
└─────────────────┘                  └──────────────────┘
```

### **Communication Patterns**

#### **1. Request/Response (Synchronous)**
```python
# Regime Detection calls Market Data Gateway
async def get_market_regime(symbol: str):
    # Direct HTTP call with timeout
    response = await httpx.get(
        f"http://market-data:8001/api/v1/ohlcv/{symbol}",
        timeout=5.0
    )
    market_data = response.json()
    return calculate_regime(market_data)
```

#### **2. Service Discovery Pattern**
```python
# Service registry (simple config-based for MVP)
SERVICES = {
    "market_data": "http://localhost:8001",
    "regime_detection": "http://localhost:8002", 
    "risk_management": "http://localhost:8003",
    "execution": "http://localhost:8004"
}

class ServiceClient:
    def __init__(self, service_name: str):
        self.base_url = SERVICES[service_name]
        self.client = httpx.AsyncClient(timeout=10.0)
```

#### **3. Circuit Breaker Pattern**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            raise ServiceUnavailableError("Circuit breaker OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise
```

### **Data Flow Architecture**

#### **Trading Decision Flow:**
```
1. Execution Service needs to make trade
   ↓
2. Calls Risk Management: "Can I trade BTC-USD $1000?"
   ↓
3. Risk Management calls Market Data: "Get BTC-USD current price"
   ↓
4. Risk Management calls Regime Detection: "What's current regime?"
   ↓
5. Risk Management calculates position size, returns approval
   ↓
6. Execution Service places trade
```

#### **Service Startup Sequence:**
```bash
# 1. Market Data Gateway (foundation)
docker-compose up market-data

# 2. Wait for health check
curl http://localhost:8001/health

# 3. Regime Detection (depends on market data)
docker-compose up regime-detection

# 4. Risk Management (depends on market data + regime)
docker-compose up risk-management

# 5. Execution (depends on all others)
docker-compose up execution
```

### **Error Handling Strategy**

#### **Service Down Scenarios:**

**Market Data Gateway Down:**
```python
# All services have fallback behavior
class MarketDataClient:
    async def get_price(self, symbol: str):
        try:
            return await self.call_gateway(symbol)
        except ServiceUnavailableError:
            # Fallback to direct Coinbase call
            return await self.call_coinbase_direct(symbol)
```

**Regime Detection Down:**
```python
# Risk Management uses default regime
class RiskManager:
    async def get_regime(self, symbol: str):
        try:
            return await self.regime_client.get_regime(symbol)
        except ServiceUnavailableError:
            return "UNKNOWN"  # Conservative default
```

**Risk Management Down:**
```python
# Execution Service stops trading
class ExecutionService:
    async def can_trade(self, order):
        try:
            return await self.risk_client.approve_trade(order)
        except ServiceUnavailableError:
            return False  # Fail safe - no trading
```

### **Development Environment**

#### **Docker Compose Setup:**
```yaml
version: '3.8'
services:
  market-data:
    build: ./market-data-gateway
    ports: ["8001:8001"]
    environment:
      - REDIS_URL=redis://redis:6379
      - COINBASE_API_URL=https://api.exchange.coinbase.com
    depends_on: [redis]
    
  regime-detection:
    build: ./regime-detection
    ports: ["8002:8002"]
    environment:
      - MARKET_DATA_URL=http://market-data:8001
    depends_on: [market-data]
    
  risk-management:
    build: ./risk-management  
    ports: ["8003:8003"]
    environment:
      - MARKET_DATA_URL=http://market-data:8001
      - REGIME_URL=http://regime-detection:8002
    depends_on: [market-data, regime-detection]
    
  execution:
    build: ./execution
    ports: ["8004:8004"] 
    environment:
      - RISK_URL=http://risk-management:8003
    depends_on: [risk-management]
    
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
```

### **API Contract Definitions**

#### **Market Data Gateway API:**
```python
# GET /api/v1/price/{symbol}
{
  "symbol": "BTC-USD",
  "price": 45000.50,
  "timestamp": "2025-10-03T10:30:00Z",
  "source": "coinbase"
}

# GET /api/v1/ohlcv/{symbol}?periods=60
{
  "symbol": "BTC-USD", 
  "data": [
    {
      "timestamp": "2025-10-03T10:29:00Z",
      "open": 44950.0,
      "high": 45100.0, 
      "low": 44900.0,
      "close": 45000.0,
      "volume": 1500.5
    }
  ]
}
```

#### **Regime Detection API:**
```python
# GET /api/v1/regime/{symbol}
{
  "symbol": "BTC-USD",
  "regime": "TRENDING", 
  "confidence": 0.85,
  "indicators": {
    "adx": 28.5,
    "choppiness": 35.2,
    "volatility": 0.02
  },
  "timestamp": "2025-10-03T10:30:00Z"
}
```

#### **Risk Management API:**
```python
# POST /api/v1/approve-trade
Request:
{
  "symbol": "BTC-USD",
  "side": "buy",
  "amount": 1000,
  "current_portfolio": {...}
}

Response:
{
  "approved": true,
  "max_amount": 800,
  "reason": "Position size reduced due to CHOPPY regime",
  "risk_metrics": {
    "portfolio_var": 0.045,
    "concentration_risk": 0.12
  }
}
```

### **Monitoring & Observability**

#### **Health Check Endpoints:**
```python
# Every service implements
# GET /health
{
  "status": "healthy",
  "dependencies": {
    "market_data": "healthy",
    "redis": "healthy"
  },
  "uptime": 3600,
  "version": "1.0.0"
}
```

#### **Distributed Tracing:**
```python
# Each request gets trace ID
import uuid

class TraceMiddleware:
    async def __call__(self, request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        request.state.trace_id = trace_id
        
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
```

### **Development Workflow**

#### **Local Development:**
```bash
# Start dependencies
docker-compose up redis

# Start services in order (separate terminals)
cd market-data-gateway && uvicorn main:app --port 8001 --reload
cd regime-detection && uvicorn main:app --port 8002 --reload  
cd risk-management && uvicorn main:app --port 8003 --reload
cd execution && uvicorn main:app --port 8004 --reload
```

#### **Testing Service Communication:**
```bash
# Test full flow
curl -X POST http://localhost:8004/api/v1/trade \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USD", "side": "buy", "amount": 1000}'

# Should trigger calls:
# execution -> risk-management -> regime-detection -> market-data
```

This architecture prevents the "services don't know how to talk" problem by defining:
1. **Clear communication patterns** (HTTP + circuit breakers)
2. **Service discovery mechanism** (config-based)
3. **Error handling strategy** (fallbacks + fail-safe)
4. **Development environment** (Docker Compose)
5. **API contracts** (explicit request/response formats)
6. **Monitoring** (health checks + tracing)

No more guessing how services interact.