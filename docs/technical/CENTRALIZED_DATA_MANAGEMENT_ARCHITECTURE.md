# Centralized Data Management Architecture - Phase 6.1 Design

## 🚨 CRITICAL PROBLEM ANALYSIS

**Current Rate Limiting Crisis**: 100+ recent 429 errors from Coinbase API

### Root Cause: Multiple Independent API Callers
1. **Backend FastAPI Process** - Direct API calls for real-time requests
2. **Celery Worker Process** - Bot evaluation tasks (25 bots × 3-4 calls = 75-100 calls/5min)
3. **Celery Beat Process** - Scheduled data fetching tasks
4. **Market Analysis Tasks** - Trend detection and regime analysis
5. **Signal Tracking System** - Performance evaluation calls

### Current API Call Patterns (PROBLEMATIC)

#### 1. Bot Evaluation Process (PRIMARY OFFENDER)
```python
# Current pattern in trading_tasks.py - MULTIPLIES API CALLS
for bot in active_bots:  # 25 bots
    # Each bot makes 3-4 API calls:
    ticker = coinbase_service.get_product_ticker(bot.pair)        # API CALL 1
    historical = coinbase_service.get_historical_data(bot.pair)   # API CALL 2  
    accounts = coinbase_service.get_accounts()                    # API CALL 3
    balance_check = coinbase_service.validate_trade_balance()     # API CALL 4
```
**Result**: 25 bots × 4 calls = **100 API calls every 5 minutes** = **1,200 calls/hour**

#### 2. Market Data Tasks (SECONDARY OFFENDER)
```python
# Current pattern in data_tasks.py
fetch_market_data_task(product_ids=["BTC-USD", "ETH-USD", ...])  # 25 products
# Each product requires separate API calls
```

#### 3. Real-time API Endpoints (TERTIARY OFFENDER)
```python
# Current pattern in market.py
@router.get("/ticker/{product_id}")
def get_ticker(product_id: str):
    ticker = coinbase_service.get_product_ticker(product_id)  # DIRECT API CALL
```

## 🏗️ CENTRALIZED DATA SERVICE ARCHITECTURE

### Core Principle: **SINGLE API CALLER**
All Coinbase API calls flow through ONE centralized service that coordinates, caches, and distributes data.

### Architecture Components

#### 1. Centralized Market Data Service (CMDS)
```python
class CentralizedMarketDataService:
    """Single source for ALL Coinbase API calls with intelligent coordination."""
    
    def __init__(self):
        self.redis_client = Redis()
        self.coinbase_client = CoinbaseAdvancedTradeAPI()
        self.request_queue = PriorityQueue()
        self.rate_limiter = CentralizedRateLimiter()
        self.cache_manager = SharedCacheManager()
    
    async def get_market_data(self, product_id: str, data_type: str) -> dict:
        """Single entry point for all market data requests."""
        # Check cache first
        cached_data = await self.cache_manager.get(product_id, data_type)
        if cached_data:
            return cached_data
        
        # Queue API request with priority
        request = MarketDataRequest(product_id, data_type, priority=1)
        await self.request_queue.put(request)
        
        # Return from cache after processing
        return await self.cache_manager.get(product_id, data_type)
```

#### 2. Shared Cache Layer (Redis-based)
```python
class SharedCacheManager:
    """Intelligent caching with dynamic TTL based on market volatility."""
    
    CACHE_SCHEMA = {
        "ticker": {
            "ttl": 30,  # 30 seconds for price data
            "key_pattern": "ticker:{product_id}"
        },
        "historical": {
            "ttl": 300,  # 5 minutes for historical data
            "key_pattern": "historical:{product_id}:{granularity}:{limit}"
        },
        "accounts": {
            "ttl": 120,  # 2 minutes for account data
            "key_pattern": "accounts:global"
        },
        "products": {
            "ttl": 3600,  # 1 hour for product list
            "key_pattern": "products:all"
        }
    }
```

#### 3. API Call Coordinator with Priority Queue
```python
class CentralizedRateLimiter:
    """Global rate limiter with priority queuing."""
    
    PRIORITY_LEVELS = {
        "TRADING": 1,           # Highest priority for active trades
        "BOT_EVALUATION": 2,    # Medium priority for bot signals
        "MARKET_DATA": 3,       # Lower priority for general data
        "BACKGROUND": 4         # Lowest priority for analytics
    }
    
    MAX_CALLS_PER_MINUTE = 10  # Conservative limit
    
    async def execute_request(self, request: APIRequest) -> dict:
        """Execute API request with global coordination."""
        await self.wait_for_rate_limit()
        
        try:
            result = await self.coinbase_client.call(request)
            await self.cache_manager.store(request, result)
            return result
        except RateLimitError:
            # Circuit breaker logic
            await self.handle_rate_limit_exceeded()
```

#### 4. Data Distribution Layer
```python
class DataDistributionService:
    """Distributes cached data to all consumers."""
    
    async def get_ticker(self, product_id: str) -> dict:
        """Get ticker data for bots/APIs."""
        return await self.cmds.get_market_data(product_id, "ticker")
    
    async def get_historical_data(self, product_id: str, **kwargs) -> pd.DataFrame:
        """Get historical data for bots/APIs."""
        return await self.cmds.get_market_data(product_id, "historical")
    
    async def get_accounts(self) -> List[dict]:
        """Get account data for bots/APIs."""
        return await self.cmds.get_market_data("global", "accounts")
```

### Migration Strategy: Zero-Downtime Transition

#### Phase 6.2: Implement Shared Cache Layer
1. **Add Redis cache to existing CoinbaseService**
```python
# Modify existing coinbase_service.py
class CoinbaseService:
    def get_product_ticker(self, product_id: str) -> dict:
        # Check shared cache first
        cached = self.shared_cache.get(f"ticker:{product_id}")
        if cached:
            return cached
        
        # Fallback to current logic
        return self._existing_get_ticker_logic(product_id)
```

#### Phase 6.3: Centralize API Calls
1. **Create CentralizedMarketDataService**
2. **Route all API calls through CMDS**
3. **Maintain backward compatibility**

#### Phase 6.4: Remove Individual API Calls
1. **Update BotSignalEvaluator to use CMDS**
```python
class BotSignalEvaluator:
    def __init__(self):
        self.data_service = DataDistributionService()  # NO DIRECT API CALLS
    
    async def evaluate_bot(self, bot: Bot) -> dict:
        # Get all data from shared cache
        ticker = await self.data_service.get_ticker(bot.pair)
        historical = await self.data_service.get_historical_data(bot.pair)
        accounts = await self.data_service.get_accounts()
        
        # Process signals (no API calls)
        return self.calculate_signals(ticker, historical, accounts)
```

#### Phase 6.5: Intelligent Refresh Logic
```python
class IntelligentRefreshManager:
    """Dynamic refresh rates based on market conditions."""
    
    def calculate_refresh_rate(self, product_id: str) -> int:
        volatility = self.get_volatility_score(product_id)
        trading_volume = self.get_volume_score(product_id)
        
        # Higher volatility = faster refresh
        if volatility > 0.8:
            return 15  # 15 seconds for highly volatile pairs
        elif volatility > 0.5:
            return 30  # 30 seconds for moderate volatility
        else:
            return 60  # 60 seconds for stable pairs
```

## 📊 Expected Performance Improvements

### Current State (BROKEN)
- **API Calls**: 1,200+ calls/hour
- **Rate Limit Errors**: 100+ recent 429 errors
- **Cache Hit Rate**: ~78% (still failing)

### Target State (FIXED)
- **API Calls**: <50 calls/hour (96% reduction)
- **Rate Limit Errors**: 0 (zero tolerance)
- **Cache Hit Rate**: >95% (shared cache)
- **Response Time**: <100ms (cache-first)

## 🛠️ Implementation Plan

### Phase 6.2: Shared Cache Layer (Week 1)
- [ ] Implement SharedCacheManager with Redis
- [ ] Add cache-first logic to existing CoinbaseService
- [ ] Test with 5 bots to validate cache performance

### Phase 6.3: Centralized API Coordinator (Week 2) 
- [ ] Create CentralizedMarketDataService
- [ ] Implement priority queue and rate limiter
- [ ] Route 50% of API calls through CMDS

### Phase 6.4: Bot Migration (Week 3)
- [ ] Update BotSignalEvaluator to use DataDistributionService
- [ ] Migrate all Celery tasks to shared cache
- [ ] Remove direct API calls from bot evaluation

### Phase 6.5: Complete Migration (Week 4)
- [ ] Migrate all FastAPI endpoints to shared cache
- [ ] Implement intelligent refresh logic
- [ ] Monitor and validate zero rate limiting

## 🔧 Technical Implementation Details

### Redis Cache Schema
```redis
# Ticker data (TTL: 30s)
SET ticker:BTC-USD '{"price": 43250.50, "volume": 1250, "timestamp": 1696000000}'

# Historical data (TTL: 300s)  
SET historical:BTC-USD:3600:100 '[{candle_data}, ...]'

# Account data (TTL: 120s)
SET accounts:global '[{account_data}, ...]'

# Product list (TTL: 3600s)
SET products:all '[{product_data}, ...]'
```

### API Request Coordination
```python
# Priority queue for coordinated API calls
request_queue = [
    APIRequest("BTC-USD", "ticker", priority=1, timestamp=now()),
    APIRequest("ETH-USD", "historical", priority=2, timestamp=now()),
    APIRequest("global", "accounts", priority=3, timestamp=now())
]

# Process queue with rate limiting
async def process_api_queue():
    while True:
        request = await queue.get_highest_priority()
        await rate_limiter.execute_request(request)
        await asyncio.sleep(6)  # Guarantee <10 calls/minute
```

## 🎯 Success Metrics

1. **Zero Rate Limiting**: 0 × 429 errors (down from 100+)
2. **API Call Reduction**: <50 calls/hour (down from 1,200+)
3. **Response Performance**: <100ms average (cache-first)
4. **System Reliability**: 99.9% uptime (no API-related outages)
5. **Bot Performance**: All 25 bots operational without API conflicts

## 🚨 Critical Success Factors

1. **Gradual Migration**: No "big bang" deployment - phase by phase
2. **Cache-First Architecture**: Cache becomes the primary data source
3. **Global Coordination**: Single rate limiter for entire system
4. **Priority-Based Queuing**: Critical trades get highest priority
5. **Monitoring & Alerting**: Real-time tracking of API usage

---

**Status**: Phase 6.1 Design Complete ✅  
**Next**: Begin Phase 6.2 Implementation  
**Goal**: Zero tolerance for rate limiting errors