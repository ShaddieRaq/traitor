"""
Coordinated Coinbase Service - Phase 6.3 Implementation
Synchronous wrapper for coordinated API calls to replace direct coinbase_service usage.
This eliminates rate limiting by routing all API calls through the centralized coordinator.
"""

import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from functools import wraps

from .api_coordinator import (
    coordinated_get_ticker,
    coordinated_get_historical, 
    coordinated_get_accounts,
    coordinated_get_products
)

logger = logging.getLogger(__name__)


def run_async_in_sync(async_func):
    """
    Decorator to run async functions in sync context.
    Uses asyncio.create_task to avoid deadlocks.
    """
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                return asyncio.run(async_func(*args, **kwargs))
            
            # There is a running loop, use thread pool to avoid deadlock
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(async_func(*args, **kwargs))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=10)  # 10 second timeout
                
        except Exception as e:
            logger.error(f"Error in run_async_in_sync: {str(e)}")
            return None
    
    return wrapper


class CoordinatedCoinbaseService:
    """
    Synchronous wrapper for coordinated API calls.
    Drop-in replacement for direct coinbase_service calls.
    """
    
    @run_async_in_sync
    async def get_product_ticker(self, product_id: str) -> Optional[dict]:
        """
        Get ticker data for a product through coordinated API.
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Ticker data dict or None if failed
        """
        try:
            result = await coordinated_get_ticker(product_id)
            if result:
                logger.debug(f"✅ Coordinated ticker data for {product_id}")
                return result
            else:
                logger.warning(f"⚠️ No ticker data returned for {product_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting coordinated ticker for {product_id}: {str(e)}")
            return None
    
    @run_async_in_sync
    async def get_historical_data(self, product_id: str, granularity: int = 3600, limit: int = 100) -> pd.DataFrame:
        """
        Get historical data through coordinated API.
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            granularity: Data granularity in seconds (default: 3600 = 1 hour)
            limit: Maximum number of data points (default: 100)
            
        Returns:
            DataFrame with OHLCV data or empty DataFrame if failed
        """
        try:
            result = await coordinated_get_historical(product_id, granularity, limit)
            if result and isinstance(result, list) and len(result) > 0:
                # Convert to DataFrame matching original format
                df = pd.DataFrame(result)
                
                # Ensure proper column names and data types
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.set_index('timestamp')
                
                # Ensure numeric columns
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.debug(f"✅ Coordinated historical data for {product_id}: {len(df)} rows")
                return df
            else:
                logger.warning(f"⚠️ No historical data returned for {product_id}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ Error getting coordinated historical data for {product_id}: {str(e)}")
            return pd.DataFrame()
    
    @run_async_in_sync  
    async def get_available_balance(self, currency: str) -> float:
        """
        Get available balance for a currency through coordinated API.
        
        Args:
            currency: Currency code (e.g., 'USD', 'BTC')
            
        Returns:
            Available balance as float, 0.0 if error or not found
        """
        try:
            accounts_data = await coordinated_get_accounts()
            if accounts_data and isinstance(accounts_data, list):
                for account in accounts_data:
                    if account.get('currency') == currency:
                        # Handle different possible formats of available_balance
                        balance_data = account.get('available_balance', 0)
                        
                        if isinstance(balance_data, dict):
                            balance = float(balance_data.get('value', 0))
                        elif isinstance(balance_data, (str, int, float)):
                            balance = float(balance_data)
                        else:
                            balance = 0.0
                            
                        logger.debug(f"✅ Coordinated balance for {currency}: {balance}")
                        return balance
                
                logger.warning(f"⚠️ Currency {currency} not found in accounts")
                return 0.0
            else:
                logger.warning(f"⚠️ No accounts data returned")
                return 0.0
        except Exception as e:
            logger.error(f"❌ Error getting coordinated balance for {currency}: {str(e)}")
            return 0.0
    
    def validate_trade_balance(self, product_id: str, side: str, size_usd: float, 
                             current_price: float) -> Dict[str, Any]:
        """
        Validate if sufficient balance exists for a trade.
        Uses coordinated API calls for balance checking.
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            size_usd: Trade size in USD
            current_price: Current price of the asset
            
        Returns:
            Dict with 'valid' (bool), 'message' (str), and 'details' (dict)
        """
        try:
            base_currency, quote_currency = product_id.split('-')
            
            if side.upper() == 'BUY':
                # For buy orders, need sufficient quote currency (usually USD)
                available_balance = self.get_available_balance(quote_currency)
                
                if available_balance >= size_usd:
                    return {
                        'valid': True,
                        'message': f'Sufficient {quote_currency} balance for {side} order',
                        'details': {
                            'required': size_usd,
                            'available': available_balance,
                            'currency': quote_currency
                        }
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'Insufficient {quote_currency} balance: need {size_usd}, have {available_balance}',
                        'details': {
                            'required': size_usd,
                            'available': available_balance,
                            'currency': quote_currency
                        }
                    }
            
            elif side.upper() == 'SELL':
                # For sell orders, need sufficient base currency
                available_balance = self.get_available_balance(base_currency)
                required_amount = size_usd / current_price
                
                if available_balance >= required_amount:
                    return {
                        'valid': True,
                        'message': f'Sufficient {base_currency} balance for {side} order',
                        'details': {
                            'required': required_amount,
                            'available': available_balance,
                            'currency': base_currency,
                            'price': current_price
                        }
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'Insufficient {base_currency} balance: need {required_amount}, have {available_balance}',
                        'details': {
                            'required': required_amount,
                            'available': available_balance,
                            'currency': base_currency,
                            'price': current_price
                        }
                    }
            
            else:
                return {
                    'valid': False,
                    'message': f'Invalid side: {side}. Must be BUY or SELL',
                    'details': {'side': side}
                }
                
        except Exception as e:
            logger.error(f"❌ Error validating trade balance for {product_id} {side}: {str(e)}")
            return {
                'valid': False,
                'message': f'Error validating balance: {str(e)}',
                'details': {'error': str(e)}
            }


# Global instance for coordinated API calls
coordinated_coinbase_service = CoordinatedCoinbaseService()