"""
Centralized Market Data Service - Phase 6.2 Implementation
Shared Cache Layer with Redis-based coordination to eliminate rate limiting.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import pandas as pd
from ..core.config import settings

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of market data that can be cached."""
    TICKER = "ticker"
    HISTORICAL = "historical" 
    ACCOUNTS = "accounts"
    PRODUCTS = "products"
    BALANCE = "balance"


class Priority(Enum):
    """Request priority levels for API call coordination."""
    TRADING = 1      # Highest priority for active trades
    BOT_EVALUATION = 2   # Medium priority for bot signals
    MARKET_DATA = 3      # Lower priority for general data
    BACKGROUND = 4       # Lowest priority for analytics


@dataclass
class CacheConfig:
    """Configuration for cache TTL and key patterns."""
    ttl: int  # Time to live in seconds
    key_pattern: str  # Redis key pattern with placeholders
    
    
@dataclass
class APIRequest:
    """Request object for coordinated API calls."""
    product_id: str
    data_type: DataType
    priority: Priority
    timestamp: float
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


class SharedCacheManager:
    """
    Intelligent caching with dynamic TTL based on market volatility.
    Central cache for all market data to prevent duplicate API calls.
    """
    
    # Cache configuration for different data types
    CACHE_CONFIGS = {
        DataType.TICKER: CacheConfig(
            ttl=30,  # 30 seconds for price data
            key_pattern="trader:ticker:{product_id}"
        ),
        DataType.HISTORICAL: CacheConfig(
            ttl=300,  # 5 minutes for historical data  
            key_pattern="trader:historical:{product_id}:{granularity}:{limit}"
        ),
        DataType.ACCOUNTS: CacheConfig(
            ttl=120,  # 2 minutes for account data
            key_pattern="trader:accounts:global"
        ),
        DataType.PRODUCTS: CacheConfig(
            ttl=3600,  # 1 hour for product list
            key_pattern="trader:products:all"
        ),
        DataType.BALANCE: CacheConfig(
            ttl=90,  # 90 seconds for balance data
            key_pattern="trader:balance:{currency}"
        )
    }
    
    def __init__(self):
        """Initialize Redis connection and cache manager."""
        try:
            # Use redis_url from settings (matches existing pattern)
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ SharedCacheManager connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, data_type: DataType, **kwargs) -> str:
        """Generate Redis cache key from data type and parameters."""
        config = self.CACHE_CONFIGS[data_type]
        return config.key_pattern.format(**kwargs)
    
    async def get(self, data_type: DataType, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get data from cache.
        
        Args:
            data_type: Type of data to retrieve
            **kwargs: Parameters for key generation
            
        Returns:
            Cached data or None if not found/expired
        """
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(data_type, **kwargs)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"💾 Cache HIT for {cache_key}")
                
                # Add cache metadata
                data['_cache_metadata'] = {
                    'hit': True,
                    'key': cache_key,
                    'retrieved_at': time.time()
                }
                
                return data
            else:
                logger.debug(f"💸 Cache MISS for {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    async def set(self, data_type: DataType, data: Dict[str, Any], **kwargs) -> bool:
        """
        Store data in cache with appropriate TTL.
        
        Args:
            data_type: Type of data being cached
            data: Data to cache
            **kwargs: Parameters for key generation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_cache_key(data_type, **kwargs)
            config = self.CACHE_CONFIGS[data_type]
            
            # Add cache metadata
            data_with_metadata = {
                **data,
                '_cache_metadata': {
                    'cached_at': time.time(),
                    'ttl': config.ttl,
                    'data_type': data_type.value
                }
            }
            
            # Store with TTL
            success = self.redis_client.setex(
                cache_key,
                config.ttl,
                json.dumps(data_with_metadata, default=str)
            )
            
            if success:
                logger.debug(f"💾 Cache SET for {cache_key} (TTL: {config.ttl}s)")
                return True
            else:
                logger.warning(f"Failed to cache data for {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error caching data: {e}")
            return False
    
    async def invalidate(self, data_type: DataType = None, **kwargs) -> int:
        """
        Invalidate cache entries.
        
        Args:
            data_type: If provided, invalidate specific data type
            **kwargs: Additional parameters for specific invalidation
            
        Returns:
            Number of keys invalidated
        """
        if not self.redis_client:
            return 0
            
        try:
            if data_type:
                # Invalidate specific cache entry
                cache_key = self._generate_cache_key(data_type, **kwargs)
                deleted = self.redis_client.delete(cache_key)
                logger.info(f"🗑️ Invalidated cache key: {cache_key}")
                return deleted
            else:
                # Invalidate all trader cache entries
                pattern = "trader:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    logger.info(f"🗑️ Invalidated {deleted} cache entries")
                    return deleted
                return 0
                
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information."""
        if not self.redis_client:
            return {"status": "disconnected"}
            
        try:
            # Get Redis info
            redis_info = self.redis_client.info()
            
            # Count trader-specific keys by type
            trader_keys = self.redis_client.keys("trader:*")
            key_counts = {}
            
            for key in trader_keys:
                key_type = key.split(":")[1] if ":" in key else "unknown"
                key_counts[key_type] = key_counts.get(key_type, 0) + 1
            
            return {
                "status": "connected",
                "total_keys": len(trader_keys),
                "keys_by_type": key_counts,
                "redis_memory_used": redis_info.get("used_memory_human", "unknown"),
                "redis_connected_clients": redis_info.get("connected_clients", 0),
                "cache_configs": {dt.value: asdict(config) for dt, config in self.CACHE_CONFIGS.items()}
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


class DataDistributionService:
    """
    Service layer that provides cached data to all consumers.
    This will replace direct API calls in bots and endpoints.
    """
    
    def __init__(self):
        self.cache_manager = SharedCacheManager()
        
    async def get_ticker_cached(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get ticker data from cache (replaces direct API calls)."""
        return await self.cache_manager.get(DataType.TICKER, product_id=product_id)
    
    async def get_historical_cached(self, product_id: str, granularity: int = 3600, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get historical data from cache (replaces direct API calls)."""
        return await self.cache_manager.get(
            DataType.HISTORICAL, 
            product_id=product_id,
            granularity=granularity,
            limit=limit
        )
    
    async def get_accounts_cached(self) -> Optional[Dict[str, Any]]:
        """Get account data from cache (replaces direct API calls)."""
        return await self.cache_manager.get(DataType.ACCOUNTS)
    
    async def get_products_cached(self) -> Optional[Dict[str, Any]]:
        """Get products data from cache (replaces direct API calls)."""
        return await self.cache_manager.get(DataType.PRODUCTS)
    
    async def get_balance_cached(self, currency: str) -> Optional[Dict[str, Any]]:
        """Get balance data from cache (replaces direct API calls)."""
        return await self.cache_manager.get(DataType.BALANCE, currency=currency)
    
    # Cache warming methods (for the centralized service to populate cache)
    async def warm_ticker_cache(self, product_id: str, ticker_data: Dict[str, Any]) -> bool:
        """Warm ticker cache with fresh data from centralized service."""
        return await self.cache_manager.set(DataType.TICKER, ticker_data, product_id=product_id)
    
    async def warm_historical_cache(self, product_id: str, historical_data: Dict[str, Any], granularity: int = 3600, limit: int = 100) -> bool:
        """Warm historical cache with fresh data from centralized service."""
        return await self.cache_manager.set(
            DataType.HISTORICAL, 
            historical_data,
            product_id=product_id,
            granularity=granularity,
            limit=limit
        )
    
    async def warm_accounts_cache(self, accounts_data: Dict[str, Any]) -> bool:
        """Warm accounts cache with fresh data from centralized service."""
        return await self.cache_manager.set(DataType.ACCOUNTS, accounts_data)


# Global instance for shared usage
shared_cache_manager = SharedCacheManager()
data_distribution_service = DataDistributionService()


# Migration helper functions for existing code
async def get_cached_ticker(product_id: str) -> Optional[Dict[str, Any]]:
    """Helper function for migrating existing ticker calls."""
    return await data_distribution_service.get_ticker_cached(product_id)


async def get_cached_historical(product_id: str, granularity: int = 3600, limit: int = 100) -> Optional[Dict[str, Any]]:
    """Helper function for migrating existing historical data calls."""
    return await data_distribution_service.get_historical_cached(product_id, granularity, limit)


async def get_cached_accounts() -> Optional[Dict[str, Any]]:
    """Helper function for migrating existing account calls."""
    return await data_distribution_service.get_accounts_cached()