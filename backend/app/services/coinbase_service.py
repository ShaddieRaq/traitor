from typing import Optional, List
import pandas as pd
from coinbase.rest import RESTClient
from coinbase.websocket import WSClient
from ..core.config import settings
import logging
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def timeout(duration):
    """Context manager for adding timeout to operations."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {duration} seconds")
    
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    try:
        yield
    finally:
        signal.alarm(0)


class CoinbaseService:
    """Service for interacting with Coinbase Advanced Trade API."""
    
    def __init__(self):
        self.client = None
        self.ws_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Coinbase REST client."""
        try:
            if settings.coinbase_api_key and settings.coinbase_api_secret:
                self.client = RESTClient(
                    api_key=settings.coinbase_api_key,
                    api_secret=settings.coinbase_api_secret
                )
                logger.info("Coinbase client initialized successfully")
            else:
                logger.warning("Coinbase API credentials not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Coinbase client: {e}")
    
    def get_products(self) -> List[dict]:
        """Get available trading products."""
        if not self.client:
            return []
        
        try:
            response = self.client.get_products()
            return response.products if hasattr(response, 'products') else []
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    def get_product_ticker(self, product_id: str) -> Optional[dict]:
        """Get current ticker for a product."""
        if not self.client:
            return None
        
        try:
            response = self.client.get_product(product_id)
            return {
                "product_id": product_id,
                "price": float(response.price),
                "volume_24h": float(response.volume_24h) if hasattr(response, 'volume_24h') else 0
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {product_id}: {e}")
            return None
    
    def get_historical_data(self, product_id: str, granularity: int = 3600, limit: int = 100) -> pd.DataFrame:
        """
        Get historical candlestick data.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            granularity: Candlestick granularity in seconds (3600 = 1 hour)
            limit: Number of candles to fetch
        """
        if not self.client:
            return pd.DataFrame()
        
        try:
            # Note: This is a placeholder - actual implementation depends on Coinbase API
            # You may need to use get_product_candles or similar method
            response = self.client.get_product_candles(
                product_id=product_id,
                granularity=granularity,
                limit=limit
            )
            
            if hasattr(response, 'candles') and response.candles:
                data = []
                for candle in response.candles:
                    data.append({
                        'timestamp': pd.to_datetime(candle.start, unit='s'),
                        'open': float(candle.open),
                        'high': float(candle.high),
                        'low': float(candle.low),
                        'close': float(candle.close),
                        'volume': float(candle.volume)
                    })
                
                df = pd.DataFrame(data)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {product_id}: {e}")
        
        return pd.DataFrame()
    
    def place_market_order(self, product_id: str, side: str, size: float) -> Optional[dict]:
        """
        Place a market order.
        
        Args:
            product_id: Trading pair
            side: "buy" or "sell"
            size: Order size
        """
        if not self.client:
            return None
        
        try:
            if side.lower() == "buy":
                response = self.client.market_order_buy(
                    product_id=product_id,
                    base_size=str(size)
                )
            else:
                response = self.client.market_order_sell(
                    product_id=product_id,
                    base_size=str(size)
                )
            
            return {
                "order_id": response.order_id,
                "product_id": product_id,
                "side": side,
                "size": size,
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Error placing {side} order for {product_id}: {e}")
            return None
    
    def get_accounts(self) -> List[dict]:
        """Get account information using portfolio breakdown (includes USD fiat accounts)."""
        if not self.client:
            logger.warning("Coinbase client not initialized")
            return []
        
        try:
            # Use the same approach as the working application
            # Get portfolios first
            portfolios_response = self.client.get_portfolios()
            if not hasattr(portfolios_response, 'portfolios') or not portfolios_response.portfolios:
                logger.error("No portfolios found")
                return []
            
            # Get the default portfolio UUID
            default_portfolio_uuid = portfolios_response.portfolios[0]['uuid']
            logger.info(f"Using portfolio UUID: {default_portfolio_uuid}")
            
            # Get portfolio breakdown which includes all balances (crypto AND fiat)
            breakdown_response = self.client.get_portfolio_breakdown(default_portfolio_uuid)
            
            accounts = []
            
            if hasattr(breakdown_response, 'breakdown') and hasattr(breakdown_response.breakdown, 'spot_positions'):
                spot_positions = breakdown_response.breakdown.spot_positions
                
                for position in spot_positions:
                    try:
                        asset = getattr(position, 'asset', '')
                        is_cash = getattr(position, 'is_cash', False)
                        total_balance_fiat = float(getattr(position, 'total_balance_fiat', 0))
                        total_balance_crypto = float(getattr(position, 'total_balance_crypto', 0))
                        available_to_trade_crypto = float(getattr(position, 'available_to_trade_crypto', 0))
                        
                        # For cash positions (USD, EUR, etc.), use the fiat balance
                        # For crypto positions, use the crypto balance
                        if is_cash:
                            available_balance = total_balance_fiat
                            hold = 0  # Cash typically doesn't have holds in the same way
                        else:
                            available_balance = available_to_trade_crypto
                            hold = total_balance_crypto - available_to_trade_crypto
                        
                        # Include accounts with balances > 0 OR important currencies
                        if total_balance_fiat > 0 or total_balance_crypto > 0 or asset in ['USD', 'USDC', 'EUR', 'GBP']:
                            accounts.append({
                                "currency": asset,
                                "available_balance": available_balance,
                                "hold": hold,
                                "is_cash": is_cash  # Flag to indicate if this is a fiat account
                            })
                            
                            if asset == 'USD':
                                logger.info(f"Found USD fiat account with balance: ${available_balance}")
                                
                    except Exception as position_error:
                        logger.error(f"Error processing position: {position_error}")
                        continue
            
            logger.info(f"Successfully processed {len(accounts)} accounts from portfolio breakdown")
            return accounts
            
        except Exception as e:
            logger.error(f"Error fetching portfolio breakdown: {e}")
            
            # Fallback to original method if portfolio breakdown fails
            logger.info("Falling back to original get_accounts() method")
            try:
                response = self.client.get_accounts()
                accounts = []
                
                if hasattr(response, 'accounts'):
                    for account in response.accounts:
                        try:
                            available_balance = 0
                            hold = 0
                            
                            if hasattr(account, 'available_balance'):
                                if hasattr(account.available_balance, 'value'):
                                    available_balance = float(account.available_balance.value)
                                elif isinstance(account.available_balance, dict):
                                    available_balance = float(account.available_balance.get('value', 0))
                                elif isinstance(account.available_balance, (str, int, float)):
                                    available_balance = float(account.available_balance)
                            
                            if hasattr(account, 'hold'):
                                if hasattr(account.hold, 'value'):
                                    hold = float(account.hold.value)
                                elif isinstance(account.hold, dict):
                                    hold = float(account.hold.get('value', 0))
                                elif isinstance(account.hold, (str, int, float)):
                                    hold = float(account.hold)
                            
                            if available_balance > 0 or hold > 0 or account.currency in ['USD', 'USDC']:
                                accounts.append({
                                    "currency": account.currency,
                                    "available_balance": available_balance,
                                    "hold": hold
                                })
                            
                        except Exception as account_error:
                            logger.error(f"Error processing fallback account: {account_error}")
                            continue
                
                return accounts
                
            except Exception as fallback_error:
                logger.error(f"Fallback method also failed: {fallback_error}")
                return []


# Global instance
coinbase_service = CoinbaseService()
