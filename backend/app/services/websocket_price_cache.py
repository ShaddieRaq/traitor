"""
WebSocket Price Cache Service
Maintains real-time price data from Coinbase WebSocket feeds.
Replaces REST API calls with cached WebSocket data.
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
import time

logger = logging.getLogger(__name__)


class WebSocketPriceCache:
    """
    Manages real-time price data from Coinbase WebSocket feeds.
    Provides instant price access without REST API calls.
    """
    
    def __init__(self):
        self.price_cache: Dict[str, dict] = {}
        self.websocket = None
        self.is_connected = False
        self.subscription_products: List[str] = []
        self.last_update_time = {}
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        
    async def connect_and_subscribe(self, product_ids: List[str]):
        """Connect to Coinbase WebSocket and subscribe to ticker updates."""
        self.subscription_products = product_ids
        self._running = True
        
        while self._running and self._reconnect_attempts < self._max_reconnect_attempts:
            try:
                logger.info(f"Connecting to Coinbase Advanced Trade WebSocket for products: {product_ids}")
                
                # Coinbase Advanced Trade WebSocket endpoint
                uri = "wss://advanced-trade-ws.coinbase.com"
                
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    self.is_connected = True
                    self._reconnect_attempts = 0
                    
                    # Subscribe to ticker channel using Advanced Trade format
                    subscribe_message = {
                        "type": "subscribe",
                        "product_ids": product_ids,
                        "channel": "ticker"
                    }
                    
                    await websocket.send(json.dumps(subscribe_message))
                    logger.info(f"✅ Subscribed to Advanced Trade WebSocket for {len(product_ids)} products")
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self._running:
                            break
                            
                        try:
                            data = json.loads(message)
                            await self._handle_ticker_message(data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse WebSocket message: {e}")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, attempting to reconnect...")
                self.is_connected = False
                self._reconnect_attempts += 1
                await asyncio.sleep(5 * self._reconnect_attempts)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                self.is_connected = False
                self._reconnect_attempts += 1
                await asyncio.sleep(5 * self._reconnect_attempts)
                
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, stopping WebSocket")
            self.is_connected = False
            
    async def _handle_ticker_message(self, data: dict):
        """Process incoming ticker messages and update price cache."""
        try:
            # Coinbase Advanced Trade format: check for events array with tickers
            if data.get("channel") == "ticker" and "events" in data:
                events = data.get("events", [])
                
                for event in events:
                    if "tickers" in event:
                        tickers = event.get("tickers", [])
                        
                        for ticker in tickers:
                            product_id = ticker.get("product_id")
                            if product_id and product_id in self.subscription_products:
                                
                                price_data = {
                                    "price": float(ticker.get("price", 0)),
                                    "volume_24h": float(ticker.get("volume_24_h", 0)),
                                    "best_bid": float(ticker.get("best_bid", 0)),
                                    "best_ask": float(ticker.get("best_ask", 0)),
                                    "timestamp": datetime.utcnow(),
                                    "high_24h": float(ticker.get("high_24_h", 0)),
                                    "low_24h": float(ticker.get("low_24_h", 0))
                                }
                                
                                self.price_cache[product_id] = price_data
                                self.last_update_time[product_id] = datetime.utcnow()
                                
                                logger.info(f"✅ Updated price for {product_id}: ${price_data['price']}")
        
        except Exception as e:
            logger.error(f"Error processing ticker message: {e}")
            logger.debug(f"Message data: {data}")
    
    def get_cached_price(self, product_id: str) -> Optional[dict]:
        """Get cached price data for a product."""
        if product_id not in self.price_cache:
            return None
            
        price_data = self.price_cache[product_id].copy()
        
        # Check if data is stale (older than 30 seconds)
        last_update = self.last_update_time.get(product_id)
        if last_update and (datetime.utcnow() - last_update).total_seconds() > 30:
            logger.warning(f"Stale price data for {product_id} (age: {(datetime.utcnow() - last_update).total_seconds()}s)")
            return None
            
        return {
            "product_id": product_id,
            "price": price_data["price"],
            "volume_24h": price_data["volume_24h"],
            "best_bid": price_data["best_bid"],
            "best_ask": price_data["best_ask"],
            "timestamp": price_data["timestamp"].isoformat(),
            "data_source": "websocket_cache"
        }
    
    def get_all_cached_prices(self) -> Dict[str, dict]:
        """Get all cached price data."""
        result = {}
        for product_id in self.subscription_products:
            price_data = self.get_cached_price(product_id)
            if price_data:
                result[product_id] = price_data
        return result
    
    def is_price_available(self, product_id: str) -> bool:
        """Check if fresh price data is available for a product."""
        return self.get_cached_price(product_id) is not None
    
    def get_connection_status(self) -> dict:
        """Get WebSocket connection status and statistics."""
        return {
            "connected": self.is_connected,
            "subscribed_products": len(self.subscription_products),
            "cached_products": len(self.price_cache),
            "reconnect_attempts": self._reconnect_attempts,
            "last_updates": {
                product_id: self.last_update_time.get(product_id, "Never").isoformat() 
                if isinstance(self.last_update_time.get(product_id), datetime) 
                else "Never"
                for product_id in self.subscription_products
            }
        }
    
    async def disconnect(self):
        """Disconnect from WebSocket and cleanup."""
        self._running = False
        self.is_connected = False
        
        if self.websocket:
            await self.websocket.close()
            
        logger.info("WebSocket price cache disconnected")


# Global instance
_price_cache_instance = None
_websocket_task = None
_event_loop = None


def get_price_cache() -> WebSocketPriceCache:
    """Get the global WebSocket price cache instance."""
    global _price_cache_instance
    if _price_cache_instance is None:
        _price_cache_instance = WebSocketPriceCache()
    return _price_cache_instance


async def start_price_websocket(product_ids: List[str]):
    """Start the WebSocket price streaming in background."""
    global _websocket_task, _event_loop
    
    cache = get_price_cache()
    
    # Create and run WebSocket connection
    _websocket_task = asyncio.create_task(
        cache.connect_and_subscribe(product_ids)
    )
    
    logger.info(f"Started WebSocket price streaming for {len(product_ids)} products")
    return _websocket_task


async def stop_price_websocket():
    """Stop the WebSocket price streaming."""
    global _websocket_task
    
    cache = get_price_cache()
    await cache.disconnect()
    
    if _websocket_task and not _websocket_task.done():
        _websocket_task.cancel()
        try:
            await _websocket_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Stopped WebSocket price streaming")


def start_price_websocket_background(product_ids: List[str]):
    """Start WebSocket price streaming in a background thread."""
    def run_websocket():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_price_websocket(product_ids))
        except Exception as e:
            logger.error(f"WebSocket background task error: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    logger.info(f"Started WebSocket price streaming in background thread for {len(product_ids)} products")
    return thread
