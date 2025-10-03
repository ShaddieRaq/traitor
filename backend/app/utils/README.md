# Utility Guidelines

## Market Data Access Patterns

### ✅ RECOMMENDED: Use Centralized Utilities

```python
from app.utils.market_data_helper import create_market_data_cache, create_single_market_data

# For multiple pairs (replaces 15+ lines of duplicate code)
market_data_cache = create_market_data_cache(unique_pairs)

# For single pair with consistent fallback
market_data = create_single_market_data("BTC-USD")
```

### ❌ AVOID: Manual Cache Creation

```python
# DON'T DO THIS (duplicated 12+ times across codebase)
market_data_cache = {}
for pair in unique_pairs:
    try:
        market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
    except Exception as e:
        logger.warning(f"Failed to get market data for {pair}: {e}")
        market_data_cache[pair] = pd.DataFrame({
            'close': [100.0], 'high': [101.0], 'low': [99.0], 
            'open': [100.5], 'volume': [1000]
        })
```

## Service Access Patterns

### ✅ RECOMMENDED: Use Singleton Getters

```python
from app.utils.service_registry import get_service_registry

registry = get_service_registry()
market_service = registry.get_market_data_service()  # ✅ Correct singleton
market_cache = registry.get_market_data_cache()      # ✅ Correct singleton

# Or use convenience functions
from app.utils.service_registry import get_market_service, get_market_cache
market_service = get_market_service()  # ✅ Shorthand
```

### ❌ AVOID: Direct Instantiation

```python
# DON'T DO THIS (breaks singleton pattern)
market_service = MarketDataService()  # ❌ Direct instantiation
market_cache = MarketDataCache()      # ❌ Direct instantiation
```

## Migration Guide

### Files with Duplicate Market Data Cache Pattern

**Replace in these files:**
- `backend/app/api/bot_temperatures.py` (2 instances)
- `backend/app/api/websocket.py` (4 instances)  
- `backend/app/api/bots.py` (3 instances)
- `backend/app/services/bot_evaluator.py` (1 instance)

**Before:**
```python
market_data_cache = {}
for pair in unique_pairs:
    try:
        market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
    except Exception as e:
        logger.warning(f"Failed to get market data for {pair}: {e}")
        market_data_cache[pair] = pd.DataFrame({
            'close': [100.0], 'high': [101.0], 'low': [99.0], 
            'open': [100.5], 'volume': [1000]
        })
```

**After:**
```python
from ..utils.market_data_helper import create_market_data_cache

market_data_cache = create_market_data_cache(unique_pairs, granularity=3600, limit=100)
```

### Files with Wrong Service Instantiation

**Fix in these files:**
- `backend/app/services/trading_safety.py:314`
- `backend/app/services/trading_service.py:458`  
- `backend/app/services/raw_trade_service.py:166`
- `backend/app/api/bots.py:387`

**Before:**
```python
market_data_service = MarketDataService()  # ❌ Wrong
```

**After:**
```python
from ..utils.service_registry import get_market_service
market_data_service = get_market_service()  # ✅ Correct
```

## Benefits

### Code Reduction
- **Market data patterns**: ~300 lines → ~20 lines (95% reduction)
- **Service instantiation**: ~50 lines → ~10 lines (80% reduction)
- **Total reduction**: **~350 lines eliminated**

### Quality Improvements
- **Single source of truth**: All market data caching through one utility
- **Consistent caching**: All historical data requests use Redis cache
- **Proper singletons**: All services use singleton pattern correctly
- **Maintainability**: Changes in one place, not 12+ locations

### Performance Benefits
- **Cache efficiency**: All requests go through MarketDataService Redis cache
- **Reduced API calls**: Eliminate bypassing of cached systems
- **Memory efficiency**: Proper singleton usage reduces object creation