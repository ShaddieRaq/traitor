# 🏗️ Coinbase Service Architecture - Complete Overview

**Date**: October 12, 2025

## 📊 **Service Hierarchy (Bottom to Top)**

```
┌─────────────────────────────────────────────────────────┐
│  Level 5: Application Layer                             │
│  - bot_evaluator.py                                      │
│  - trading_tasks.py                                      │
│  - breakout_detector.py ← YOU ARE HERE (WRONG LEVEL!)  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Level 4: Market Data Service (PHASE 7)                 │
│  - MarketDataService (Redis cached, batch fetching)     │
│  - 60s cache TTL, 95%+ hit rate                         │
│  - Eliminates rate limiting                             │
│  ✅ USE THIS FOR BREAKOUT SCANNER!                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Level 3: Coordinated Services (PHASE 6.4)              │
│  - SyncCoordinatedCoinbaseService                       │
│  - Request queuing + priority handling                   │
│  - Thread-safe API coordination                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Level 2: WebSocket Streaming                           │
│  - SimpleCoinbaseWebSocket                              │
│  - Real-time price feeds (zero REST API calls)          │
│  - Sub-second latency                                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Level 1: Base Coinbase Service                         │
│  - coinbase_service.py                                  │
│  - Direct SDK wrapper                                   │
│  - Should ONLY be called through higher levels          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Level 0: Coinbase SDK                                  │
│  - coinbase.rest.RESTClient                             │
│  - Rate limited by Coinbase                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 **Services You Should Use**

### **1. MarketDataService** (✅ RECOMMENDED for Breakout Scanner)
**File**: `/backend/app/services/market_data_service.py`

**Purpose**: Batch fetching + Redis caching for market data

**Global Instance**:
```python
from app.services.market_data_service import get_market_data_service
market_service = get_market_data_service()
```

**Key Methods**:
```python
# Get all products (cached 5 minutes)
products = market_service.get_all_products()
# Returns: List[ProductInfo] with product_id, base_currency, quote_currency, etc.

# Get product ticker (cached 60 seconds)
ticker = market_service.get_product_ticker(product_id)
# Returns: TickerData with price, volume_24h, etc.

# Get product stats (cached 60 seconds)
stats = market_service.get_product_stats(product_id)
# Returns: Dict with price_change_24h, volume_change_24h, etc.

# Refresh all data for multiple products (batch operation)
data = market_service.refresh_all_market_data(product_ids=['BTC-USD', 'ETH-USD', ...])
```

**Benefits**:
- ✅ **Redis caching** - 60s TTL, 95%+ hit rate
- ✅ **Batch fetching** - One API call for all pairs
- ✅ **Zero rate limits** - Proven in production since Phase 7
- ✅ **Statistics tracking** - Monitor cache performance

**Stats API**:
```bash
curl "http://localhost:8000/api/v1/cache/stats" | jq
# Shows: cache_hits, cache_misses, hit_rate, api_calls
```

---

### **2. SimpleCoinbaseWebSocket** (For Real-Time Prices)
**File**: `/backend/app/services/simple_websocket.py`

**Purpose**: Real-time price streaming (eliminates REST API calls)

**Global Instance**:
```python
from app.services.simple_websocket import get_websocket_service
ws_service = get_websocket_service()
```

**Key Methods**:
```python
# Get cached price (instant, no API call)
price_data = ws_service.get_price(product_id)
# Returns: {'price': 65432.10, 'product_id': 'BTC-USD', ...}

# Start streaming (usually auto-started)
ws_service.start_streaming()

# Check status
is_running = ws_service.is_streaming
```

**Benefits**:
- ✅ **Zero REST API calls** for price data
- ✅ **Sub-second updates** via WebSocket
- ✅ **Auto-reconnection** on disconnects
- ✅ **Used by bot_evaluator** for signal calculations

---

### **3. SyncCoordinatedCoinbaseService** (For Trading Operations)
**File**: `/backend/app/services/sync_coordinated_coinbase_service.py`

**Purpose**: Request queuing + priority handling for trading operations

**Global Instance**:
```python
from app.services.sync_coordinated_coinbase_service import get_coordinated_coinbase_service
coordinated_service = get_coordinated_coinbase_service()
```

**Key Methods**:
```python
# Place order with priority queuing
order = coordinated_service.place_order(...)

# Get account balance
balance = coordinated_service.get_account_balance(currency)

# Cancel order
result = coordinated_service.cancel_order(order_id)
```

**Benefits**:
- ✅ **Thread-safe** request coordination
- ✅ **Priority handling** (urgent requests first)
- ✅ **Rate limit aware** queuing

---

## 🔥 **Current Problem: Breakout Scanner**

**What's happening now (BAD)**:
```python
# In breakout_detector.py:
def _fetch_all_products(self):
    # Tries coinbase_service.get_products() ← Hits REST API
    products = self.coinbase_service.get_products()
    
    # Then as FALLBACK, hits API DIRECTLY! ❌
    import requests
    response = requests.get('https://api.coinbase.com/...')  # BYPASSES ALL INFRASTRUCTURE!
```

**Why this is bad**:
1. ❌ Bypasses Redis cache
2. ❌ Bypasses WebSocket streaming  
3. ❌ Bypasses rate limit coordination
4. ❌ Causes the rate limiting you're seeing

---

## ✅ **How to Fix Breakout Scanner**

**Replace current code**:
```python
# OLD (BAD):
from app.services.coinbase_service import coinbase_service
self.coinbase_service = coinbase_service

def _fetch_all_products(self):
    products = self.coinbase_service.get_products()  # ❌ REST API call
    # Fallback to direct API ❌❌
```

**NEW (GOOD)**:
```python
# Use MarketDataService instead
from app.services.market_data_service import get_market_data_service

def __init__(self):
    self.market_data_service = get_market_data_service()

def _fetch_all_products(self) -> List[Dict]:
    """Fetch via MarketDataService (cached)."""
    try:
        # ✅ Uses Redis cache, no rate limits
        products = self.market_data_service.get_all_products()
        
        if products:
            logger.info(f"✅ Retrieved {len(products)} products from cache/API")
            # Convert ProductInfo objects to dicts
            return [p.to_dict() for p in products]
        
        return []
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []

def _get_product_24h_stats(self, product_id: str) -> dict:
    """Get 24h price/volume changes via MarketDataService."""
    try:
        # ✅ Cached 60 seconds
        stats = self.market_data_service.get_product_stats(product_id)
        return stats or {}
    except Exception as e:
        logger.error(f"Error getting stats for {product_id}: {e}")
        return {}
```

---

## 📊 **Service Feature Comparison**

| Feature | Direct API | coinbase_service | WebSocket | MarketDataService |
|---------|-----------|------------------|-----------|-------------------|
| **Rate Limits** | ❌ HIGH | ❌ HIGH | ✅ ZERO | ✅ MINIMAL |
| **Caching** | ❌ No | ❌ No | ✅ Yes | ✅ Redis (60s) |
| **Batch Fetching** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Real-Time Prices** | ❌ No | ❌ No | ✅ Yes | ⚠️ Via cache |
| **Hit Rate** | N/A | N/A | 100% | 95%+ |
| **API Calls/Min** | 25+ | 25+ | 0 | 1-2 |
| **Production Ready** | ❌ No | ⚠️ Limited | ✅ Yes | ✅ Yes |

---

## 🎯 **For Your Breakout Scanner**

**Use MarketDataService because**:
1. ✅ **get_all_products()** - Returns all 663 pairs (cached 5 min)
2. ✅ **Redis cache** - 60s TTL prevents rate limits
3. ✅ **Proven in production** - Zero rate limits since Phase 7
4. ✅ **Easy integration** - Just swap the service

**Code changes needed**:
```python
# In breakout_detector.py __init__:
- from app.services.coinbase_service import coinbase_service
- self.coinbase_service = coinbase_service
+ from app.services.market_data_service import get_market_data_service
+ self.market_data_service = get_market_data_service()

# In _fetch_all_products():
- products = self.coinbase_service.get_products()
- # Remove direct API fallback!
+ products = self.market_data_service.get_all_products()
+ return [p.to_dict() for p in products]
```

---

## 🚀 **Next Steps**

1. **Update breakout_detector.py** to use MarketDataService
2. **Remove direct API fallback** (the `requests.get()` call)
3. **Test scanning** - should see zero rate limits
4. **Monitor cache stats** - `curl http://localhost:8000/api/v1/cache/stats`

**Expected Results After Fix**:
```bash
# Before (BAD):
API Calls: 663 per scan (one per product) ← RATE LIMITED!

# After (GOOD):
API Calls: 1-2 per scan (batch + cache) ← NO RATE LIMITS!
Cache Hit Rate: 95%+
```

---

**Summary**: You have excellent infrastructure! The breakout scanner just needs to **use MarketDataService** instead of hitting the API directly. This will eliminate your rate limiting issues immediately.
