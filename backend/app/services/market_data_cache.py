"""
Market Data Cache Service - Phase 1 Implementation
Provides intelligent caching of market data to reduce Coinbase API calls by 90%+
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)


class MarketDataCache:
    """
    Intelligent cache for market data with time-based invalidation.
    
    Features:
    - Time-based cache expiration (default 30 seconds)
    - LRU eviction for memory management
    - Thread-safe operations
    - Request deduplication
    """
    
    def __init__(self, cache_ttl_seconds: int = 30, max_cache_size: int = 100):
        """
        Initialize the market data cache.
        
        Args:
            cache_ttl_seconds: Time to live for cached data in seconds
            max_cache_size: Maximum number of cache entries (LRU eviction)
        """
        self._cache: OrderedDict[str, Tuple[pd.DataFrame, datetime]] = OrderedDict()
        self._cache_ttl = cache_ttl_seconds
        self._max_cache_size = max_cache_size
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'api_calls_saved': 0
        }
        logger.info(f"MarketDataCache initialized with TTL={cache_ttl_seconds}s, max_size={max_cache_size}")
    
    def get_or_fetch(self, product_id: str, granularity: int, limit: int, fetch_func) -> pd.DataFrame:
        """
        Get market data from cache or fetch if not available/expired.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            granularity: Time interval in seconds
            limit: Number of data points
            fetch_func: Function to call if cache miss (should return pd.DataFrame)
            
        Returns:
            DataFrame with market data
        """
        cache_key = self._generate_cache_key(product_id, granularity, limit)
        now = datetime.utcnow()
        
        with self._lock:
            # Check if we have valid cached data
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                age_seconds = (now - timestamp).total_seconds()
                
                if age_seconds < self._cache_ttl:
                    # Cache hit - move to end for LRU
                    self._cache.move_to_end(cache_key)
                    self._stats['hits'] += 1
                    self._stats['api_calls_saved'] += 1
                    
                    logger.debug(f"Cache HIT for {cache_key} (age: {age_seconds:.1f}s)")
                    return cached_data.copy()  # Return copy to prevent modification
                else:
                    # Expired - remove from cache
                    del self._cache[cache_key]
                    logger.debug(f"Cache EXPIRED for {cache_key} (age: {age_seconds:.1f}s)")
            
            # Cache miss - fetch new data
            self._stats['misses'] += 1
            logger.debug(f"Cache MISS for {cache_key} - fetching from API")
            
            try:
                data = fetch_func()
                
                # Cache the new data
                self._cache[cache_key] = (data.copy(), now)
                
                # Enforce cache size limit (LRU eviction)
                while len(self._cache) > self._max_cache_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats['evictions'] += 1
                    logger.debug(f"Cache EVICTED {oldest_key} (LRU)")
                
                logger.info(f"Cached new data for {cache_key} ({len(data)} rows)")
                return data
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {cache_key}: {e}")
                # Return empty DataFrame on fetch failure
                return pd.DataFrame()
    
    def _generate_cache_key(self, product_id: str, granularity: int, limit: int) -> str:
        """Generate cache key from parameters."""
        return f"{product_id}:{granularity}:{limit}"
    
    def invalidate(self, product_id: Optional[str] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            product_id: If provided, only invalidate entries for this product.
                       If None, invalidate all entries.
                       
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if product_id is None:
                # Invalidate all entries
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Invalidated all {count} cache entries")
                return count
            else:
                # Invalidate entries for specific product
                keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{product_id}:")]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.info(f"Invalidated {len(keys_to_remove)} cache entries for {product_id}")
                return len(keys_to_remove)
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_size': len(self._cache),
                'max_cache_size': self._max_cache_size,
                'cache_ttl_seconds': self._cache_ttl,
                'total_requests': total_requests,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'api_calls_saved': self._stats['api_calls_saved']
            }
    
    def get_cache_info(self) -> Dict:
        """Get detailed cache information for debugging."""
        with self._lock:
            cache_info = {}
            now = datetime.utcnow()
            
            for key, (data, timestamp) in self._cache.items():
                age_seconds = (now - timestamp).total_seconds()
                cache_info[key] = {
                    'timestamp': timestamp.isoformat(),
                    'age_seconds': round(age_seconds, 1),
                    'data_rows': len(data),
                    'expires_in_seconds': round(self._cache_ttl - age_seconds, 1),
                    'is_expired': age_seconds >= self._cache_ttl
                }
            
            return cache_info


# Global cache instance
_global_market_data_cache = MarketDataCache(cache_ttl_seconds=30, max_cache_size=100)


def get_market_data_cache() -> MarketDataCache:
    """Get the global market data cache instance."""
    return _global_market_data_cache
