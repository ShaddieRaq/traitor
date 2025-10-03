"""
Service registry to enforce singleton patterns and prevent direct instantiation.
Replaces inconsistent service creation patterns throughout the codebase.

This module addresses the service instantiation anti-pattern where some files
use proper singleton getters while others use direct class instantiation:

WRONG patterns found in:
- backend/app/services/trading_safety.py:314 - MarketDataService()
- backend/app/services/trading_service.py:458 - MarketDataService()  
- backend/app/services/raw_trade_service.py:166 - MarketDataService()
- backend/app/api/bots.py:387 - MarketDataCache()

CORRECT patterns:
- get_market_data_service() - singleton with proper initialization
- get_market_data_cache() - singleton with proper caching
- get_coordinated_coinbase_service() - singleton with rate limiting

Usage:
    from app.utils.service_registry import get_service_registry
    
    registry = get_service_registry()
    market_service = registry.get_market_data_service()  # ✅ Correct
    # NOT: market_service = MarketDataService()  # ❌ Wrong
"""

from typing import TypeVar, Type, Optional
import logging

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Central registry for all service instances.
    
    Enforces singleton patterns and prevents direct instantiation anti-patterns.
    All services should be accessed through this registry to ensure proper
    initialization, caching, and resource management.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self._initialized = True
    
    def get_market_data_service(self):
        """
        Get singleton MarketDataService instance.
        
        Returns properly initialized MarketDataService with Redis caching.
        Replaces direct MarketDataService() instantiation.
        
        Returns:
            MarketDataService singleton instance
        """
        from ..services.market_data_service import get_market_data_service
        return get_market_data_service()
    
    def get_market_data_cache(self):
        """
        Get singleton MarketDataCache instance.
        
        Returns properly initialized MarketDataCache with thread-safe LRU caching.
        Replaces direct MarketDataCache() instantiation.
        
        Returns:
            MarketDataCache singleton instance
        """ 
        from ..services.market_data_cache import get_market_data_cache
        return get_market_data_cache()
    
    def get_coordinated_coinbase_service(self):
        """
        Get coordinated Coinbase service instance.
        
        Returns properly initialized SyncCoordinatedCoinbaseService with
        rate limiting and API coordination.
        
        Returns:
            SyncCoordinatedCoinbaseService singleton instance
        """
        from ..services.sync_coordinated_coinbase_service import get_coordinated_coinbase_service
        return get_coordinated_coinbase_service()
    
    def get_coinbase_service(self):
        """
        Get legacy CoinbaseService instance.
        
        Note: Prefer get_coordinated_coinbase_service() for new code.
        This method exists for backward compatibility.
        
        Returns:
            CoinbaseService instance
        """
        from ..services.coinbase_service import coinbase_service
        return coinbase_service
    
    def get_websocket_service(self):
        """
        Get WebSocket service instance.
        
        Returns:
            SimpleCoinbaseWebSocket singleton instance
        """
        from ..services.simple_websocket import get_websocket_service
        return get_websocket_service()
    
    def get_price_cache(self):
        """
        Get WebSocket price cache instance.
        
        Returns:
            WebSocketPriceCache singleton instance
        """
        from ..services.websocket_price_cache import get_price_cache
        return get_price_cache()


# Global registry instance - singleton pattern
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """
    Get the global service registry singleton.
    
    Returns:
        ServiceRegistry singleton instance
    """
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
        logger.debug("✅ Service registry initialized")
    return _service_registry


def reset_service_registry():
    """
    Reset the global service registry.
    
    This is primarily for testing purposes to ensure clean state.
    """
    global _service_registry
    _service_registry = None
    logger.debug("🔄 Service registry reset")


# Convenience functions for common service access patterns
def get_market_service():
    """Convenience function to get MarketDataService."""
    return get_service_registry().get_market_data_service()


def get_market_cache():
    """Convenience function to get MarketDataCache."""
    return get_service_registry().get_market_data_cache()


def get_coinbase_service():
    """Convenience function to get coordinated CoinbaseService."""
    return get_service_registry().get_coordinated_coinbase_service()