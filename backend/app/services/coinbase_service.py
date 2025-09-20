from typing import Optional, List, Callable, Dict, Any
import pandas as pd
import json
import math
from threading import Thread
from coinbase.rest import RESTClient
from coinbase.websocket import WSClient
from ..core.config import settings
import logging
import signal
from contextlib import contextmanager
from .market_data_cache import get_market_data_cache

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
    """Service for interacting with Coinbase Advanced Trade API with WebSocket support."""
    
    def __init__(self):
        self.client = None
        self.ws_client = None
        self.ws_thread = None
        self.is_ws_running = False
        self.message_handlers: Dict[str, List[Callable]] = {
            'ticker': [],
            'level2': [],
            'heartbeat': []
        }
        # Account data caching to reduce rate limiting
        self.cached_accounts = None
        self.cached_accounts_timestamp = None
        
        # Initialize market data cache
        self.market_data_cache = get_market_data_cache()
        
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
    
    def _initialize_websocket(self):
        """Initialize Coinbase WebSocket client."""
        try:
            if settings.coinbase_api_key and settings.coinbase_api_secret:
                self.ws_client = WSClient(
                    api_key=settings.coinbase_api_key,
                    api_secret=settings.coinbase_api_secret,
                    on_message=self._handle_ws_message
                )
                logger.info("Coinbase WebSocket client initialized successfully")
                return True
            else:
                logger.warning("Coinbase API credentials not provided for WebSocket")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Coinbase WebSocket client: {e}")
            return False
    
    def _handle_ws_message(self, message):
        """Handle incoming WebSocket messages and trigger bot evaluations."""
        try:
            logger.info(f"📥 Received WebSocket message: {type(message)}")
            
            # Log the raw message for debugging (safely)
            if isinstance(message, str):
                try:
                    msg_preview = message[:200] if len(message) > 200 else message
                    logger.info(f"📨 Raw message preview: {msg_preview}")
                except Exception as e:
                    logger.info(f"📨 Raw message length: {len(message)} chars")
                message = json.loads(message)
            
            if isinstance(message, dict):
                logger.info(f"📋 Message keys: {list(message.keys())}")
            
            channel = message.get('channel', '') if isinstance(message, dict) else ''
            logger.info(f"📡 Message channel: '{channel}'")
            
            # Route message to appropriate handlers
            if channel in self.message_handlers:
                for handler in self.message_handlers[channel]:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler for {channel}: {e}")
            
            # Handle ticker updates for bot evaluation
            if channel == 'ticker':
                logger.info(f"📊 Processing ticker message")
                events = message.get('events', [])
                for event in events:
                    tickers = event.get('tickers', [])
                    for ticker in tickers:
                        product_id = ticker.get('product_id')
                        price = ticker.get('price')
                        if product_id and price:
                            logger.info(f"📈 Ticker update: {product_id} @ ${price}")
                            # Trigger bot evaluation for this product
                            self._trigger_bot_evaluations(product_id, ticker)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    def _trigger_bot_evaluations(self, product_id: str, ticker_data: dict):
        """Trigger bot evaluations for a specific product on ticker updates."""
        try:
            logger.info(f"🤖 Triggering bot evaluations for {product_id}")
            
            # Import here to avoid circular imports
            from ..services.streaming_bot_evaluator import StreamingBotEvaluator
            from ..core.database import SessionLocal
            
            # Create database session
            db = SessionLocal()
            try:
                evaluator = StreamingBotEvaluator(db)
                evaluator.evaluate_bots_on_ticker_update(product_id, ticker_data)
                logger.info(f"✅ Bot evaluations completed for {product_id}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error triggering bot evaluations for {product_id}: {e}")
    
    def add_message_handler(self, channel: str, handler: Callable):
        """Add a handler function for WebSocket messages from a specific channel."""
        if channel not in self.message_handlers:
            self.message_handlers[channel] = []
        self.message_handlers[channel].append(handler)
        logger.info(f"Added message handler for {channel} channel")
    
    def remove_message_handler(self, channel: str, handler: Callable):
        """Remove a handler function for WebSocket messages."""
        if channel in self.message_handlers and handler in self.message_handlers[channel]:
            self.message_handlers[channel].remove(handler)
            logger.info(f"Removed message handler for {channel} channel")
    
    def start_websocket(self, product_ids: List[str], channels: List[str] = None):
        """Start WebSocket connection for specified products and channels."""
        if channels is None:
            channels = ['ticker']  # Default to ticker updates
            
        if self.is_ws_running:
            logger.warning("WebSocket is already running")
            return False
            
        if not self._initialize_websocket():
            logger.error("Failed to initialize WebSocket client")
            return False
        
        try:
            def ws_run():
                try:
                    logger.info(f"🔌 Opening WebSocket connection...")
                    self.ws_client.open()
                    logger.info("✅ WebSocket connection opened")
                    
                    logger.info(f"🎯 Starting ticker subscription for {product_ids}")
                    # Subscribe to all products at once instead of individually
                    self.ws_client.ticker(product_ids)
                    logger.info(f"✅ Subscribed to ticker for all products: {product_ids}")
                    
                    logger.info("🔄 Starting WebSocket message loop...")
                    self.ws_client.run_forever_with_exception_check()
                    logger.info("🛑 WebSocket message loop ended")
                    
                except Exception as e:
                    logger.error(f"❌ WebSocket error: {e}")
                    import traceback
                    logger.error(f"📜 WebSocket traceback: {traceback.format_exc()}")
                    self.is_ws_running = False
                finally:
                    logger.info("🧹 WebSocket thread cleanup")
            
            self.ws_thread = Thread(target=ws_run, daemon=True)
            self.ws_thread.start()
            self.is_ws_running = True
            logger.info("WebSocket thread started successfully")
            
            # Give the connection a moment to establish
            import time
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")
            return False
    
    def start_portfolio_streaming(self, product_ids: List[str] = None):
        """Start WebSocket connection with portfolio/user data streaming."""
        if product_ids is None:
            product_ids = ["BTC-USD", "ETH-USD"]  # Default products
            
        # Start regular WebSocket for tickers + user data
        channels = ['ticker', 'user']
        return self.start_websocket(product_ids, channels)
    
    def stop_websocket(self):
        """Stop WebSocket connection."""
        if not self.is_ws_running:
            logger.info("WebSocket is not running")
            return
            
        try:
            self.is_ws_running = False
            if self.ws_client:
                self.ws_client.close()
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=5)
            logger.info("WebSocket stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping WebSocket: {e}")
    
    def get_websocket_status(self) -> Dict[str, Any]:
        """Get current WebSocket connection status."""
        return {
            "is_running": self.is_ws_running,
            "thread_alive": self.ws_thread.is_alive() if self.ws_thread else False,
            "client_initialized": self.ws_client is not None,
            "handler_count": {channel: len(handlers) for channel, handlers in self.message_handlers.items()}
        }
    
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
        """Get current ticker for a product. Uses WebSocket cache first, REST API as fallback."""
        # Try WebSocket cache first (instant, no rate limits)
        try:
            from .simple_websocket import get_websocket_service
            ws_service = get_websocket_service()
            cached_price = ws_service.get_price(product_id)
            
            if cached_price:
                logger.debug(f"✅ Using WebSocket price for {product_id}: ${cached_price['price']}")
                return cached_price
        except Exception as e:
            logger.warning(f"WebSocket price error for {product_id}: {e}")
        
        # Fallback to REST API (rate limited)
        if not self.client:
            return None
        
        try:
            logger.warning(f"⚠️ WebSocket cache miss, using REST API for {product_id}")
            response = self.client.get_product(product_id)
            return {
                "product_id": product_id,
                "price": float(response.price),
                "volume_24h": float(response.volume_24h) if hasattr(response, 'volume_24h') else 0,
                "data_source": "rest_api"
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {product_id}: {e}")
            return None
    
    def get_historical_data(self, product_id: str, granularity: int = 3600, limit: int = 100) -> pd.DataFrame:
        """
        Get historical candlestick data with intelligent caching.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            granularity: Candlestick granularity in seconds (3600 = 1 hour)
            limit: Number of candles to fetch
        """
        if not self.client:
            return pd.DataFrame()
        
        # Use cache to get data, falling back to API if needed
        def fetch_from_api():
            return self._fetch_historical_data_from_api(product_id, granularity, limit)
        
        return self.market_data_cache.get_or_fetch(product_id, granularity, limit, fetch_from_api)
    
    def _fetch_historical_data_from_api(self, product_id: str, granularity: int, limit: int) -> pd.DataFrame:
        """
        Internal method to fetch data directly from Coinbase API.
        This method should only be called by the cache system.
        """
        logger.info(f"🌐 Making API call for {product_id} (granularity={granularity}, limit={limit})")
        
        try:
            import time
            
            # Calculate start and end times as Unix timestamps
            end_timestamp = int(time.time())
            start_timestamp = end_timestamp - (granularity * limit)
            
            # Convert granularity to string format expected by API
            granularity_map = {
                60: "ONE_MINUTE",
                300: "FIVE_MINUTE", 
                900: "FIFTEEN_MINUTE",
                3600: "ONE_HOUR",
                21600: "SIX_HOUR",
                86400: "ONE_DAY"
            }
            
            granularity_str = granularity_map.get(granularity, "ONE_HOUR")
            
            # Use the correct Coinbase API method for getting candlestick data
            response = self.client.get_public_candles(
                product_id=product_id,
                start=str(start_timestamp),
                end=str(end_timestamp),
                granularity=granularity_str,
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
                logger.info(f"✅ Successfully fetched {len(df)} candles for {product_id}")
                return df
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching historical data for {product_id}: {e}")
            
            # Check for rate limiting errors and report to system health
            if "429" in error_msg or "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
                logger.error(f"🚨 Rate limiting detected for {product_id}: {error_msg}")
                # Report to system health monitor
                try:
                    from ..api.system_errors import report_bot_error, ErrorType
                    report_bot_error(
                        error_type=ErrorType.MARKET_DATA,
                        message=f"Rate limiting error fetching {product_id} data: {error_msg}",
                        details={"product_id": product_id, "error_type": "rate_limit_429"}
                    )
                except Exception as report_error:
                    logger.error(f"Failed to report rate limiting error: {report_error}")
        
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
            import uuid
            import time
            client_order_id = str(uuid.uuid4())
            
            # Get product info to determine proper decimal precision
            try:
                products = self.get_products()
                product_info = None
                
                # Find the specific product
                for product in products:
                    # Handle different response formats
                    if hasattr(product, 'product_id'):
                        if product.product_id == product_id:
                            product_info = product
                            break
                    elif isinstance(product, dict) and product.get('product_id') == product_id:
                        product_info = product
                        break
                
                # Round size to proper decimal places based on base_increment
                rounded_size = size
                if product_info:
                    # Get base_increment from the product
                    if hasattr(product_info, 'base_increment'):
                        base_increment = float(product_info.base_increment)
                    elif isinstance(product_info, dict) and 'base_increment' in product_info:
                        base_increment = float(product_info['base_increment'])
                    else:
                        base_increment = None
                    
                    if base_increment and base_increment > 0:
                        # Calculate decimal places from base_increment (e.g., 0.000001 = 6 decimals)
                        decimal_places = max(0, -int(round(math.log10(base_increment))))
                        rounded_size = round(size, decimal_places)
                        logger.info(f"🔧 Size precision: {size} → {rounded_size} ({decimal_places} decimals, base_increment: {base_increment})")
                    else:
                        logger.warning(f"⚠️ No base_increment found for {product_id}, using original size")
                else:
                    logger.warning(f"⚠️ Could not find product info for {product_id}, using original size")
            except Exception as e:
                logger.error(f"❌ Error getting product precision for {product_id}: {e}")
                rounded_size = size
            
            # REAL TRADE EXECUTION
            logger.info(f"💰 EXECUTING REAL TRADE: {side} {rounded_size} {product_id}")
            
            # Real Coinbase order execution
            if side.lower() == "buy":
                response = self.client.market_order_buy(
                    product_id=product_id,
                    base_size=str(rounded_size),
                    client_order_id=client_order_id
                )
            else:
                response = self.client.market_order_sell(
                    product_id=product_id,
                    base_size=str(rounded_size),
                    client_order_id=client_order_id
                )
            
            # Extract order ID from response - debug the structure
            logger.info(f"🔍 Coinbase API Response Type: {type(response)}")
            logger.info(f"🔍 Response success: {getattr(response, 'success', None)}")
            logger.info(f"🔍 Response success_response: {getattr(response, 'success_response', None)}")
            
            # Check for Coinbase API errors and make them OBVIOUS
            if hasattr(response, 'success') and not response.success:
                error_response = getattr(response, 'error_response', None)
                logger.error(f"🚨 COINBASE REJECTED ORDER: {product_id} {side} {rounded_size}")
                logger.error(f"🚨 REJECTION REASON: {error_response}")
                
                # Try to extract specific error details
                if error_response:
                    if hasattr(error_response, 'message'):
                        logger.error(f"🚨 ERROR MESSAGE: {error_response.message}")
                    if hasattr(error_response, 'error_details'):
                        logger.error(f"🚨 ERROR DETAILS: {error_response.error_details}")
                    if hasattr(error_response, 'failure_reason'):
                        logger.error(f"🚨 FAILURE REASON: {error_response.failure_reason}")
                    
                    # Log the full error response structure
                    logger.error(f"🚨 FULL ERROR RESPONSE: {str(error_response)}")
                
                # Return None to indicate failure
                return None
            
            order_id = None
            if hasattr(response, 'success') and response.success and hasattr(response, 'success_response'):
                success_resp = response.success_response
                logger.info(f"✅ Trade successful! Response type: {type(success_resp)}")
                logger.info(f"✅ Success response content: {success_resp}")
                
                # The response is a dictionary, so access order_id as a key
                if isinstance(success_resp, dict) and 'order_id' in success_resp:
                    order_id = success_resp['order_id']
                elif hasattr(success_resp, 'order_id'):
                    order_id = success_resp.order_id
                elif hasattr(success_resp, 'id'):
                    order_id = success_resp.id
                elif hasattr(success_resp, 'order') and hasattr(success_resp.order, 'order_id'):
                    order_id = success_resp.order.order_id
            
            logger.info(f"✅ Extracted order_id: {order_id}")
            
            return {
                "order_id": order_id,
                "client_order_id": client_order_id,
                "product_id": product_id,
                "side": side,
                "size": size,
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"🚨 EXCEPTION DURING {side} ORDER FOR {product_id}: {str(e)}")
            logger.error(f"🚨 EXCEPTION TYPE: {type(e).__name__}")
            logger.error(f"🚨 FULL EXCEPTION: {repr(e)}")
            import traceback
            logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
            return None

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a specific order.
        
        Args:
            order_id: The order ID to check
            
        Returns:
            Dict with order status information or None if not found
        """
        if not self.client or not order_id:
            return None
            
        try:
            # Get the order from Coinbase
            response = self.client.get_order(order_id)
            
            if response and hasattr(response, 'order'):
                order = response.order
                return {
                    "order_id": getattr(order, 'order_id', order_id),
                    "status": getattr(order, 'status', 'unknown'),
                    "filled_size": float(getattr(order, 'filled_size', 0)),
                    "remaining_size": float(getattr(order, 'remaining_size', 0)),
                    "average_filled_price": float(getattr(order, 'average_filled_price', 0)),
                    "product_id": getattr(order, 'product_id', ''),
                    "side": getattr(order, 'side', ''),
                    "created_time": getattr(order, 'created_time', None),
                    "completion_percentage": getattr(order, 'completion_percentage', '0')
                }
            else:
                logger.warning(f"No order found for ID: {order_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking order status for {order_id}: {e}")
            return None
    
    def get_accounts(self) -> List[dict]:
        """Get account information using portfolio breakdown (includes USD fiat accounts)."""
        if not self.client:
            logger.warning("Coinbase client not initialized")
            return []
        
        # Check if we have fresh cached data (within 60 seconds to reduce rate limiting)
        from datetime import datetime
        if (self.cached_accounts and self.cached_accounts_timestamp and 
            (datetime.utcnow() - self.cached_accounts_timestamp).total_seconds() < 60):
            cache_age = (datetime.utcnow() - self.cached_accounts_timestamp).total_seconds()
            logger.info(f"💾 Using cached account data (age: {cache_age:.1f}s) - avoiding REST API call")
            return self.cached_accounts
        
        # Make REST API call (with rate limiting risk)
        logger.warning("⚠️ Making REST API call for account data - potential rate limiting risk")
        
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
            
            # Cache the results to reduce future API calls
            self.cached_accounts = accounts
            self.cached_accounts_timestamp = datetime.utcnow()
            
            return accounts
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching portfolio breakdown: {e}")
            
            # Check for rate limiting errors and report to system health
            if "429" in error_msg or "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
                logger.error(f"🚨 Rate limiting detected in portfolio breakdown: {error_msg}")
                try:
                    from ..api.system_errors import report_bot_error, ErrorType
                    report_bot_error(
                        error_type=ErrorType.MARKET_DATA,
                        message=f"Rate limiting error in portfolio breakdown: {error_msg}",
                        details={"error_type": "rate_limit_429", "operation": "portfolio_breakdown"}
                    )
                except Exception as report_error:
                    logger.error(f"Failed to report rate limiting error: {report_error}")
            
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
                
                # Cache the fallback results too
                self.cached_accounts = accounts
                self.cached_accounts_timestamp = datetime.utcnow()
                
                return accounts
                
            except Exception as fallback_error:
                error_msg = str(fallback_error)
                logger.error(f"Fallback method also failed: {fallback_error}")
                
                # Check for rate limiting errors and report to system health
                if "429" in error_msg or "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
                    logger.error(f"🚨 Rate limiting detected in account data fetch: {error_msg}")
                    try:
                        from ..api.system_errors import report_bot_error, ErrorType
                        report_bot_error(
                            error_type=ErrorType.MARKET_DATA,
                            message=f"Rate limiting error fetching account data: {error_msg}",
                            details={"error_type": "rate_limit_429", "operation": "get_accounts"}
                        )
                    except Exception as report_error:
                        logger.error(f"Failed to report rate limiting error: {report_error}")
                
                return []
    
    def get_transaction_summary(self, start_date: str = None, end_date: str = None, user_native_currency: str = "USD") -> Optional[Dict[str, Any]]:
        """
        Get transaction summary including deposits, withdrawals, and other transactions.
        
        Args:
            start_date: Start date in ISO format (e.g., "2024-01-01T00:00:00Z")
            end_date: End date in ISO format (e.g., "2024-12-31T23:59:59Z")  
            user_native_currency: Native currency for summary (default USD)
            
        Returns:
            Transaction summary with deposits, withdrawals, and other transaction data
        """
        try:
            logger.info(f"Getting transaction summary from {start_date} to {end_date}")
            
            # Call Coinbase API using the correct method - start with basic call
            if start_date and end_date:
                response = self.client.get_transaction_summary(
                    start_date=start_date,
                    end_date=end_date,
                    user_native_currency=user_native_currency
                )
            else:
                # Try basic call without date parameters
                response = self.client.get_transaction_summary()
            
            if response and hasattr(response, 'transaction_summary'):
                logger.info("Successfully retrieved transaction summary")
                return response.transaction_summary
            else:
                logger.warning("Transaction summary response was empty or malformed")
                return None
                
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            return None

    def get_available_balance(self, currency: str) -> float:
        """
        Get available balance for a specific currency.
        Uses cached account data when available to avoid rate limiting.
        
        Args:
            currency: Currency code (e.g., 'USD', 'BTC', 'ETH')
            
        Returns:
            Available balance as float, 0.0 if currency not found or error
        """
        try:
            # Check if we have fresh cached account data first
            from datetime import datetime
            if self.cached_accounts and self.cached_accounts_timestamp:
                cache_age = (datetime.utcnow() - self.cached_accounts_timestamp).total_seconds()
                if cache_age < 60:
                    # Use cached data - much faster and avoids rate limiting
                    logger.info(f"💾 Using cached account data for {currency} balance lookup (cache age: {cache_age:.1f}s)")
                    
                    for account in self.cached_accounts:
                        if account.get('currency') == currency:
                            balance = float(account.get('available_balance', 0))
                            logger.info(f"💾 Found {currency} balance: {balance} from cache")
                            return balance
                    
                    # Currency not found in cached accounts
                    logger.debug(f"Currency {currency} not found in cached accounts (balance: 0.0)")
                    return 0.0
            
            # Fallback to get_accounts() which will handle caching and REST API calls
            logger.debug(f"No fresh cached data available, fetching accounts for {currency} balance")
            accounts = self.get_accounts()
            for account in accounts:
                if account.get('currency') == currency:
                    return float(account.get('available_balance', 0))
            
            # For currencies not in accounts (like XRP when we have 0 balance),
            # return 0.0 without warning - this is normal for BUY orders
            logger.debug(f"Currency {currency} not found in accounts (balance: 0.0)")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error fetching available balance for {currency}: {e}")
            return 0.0
    
    def validate_trade_balance(self, product_id: str, side: str, size_usd: float, 
                             current_price: float) -> Dict[str, Any]:
        """
        Validate that account has sufficient balance for the trade.
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            size_usd: Trade size in USD
            current_price: Current market price
            
        Returns:
            Dict with validation results
        """
        try:
            # Parse the product_id to get base and quote currencies
            base_currency, quote_currency = product_id.split('-')
            
            if side.upper() == 'BUY':
                # For buy orders, need sufficient quote currency (usually USD)
                required_balance = size_usd
                available_balance = self.get_available_balance(quote_currency)
                currency_needed = quote_currency
                
                if available_balance >= required_balance:
                    return {
                        'valid': True,
                        'message': f'Sufficient {currency_needed} balance for ${size_usd:.2f} buy order',
                        'available': available_balance,
                        'required': required_balance,
                        'currency': currency_needed
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'Insufficient {currency_needed} balance: ${available_balance:.2f} available, ${required_balance:.2f} required',
                        'available': available_balance,
                        'required': required_balance,
                        'currency': currency_needed
                    }
                    
            else:  # SELL
                # For sell orders, need sufficient base currency (e.g., BTC)
                base_size_needed = size_usd / current_price
                available_balance = self.get_available_balance(base_currency)
                
                if available_balance >= base_size_needed:
                    return {
                        'valid': True,
                        'message': f'Sufficient {base_currency} balance for {base_size_needed:.8f} {base_currency} sell order',
                        'available': available_balance,
                        'required': base_size_needed,
                        'currency': base_currency,
                        'size_usd': size_usd
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'Insufficient {base_currency} balance: {available_balance:.8f} available, {base_size_needed:.8f} required (${size_usd:.2f} USD)',
                        'available': available_balance,
                        'required': base_size_needed,
                        'currency': base_currency,
                        'size_usd': size_usd
                    }
                    
        except Exception as e:
            logger.error(f"Error validating trade balance: {e}")
            return {
                'valid': False,
                'message': f'Error validating balance: {str(e)}',
                'available': 0.0,
                'required': 0.0,
                'currency': 'UNKNOWN'
            }
    
    def get_raw_fills(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Get RAW fills from Coinbase API with ZERO processing or calculations.
        Returns the EXACT data that Coinbase sends us.
        
        Args:
            days_back: Number of days to look back for fills
        
        Returns:
            List of RAW fill dictionaries exactly as Coinbase sends them
        """
        try:
            if not self.client:
                logger.error("Coinbase client not initialized")
                return []
            
            logger.info(f"🔍 Fetching RAW Coinbase fills for last {days_back} days...")
            
            raw_fills = []
            cursor = None
            page_count = 0
            max_pages = 50  # Safety limit
            
            while page_count < max_pages:
                try:
                    # Get fills with pagination
                    if cursor:
                        response = self.client.get_fills(limit=1000, cursor=cursor)
                    else:
                        response = self.client.get_fills(limit=1000)
                    
                    if not response or not hasattr(response, 'fills'):
                        logger.warning(f"No fills returned from Coinbase API on page {page_count + 1}")
                        break
                    
                    fills = getattr(response, 'fills', [])
                    logger.info(f"📊 Page {page_count + 1}: Retrieved {len(fills)} fills from Coinbase")
                    
                    if not fills:
                        logger.info("No more fills to retrieve")
                        break
                    
                    # Store RAW Coinbase data - NO PROCESSING AT ALL
                    for fill in fills:
                        try:
                            raw_fill = {
                                'order_id': getattr(fill, 'order_id', None),
                                'trade_id': getattr(fill, 'trade_id', None),
                                'product_id': getattr(fill, 'product_id', None),
                                'side': getattr(fill, 'side', None),
                                'size': getattr(fill, 'size', None),  # RAW string from Coinbase
                                'price': getattr(fill, 'price', None),  # RAW string from Coinbase
                                'fee': getattr(fill, 'fee', None),  # RAW string from Coinbase
                                'trade_time': getattr(fill, 'trade_time', None),
                                'liquidity_indicator': getattr(fill, 'liquidity_indicator', None),
                                'size_in_quote': getattr(fill, 'size_in_quote', None),  # RAW boolean from Coinbase
                                'user_id': getattr(fill, 'user_id', None),
                                'commission': getattr(fill, 'commission', None),  # RAW string from Coinbase
                                'size_usd': getattr(fill, 'size_usd', None)  # RAW USD value from Coinbase (if provided)
                            }
                            
                            # NO CALCULATIONS - store exactly what Coinbase gives us
                            raw_fills.append(raw_fill)
                            
                        except Exception as e:
                            logger.warning(f"Failed to extract raw fill data: {e}")
                            continue
                    
                    # Check for next page
                    cursor = getattr(response, 'cursor', None)
                    if not cursor:
                        logger.info("No more pages available")
                        break
                    
                    page_count += 1
                    logger.info(f"Moving to page {page_count + 1}...")
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page_count + 1}: {e}")
                    break
            
            logger.info(f"✅ Retrieved {len(raw_fills)} RAW fills across {page_count + 1} pages")
            return raw_fills
            
        except Exception as e:
            logger.error(f"❌ Failed to get raw Coinbase fills: {e}")
            return []

    def start_price_websocket_streaming(self, product_ids: List[str]) -> dict:
        """Start WebSocket price streaming for specified products."""
        try:
            from .simple_websocket import get_websocket_service
            
            if not product_ids:
                return {
                    "success": False,
                    "message": "No products specified for streaming",
                    "products": []
                }
            
            # Start WebSocket price streaming
            ws_service = get_websocket_service()
            success = ws_service.start_streaming(product_ids)
            
            if success:
                logger.info(f"🚀 Started WebSocket price streaming for {len(product_ids)} products")
                return {
                    "success": True,
                    "message": f"WebSocket price streaming started for {len(product_ids)} products",
                    "products": product_ids,
                    "streaming": True
                }
            else:
                return {
                    "success": False,
                    "message": "WebSocket already running or failed to start",
                    "products": product_ids
                }
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket price streaming: {e}")
            return {
                "success": False,
                "message": f"Error starting WebSocket streaming: {str(e)}",
                "products": product_ids
            }

    def get_websocket_price_status(self) -> dict:
        """Get WebSocket price streaming status."""
        try:
            from .simple_websocket import get_websocket_service
            ws_service = get_websocket_service()
            
            return {
                "connected": ws_service.is_running(),
                "subscribed_products": len(ws_service.subscription_products),
                "cached_products": len(ws_service.get_all_prices()),
                "last_update": "Live" if ws_service.is_running() else "Not connected"
            }
        except Exception as e:
            logger.error(f"Error getting WebSocket price status: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def get_cache_stats(self) -> dict:
        """Get market data cache performance statistics."""
        return self.market_data_cache.get_stats()
    
    def get_cache_info(self) -> dict:
        """Get detailed cache information for debugging."""
        return self.market_data_cache.get_cache_info()
    
    def invalidate_cache(self, product_id: Optional[str] = None) -> int:
        """
        Invalidate market data cache.
        
        Args:
            product_id: If provided, only invalidate cache for this product.
                       If None, invalidate all cache entries.
                       
        Returns:
            Number of cache entries invalidated
        """
        return self.market_data_cache.invalidate(product_id)


# Global instance
coinbase_service = CoinbaseService()
