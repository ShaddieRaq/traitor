# 🚨 API Rate Limiting Fix Plan - WebSocket Implementation (UPDATED)

## Current Problem
```
2025-09-14 10:33:21 - coinbase.RESTClient - ERROR - HTTP Error: 429 Client Error: Too Many Requests 
ERROR:coinbase.RESTClient:HTTP Error: Too Many Requests 
ERROR:app.services.coinbase_service:Error fetching portfolio breakdown: 429 Client Error: Too Many Requests 
```

## Root Cause: "Hot Path API Abuse"
- **Bot Evaluation**: Every 500ms Celery tasks call REST APIs for prices
- **Dashboard Polling**: Every 5 seconds frontend triggers balance/portfolio fetches  
- **Trade Validation**: Every trade attempt calls `get_portfolio_breakdown()`
- **Market Analysis**: Frequent `get_products()` and `get_ticker()` calls

**Result**: Coinbase REST API rate limits exceeded (industry standard: ~10 requests/second)

---

## 🎯 SOLUTION: Direct WebSocket Implementation (Industry Gold Standard)

**DECISION**: Skip caching phase and implement WebSocket portfolio/price streaming directly.
**RATIONALE**: System already has sophisticated WebSocket infrastructure - leverage existing capabilities.

### Phase 1: WebSocket Portfolio Balance Stream (2-3 hours)
**Goal**: Replace `get_portfolio_breakdown()` REST calls with real-time WebSocket portfolio updates

## 📊 IMPLEMENTATION STATUS - PHASE 1 ✅ COMPLETE

### ✅ **WebSocket Portfolio Infrastructure - IMPLEMENTED**
- **CoinbaseService Enhancement**: ✅ Added portfolio data storage and WebSocket user channel support
- **Hybrid get_accounts()**: ✅ Uses WebSocket data when available, REST API as fallback  
- **Portfolio Streaming API**: ✅ `/api/v1/ws/start-portfolio-stream` endpoint operational
- **Status Monitoring**: ✅ `/api/v1/ws/portfolio-stream-status` for real-time monitoring

### ✅ **Current Status**
```bash
# Portfolio streaming started successfully:
curl -X POST "http://localhost:8000/api/v1/ws/start-portfolio-stream"
# Result: ✅ "Portfolio WebSocket streaming started for 8 products"

# Products covered: BTC-USD, ETH-USD, SOL-USD, DOGE-USD, XRP-USD, BONK-USD, MOODENG-USD, AVNT-USD
```

### 🔧 **Next: User Channel Subscription**
**Issue**: WebSocket running but needs explicit user data subscription for portfolio updates.
**Solution**: Enhance WebSocket client to subscribe to Coinbase 'user' channel for real-time balance updates.

---

## Root Cause: "Hot Path API Abuse"
- **Bot Evaluation**: Every 500ms Celery tasks call REST APIs for prices
- **Dashboard Polling**: Every 5 seconds frontend triggers balance/portfolio fetches  
- **Trade Validation**: Every trade attempt calls `get_portfolio_breakdown()`
- **Market Analysis**: Frequent `get_products()` and `get_ticker()` calls

**Result**: Coinbase REST API rate limits exceeded (industry standard: ~10 requests/second)

---

## 🎯 SOLUTION: WebSocket + Caching Hybrid (Industry Gold Standard)

### Phase 1: Immediate Rate Limiting Protection (1-2 hours)
**Goal**: Stop 429 errors immediately with caching layer

#### 1.1 Add Redis Caching to CoinbaseService
```python
# backend/app/services/coinbase_service.py

import redis
import json
from datetime import datetime, timedelta

class CoinbaseService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        # Existing code...
    
    def get_portfolio_breakdown_cached(self, portfolio_uuid: str) -> dict:
        """Get portfolio breakdown with 30-second caching."""
        cache_key = f"portfolio_breakdown:{portfolio_uuid}"
        
        # Try cache first
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fallback to REST API with rate limiting protection
        try:
            breakdown = self.client.get_portfolio_breakdown(portfolio_uuid)
            # Cache for 30 seconds
            self.redis_client.setex(cache_key, 30, json.dumps(breakdown))
            return breakdown
        except Exception as e:
            if "429" in str(e):
                # Return stale cache if available during rate limiting
                stale_cache = self.redis_client.get(f"{cache_key}:stale")
                if stale_cache:
                    logger.warning("Using stale cache due to rate limiting")
                    return json.loads(stale_cache)
            raise
    
    def get_ticker_cached(self, product_id: str) -> dict:
        """Get ticker with 5-second caching."""
        cache_key = f"ticker:{product_id}"
        
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        try:
            ticker = self.client.get_product_ticker(product_id)
            self.redis_client.setex(cache_key, 5, json.dumps(ticker))
            # Keep stale copy for rate limiting fallback
            self.redis_client.setex(f"{cache_key}:stale", 300, json.dumps(ticker))
            return ticker
        except Exception as e:
            if "429" in str(e):
                stale_cache = self.redis_client.get(f"{cache_key}:stale")
                if stale_cache:
                    logger.warning(f"Using stale ticker for {product_id} due to rate limiting")
                    return json.loads(stale_cache)
            raise
```

#### 1.2 Update All Hot Path Calls
Replace direct REST calls with cached versions:
- `get_accounts()` → `get_accounts_cached()` (30s cache)
- Balance validation calls → cached portfolio breakdown
- Bot evaluator price fetching → cached tickers
- Market analysis → cached products list

#### 1.3 Add Rate Limiting Monitoring
```python
# backend/app/services/system_health_service.py

class SystemHealthService:
    def check_api_rate_limiting(self) -> dict:
        """Monitor for 429 errors and cache hit rates."""
        redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
        # Get recent 429 error count
        error_count = redis_client.get("api_429_errors:last_5min") or 0
        
        # Get cache hit rate
        cache_hits = redis_client.get("cache_hits:last_5min") or 0
        cache_misses = redis_client.get("cache_misses:last_5min") or 0
        hit_rate = int(cache_hits) / (int(cache_hits) + int(cache_misses)) if (int(cache_hits) + int(cache_misses)) > 0 else 0
        
        return {
            "status": "healthy" if int(error_count) == 0 else "degraded",
            "429_errors_last_5min": int(error_count),
            "cache_hit_rate": hit_rate,
            "recommendation": "WebSocket migration needed" if hit_rate < 0.8 else "Cache working well"
        }
```

### Phase 2: WebSocket Real-time Data Migration (4-6 hours)
**Goal**: Replace REST API calls with real-time WebSocket streams

#### 2.1 Portfolio Balance WebSocket Stream
```python
# backend/app/services/coinbase_websocket_service.py

class CoinbaseWebSocketService:
    def __init__(self):
        self.portfolio_data = {}
        self.ticker_data = {}
        
    async def start_portfolio_stream(self):
        """Stream real-time portfolio updates."""
        async with websockets.connect("wss://ws-feed.exchange.coinbase.com") as websocket:
            subscribe_message = {
                "type": "subscribe",
                "channels": ["user"],
                "signature": self.generate_signature(),
                "key": settings.COINBASE_API_KEY,
                "timestamp": str(int(time.time()))
            }
            await websocket.send(json.dumps(subscribe_message))
            
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "account":
                    # Update real-time portfolio cache
                    self.update_portfolio_cache(data)
                    
    def update_portfolio_cache(self, account_data: dict):
        """Update Redis cache with real-time portfolio data."""
        cache_key = f"portfolio_realtime:{account_data['currency']}"
        self.redis_client.setex(cache_key, 300, json.dumps(account_data))
```

#### 2.2 Price Ticker WebSocket Stream
```python
async def start_ticker_stream(self, product_ids: List[str]):
    """Stream real-time price updates for all trading pairs."""
    subscribe_message = {
        "type": "subscribe", 
        "channels": [{"name": "ticker", "product_ids": product_ids}]
    }
    
    async for message in websocket:
        data = json.loads(message)
        if data.get("type") == "ticker":
            # Update real-time price cache
            cache_key = f"ticker_realtime:{data['product_id']}"
            self.redis_client.setex(cache_key, 60, json.dumps(data))
```

#### 2.3 Hybrid Fallback Architecture  
```python
def get_portfolio_breakdown_hybrid(self, portfolio_uuid: str) -> dict:
    """Hybrid: WebSocket real-time > Cache > REST fallback."""
    
    # 1. Try real-time WebSocket data (preferred)
    realtime_key = f"portfolio_realtime:{portfolio_uuid}"
    realtime_data = self.redis_client.get(realtime_key)
    if realtime_data:
        return json.loads(realtime_data)
    
    # 2. Try recent cache (acceptable)
    cache_key = f"portfolio_breakdown:{portfolio_uuid}"
    cached_data = self.redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # 3. REST API fallback (rate limited, last resort)
    return self.get_portfolio_breakdown_with_backoff(portfolio_uuid)
```

### Phase 3: System Health Integration (1 hour)
**Goal**: Make 429 errors visible in dashboard System Health panel

#### 3.1 Add market_data Error Tracking
```python
# backend/app/api/system.py

@router.get("/errors")
def get_system_errors():
    """Get system errors including API rate limiting."""
    errors = []
    
    # Check for recent 429 errors
    redis_client = redis.Redis(host='localhost', port=6379, db=1)
    recent_429s = redis_client.get("api_429_errors:last_hour") or 0
    
    if int(recent_429s) > 0:
        errors.append({
            "id": f"rate_limit_{int(time.time())}",
            "error_type": "market_data",
            "message": f"Coinbase API rate limiting active ({recent_429s} errors in last hour). Using cached data.",
            "timestamp": datetime.utcnow().isoformat(),
            "resolved": False
        })
    
    return errors
```

#### 3.2 Frontend Integration
The existing `SystemHealthPanel.tsx` will automatically display these as `📡 market_data` errors with the message explaining the caching fallback.

---

## 📋 Implementation Checklist

### Immediate (1-2 hours)
- [ ] Add Redis caching layer to `CoinbaseService`
- [ ] Replace hot path calls with cached versions
- [ ] Add 429 error monitoring and fallback logic
- [ ] Test cache hit rates and 429 error elimination

### Short-term (4-6 hours)  
- [ ] Implement WebSocket portfolio stream
- [ ] Implement WebSocket ticker stream
- [ ] Create hybrid fallback architecture
- [ ] Comprehensive testing of real-time data accuracy

### Integration (1 hour)
- [ ] Add API rate limiting errors to System Health panel
- [ ] Update frontend to show rate limiting status
- [ ] Add cache performance metrics to dashboard

## Expected Results
- **Immediate**: 429 errors eliminated via intelligent caching
- **Short-term**: True real-time data without REST API dependency  
- **Long-term**: Industry-standard WebSocket + cache architecture
- **User Experience**: Faster, more reliable price/balance data

## Files to Modify
1. `backend/app/services/coinbase_service.py` - Add caching layer
2. `backend/app/services/coinbase_websocket_service.py` - New WebSocket service
3. `backend/app/api/system.py` - Add 429 error tracking
4. `backend/app/core/celery_app.py` - Add WebSocket startup tasks
5. `frontend/src/components/Trading/SystemHealthPanel.tsx` - Already ready for market_data errors

## Risk Mitigation
- **Cache fallback**: Always keep stale cache for rate limiting periods
- **WebSocket reconnection**: Automatic reconnection with exponential backoff
- **Data validation**: Compare WebSocket vs REST accuracy during transition
- **Gradual migration**: Phase 1 (caching) can run independently of Phase 2 (WebSocket)
