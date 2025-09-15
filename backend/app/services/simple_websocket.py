"""
Simple Coinbase WebSocket Price Service
Real-time price feeds to eliminate REST API rate limiting.
"""

import asyncio
import json
import logging
import websockets
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class SimpleCoinbaseWebSocket:
    """Simple, reliable Coinbase WebSocket price service."""
    
    def __init__(self):
        self.price_cache: Dict[str, dict] = {}
        self.is_connected = False
        self.subscription_products: List[str] = []
        self._running = False
        self._thread = None
        
    def start_streaming(self, product_ids: List[str]):
        """Start WebSocket streaming in background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("WebSocket already running")
            return False
            
        self.subscription_products = product_ids
        self._running = True
        
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._websocket_loop())
            except Exception as e:
                logger.error(f"WebSocket thread error: {e}")
            finally:
                loop.close()
        
        self._thread = threading.Thread(target=run_websocket, daemon=True)
        self._thread.start()
        logger.info(f"✅ Started WebSocket for {len(product_ids)} products")
        return True
    
    async def _websocket_loop(self):
        """Main WebSocket connection loop."""
        uri = "wss://advanced-trade-ws.coinbase.com"
        
        while self._running:
            try:
                logger.info("🔌 Connecting to Coinbase Advanced Trade WebSocket...")
                
                async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
                    self.is_connected = True
                    logger.info("✅ Connected to Coinbase WebSocket")
                    
                    # Subscribe to ticker updates
                    subscribe_msg = {
                        "type": "subscribe",
                        "product_ids": self.subscription_products,
                        "channel": "ticker"
                    }
                    
                    await websocket.send(json.dumps(subscribe_msg))
                    logger.info(f"📡 Subscribed to ticker for {len(self.subscription_products)} products")
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self._running:
                            break
                            
                        try:
                            data = json.loads(message)
                            self._process_message(data)
                        except Exception as e:
                            logger.warning(f"Error processing message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket disconnected, reconnecting in 5 seconds...")
                self.is_connected = False
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}, reconnecting in 10 seconds...")
                self.is_connected = False
                await asyncio.sleep(10)
    
    def _process_message(self, data: dict):
        """Process incoming WebSocket messages."""
        try:
            if data.get("channel") == "ticker" and "events" in data:
                for event in data.get("events", []):
                    if "tickers" in event:
                        for ticker in event.get("tickers", []):
                            product_id = ticker.get("product_id")
                            if product_id and product_id in self.subscription_products:
                                
                                price_data = {
                                    "product_id": product_id,
                                    "price": float(ticker.get("price", 0)),
                                    "volume_24h": float(ticker.get("volume_24_h", 0)),
                                    "best_bid": float(ticker.get("best_bid", 0)),
                                    "best_ask": float(ticker.get("best_ask", 0)),
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "data_source": "websocket"
                                }
                                
                                self.price_cache[product_id] = price_data
                                logger.info(f"💰 {product_id}: ${price_data['price']}")
                                
        except Exception as e:
            logger.error(f"Error processing ticker: {e}")
    
    def get_price(self, product_id: str) -> Optional[dict]:
        """Get cached price for a product."""
        return self.price_cache.get(product_id)
    
    def get_all_prices(self) -> Dict[str, dict]:
        """Get all cached prices."""
        return self.price_cache.copy()
    
    def is_running(self) -> bool:
        """Check if WebSocket is running."""
        return self._running and self.is_connected
    
    def stop(self):
        """Stop WebSocket streaming."""
        self._running = False
        self.is_connected = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🛑 WebSocket stopped")


# Global instance
_websocket_service = None


def get_websocket_service() -> SimpleCoinbaseWebSocket:
    """Get the global WebSocket service instance."""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = SimpleCoinbaseWebSocket()
    return _websocket_service
