from typing import Optional, List, Callable, Dict, Any
import pandas as pd
import json
from threading import Thread
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
            if isinstance(message, str):
                message = json.loads(message)
            
            channel = message.get('channel', '')
            
            # Route message to appropriate handlers
            if channel in self.message_handlers:
                for handler in self.message_handlers[channel]:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler for {channel}: {e}")
            
            # Handle ticker updates for bot evaluation
            if channel == 'ticker':
                events = message.get('events', [])
                for event in events:
                    tickers = event.get('tickers', [])
                    for ticker in tickers:
                        product_id = ticker.get('product_id')
                        price = ticker.get('price')
                        if product_id and price:
                            logger.debug(f"Ticker update: {product_id} @ ${price}")
                            # Trigger bot evaluation for this product
                            self._trigger_bot_evaluations(product_id, ticker)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    def _trigger_bot_evaluations(self, product_id: str, ticker_data: dict):
        """Trigger bot evaluations for a specific product on ticker updates."""
        try:
            # Import here to avoid circular imports
            from ..services.streaming_bot_evaluator import StreamingBotEvaluator
            from ..core.database import SessionLocal
            
            # Create database session
            db = SessionLocal()
            try:
                evaluator = StreamingBotEvaluator(db)
                evaluator.evaluate_bots_on_ticker_update(product_id, ticker_data)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error triggering bot evaluations for {product_id}: {e}")
    
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
                    logger.info(f"Opening WebSocket connection...")
                    self.ws_client.open()
                    logger.info("WebSocket connection opened")
                    
                    logger.info(f"Starting ticker subscription for {product_ids}")
                    # Use the specific ticker method for each product
                    for product_id in product_ids:
                        self.ws_client.ticker(product_id)
                        logger.info(f"Subscribed to ticker for {product_id}")
                    
                    logger.info("Starting WebSocket message loop...")
                    self.ws_client.run_forever_with_exception_check()
                    
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    import traceback
                    logger.error(f"WebSocket traceback: {traceback.format_exc()}")
                    self.is_ws_running = False
            
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
            import uuid
            import time
            client_order_id = str(uuid.uuid4())
            
            # REAL TRADE EXECUTION
            logger.info(f"💰 EXECUTING REAL TRADE: {side} {size} {product_id}")
            
            # Real Coinbase order execution
            if side.lower() == "buy":
                response = self.client.market_order_buy(
                    product_id=product_id,
                    base_size=str(size),
                    client_order_id=client_order_id
                )
            else:
                response = self.client.market_order_sell(
                    product_id=product_id,
                    base_size=str(size),
                    client_order_id=client_order_id
                )
            
            # Extract order ID from response (need to check SDK structure)
            order_id = getattr(response, 'order_id', None) or getattr(response, 'id', None)
            
            return {
                "order_id": order_id,
                "client_order_id": client_order_id,
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
    
    def get_recent_fills(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Get recent fills/trades from Coinbase API for the specified number of days.
        
        Args:
            days_back: Number of days to look back for fills
        
        Returns:
            List of fill/trade dictionaries with real Coinbase data
        """
        try:
            if not self.client:
                logger.error("Coinbase client not initialized")
                return []
            
            logger.info(f"🔍 Fetching ALL Coinbase fills for last {days_back} days using pagination...")
            
            all_fills = []
            cursor = None
            page_count = 0
            max_pages = 50  # Safety limit to prevent infinite loops
            
            # Use pagination to get ALL fills, not just 100
            while page_count < max_pages:
                try:
                    # Get fills with pagination
                    if cursor:
                        response = self.client.get_fills(limit=1000, cursor=cursor)  # Max limit
                    else:
                        response = self.client.get_fills(limit=1000)  # Max limit for first page
                    
                    # Avoid slow __getitem__ - use getattr instead
                    if not response or not hasattr(response, 'fills'):
                        logger.warning(f"No fills returned from Coinbase API on page {page_count + 1}")
                        break
                    
                    fills = getattr(response, 'fills', [])
                    logger.info(f"📊 Page {page_count + 1}: Retrieved {len(fills)} fills from Coinbase")
                    
                    if not fills:
                        logger.info("No more fills to retrieve")
                        break
                    
                    # Convert Coinbase fills to our format
                    for fill in fills:
                        try:
                            processed_fill = {
                                'order_id': getattr(fill, 'order_id', None),
                                'trade_id': getattr(fill, 'trade_id', None),  # Unique fill ID
                                'product_id': getattr(fill, 'product_id', None),
                                'side': getattr(fill, 'side', '').upper(),
                                'size': float(getattr(fill, 'size', 0)),
                                'price': float(getattr(fill, 'price', 0)),
                                'fee': float(getattr(fill, 'fee', 0)),
                                'created_at': getattr(fill, 'trade_time', None),  # FIX: Use trade_time for actual timestamp
                                'liquidity_indicator': getattr(fill, 'liquidity_indicator', None),
                                'size_in_quote': getattr(fill, 'size_in_quote', False),
                                'user_id': getattr(fill, 'user_id', None),
                                'commission': float(getattr(fill, 'commission', 0))
                            }
                            
                            # Calculate USD size
                            if processed_fill['size_in_quote']:
                                processed_fill['size_usd'] = processed_fill['size']
                            else:
                                processed_fill['size_usd'] = processed_fill['size'] * processed_fill['price']
                            
                            all_fills.append(processed_fill)
                            
                        except Exception as e:
                            logger.warning(f"Failed to process fill: {e}")
                            continue
                    
                    # Check for next page
                    cursor = getattr(response, 'cursor', None)
                    if not cursor:
                        logger.info("No more pages available")
                        break
                    
                    page_count += 1
                    logger.info(f"Moving to page {page_count + 1} with cursor: {cursor[:10]}...")
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page_count + 1}: {e}")
                    break
            
            logger.info(f"✅ Retrieved total of {len(all_fills)} fills across {page_count + 1} pages")
            return all_fills
            
        except Exception as e:
            logger.error(f"❌ Failed to get Coinbase fills: {e}")
            return []


# Global instance
coinbase_service = CoinbaseService()
