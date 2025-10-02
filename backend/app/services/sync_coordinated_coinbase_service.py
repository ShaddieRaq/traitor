"""
Synchronous Coordinated Coinbase Service - Phase 6.4
Wrapper around coinbase_service that adds rate limiting without async complications.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from .sync_api_coordinator import get_sync_coordinator, RequestPriority

logger = logging.getLogger(__name__)


class SyncCoordinatedCoinbaseService:
    """
    Synchronous wrapper around coinbase_service that adds intelligent
    rate limiting and coordination without async/sync deadlock issues.
    """
    
    def __init__(self, coinbase_service):
        self.coinbase_service = coinbase_service
        self.coordinator = get_sync_coordinator(coinbase_service)
        logger.info("🔧 SyncCoordinatedCoinbaseService initialized")
    
    def get_product_ticker(self, product_id: str, priority: RequestPriority = RequestPriority.MEDIUM) -> Optional[Dict[str, Any]]:
        """Get product ticker with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_product_ticker', 
                product_id, 
                priority=priority
            )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated ticker call failed for {product_id}: {e}")
            return None
    
    def get_historical_data(self, product_id: str, granularity: int = 3600, limit: int = 100, 
                          priority: RequestPriority = RequestPriority.MEDIUM) -> pd.DataFrame:
        """Get historical data with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_historical_data',
                product_id,
                granularity,
                limit,
                priority=priority
            )
            return result if result is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ Coordinated historical data call failed for {product_id}: {e}")
            return pd.DataFrame()
    
    def get_accounts(self, priority: RequestPriority = RequestPriority.MEDIUM) -> Optional[List[Dict[str, Any]]]:
        """Get accounts with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_accounts',
                priority=priority
            )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated accounts call failed: {e}")
            return None
    
    def get_products(self, priority: RequestPriority = RequestPriority.MEDIUM) -> Optional[List[Dict[str, Any]]]:
        """Get products with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_products',
                priority=priority
            )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated products call failed: {e}")
            return None
    
    def get_available_balance(self, currency: str, priority: RequestPriority = RequestPriority.HIGH) -> float:
        """Get available balance with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_available_balance',
                currency,
                priority=priority
            )
            return result if result is not None else 0.0
        except Exception as e:
            logger.error(f"❌ Coordinated balance call failed for {currency}: {e}")
            return 0.0
    
    def validate_trade_balance(self, product_id: str, side: str, size_usd: float,
                             current_price: float, priority: RequestPriority = RequestPriority.HIGH) -> Dict[str, Any]:
        """Validate trade balance with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'validate_trade_balance',
                product_id,
                side,
                size_usd,
                current_price,
                priority=priority
            )
            return result if result else {'valid': False, 'reason': 'API call failed'}
        except Exception as e:
            logger.error(f"❌ Coordinated balance validation failed: {e}")
            return {'valid': False, 'reason': f'API error: {e}'}
    
    def place_market_order(self, product_id: str, side: str, amount: float,
                          priority: RequestPriority = RequestPriority.CRITICAL) -> Optional[Dict[str, Any]]:
        """Place market order with highest priority coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'place_market_order',
                product_id,
                side,
                amount,
                priority=priority
            )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated order placement failed: {e}")
            return None
    
    def get_order_status(self, order_id: str, priority: RequestPriority = RequestPriority.HIGH) -> Optional[Dict[str, Any]]:
        """Get order status with rate limiting coordination."""
        try:
            result = self.coordinator.coordinated_call(
                'get_order_status',
                order_id,
                priority=priority
            )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated order status call failed: {e}")
            return None
    
    def get_fills(self, product_id: str = None, priority: RequestPriority = RequestPriority.MEDIUM) -> Optional[List[Dict[str, Any]]]:
        """Get fills with rate limiting coordination."""
        try:
            if product_id:
                result = self.coordinator.coordinated_call(
                    'get_fills',
                    product_id=product_id,
                    priority=priority
                )
            else:
                result = self.coordinator.coordinated_call(
                    'get_fills',
                    priority=priority
                )
            return result
        except Exception as e:
            logger.error(f"❌ Coordinated fills call failed: {e}")
            return None
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination and rate limiting statistics."""
        return self.coordinator.get_stats()
    
    def clear_cache(self):
        """Clear the coordination cache."""
        self.coordinator.clear_cache()
    
    # Pass-through methods that don't need coordination (rare/non-rate-limited calls)
    def __getattr__(self, name):
        """Pass through any other method calls to the original service."""
        if hasattr(self.coinbase_service, name):
            return getattr(self.coinbase_service, name)
        raise AttributeError(f"Neither SyncCoordinatedCoinbaseService nor coinbase_service has attribute '{name}'")


# Global coordinated service instance
_coordinated_service = None


def get_coordinated_coinbase_service():
    """Get the global coordinated coinbase service."""
    global _coordinated_service
    
    if _coordinated_service is None:
        # Import here to avoid circular imports
        from .coinbase_service import coinbase_service
        _coordinated_service = SyncCoordinatedCoinbaseService(coinbase_service)
        logger.info("🚀 Global SyncCoordinatedCoinbaseService created")
    
    return _coordinated_service