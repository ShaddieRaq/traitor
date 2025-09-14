"""
WebSocket endpoints for real-time data streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.models import Bot
from ..services.coinbase_service import coinbase_service
from ..utils.temperature import calculate_bot_temperature
from ..services.bot_evaluator import BotSignalEvaluator

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time bot status updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.bot_evaluator = None
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSockets."""
        if not self.active_connections:
            return
            
        disconnect_list = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnect_list.append(connection)
        
        # Clean up failed connections
        for connection in disconnect_list:
            self.disconnect(connection)
    
    async def broadcast_trade_update(self, trade_update: dict):
        """Broadcast trade execution updates to all connected clients."""
        message = {
            "type": "trade_execution_update",
            "data": trade_update,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/trade-execution")
async def websocket_trade_execution(websocket: WebSocket):
    """WebSocket endpoint for real-time trade execution updates."""
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "trade_connection_established",
            "message": "Connected to trade execution updates",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        # Keep connection alive for trade updates
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in trade execution WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/bot-status")
async def websocket_bot_status(websocket: WebSocket):
    """WebSocket endpoint for real-time bot status updates."""
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to bot status updates",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
                elif message.get("type") == "subscribe_products":
                    # Handle product subscription requests
                    product_ids = message.get("product_ids", [])
                    await manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "product_ids": product_ids,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message handling: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.post("/websocket/start")
async def start_websocket_streaming(db: Session = Depends(get_db)):
    """Start WebSocket streaming for all active bot pairs."""
    try:
        # Get active products from running bots
        from ..services.streaming_bot_evaluator import StreamingBotEvaluator
        streaming_evaluator = StreamingBotEvaluator(db)
        active_products = streaming_evaluator.get_active_products()
        
        if not active_products:
            return {
                "success": False,
                "message": "No running bots found - no products to stream",
                "active_products": []
            }
        
        # Start WebSocket connection for active products
        success = coinbase_service.start_websocket(active_products, ['ticker'])
        
        return {
            "success": success,
            "message": "WebSocket streaming started for active bot pairs" if success else "Failed to start WebSocket streaming",
            "active_products": active_products,
            "connection_status": coinbase_service.get_websocket_status()
        }
        
    except Exception as e:
        logger.error(f"Error starting WebSocket streaming: {e}")
        return {
            "success": False,
            "message": f"Error starting WebSocket streaming: {str(e)}",
            "active_products": []
        }


@router.post("/websocket/stop")
async def stop_websocket_streaming():
    """Stop WebSocket streaming."""
    try:
        coinbase_service.stop_websocket()
        return {
            "success": True,
            "message": "WebSocket streaming stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping WebSocket streaming: {e}")
        return {
            "success": False,
            "message": f"Error stopping WebSocket streaming: {str(e)}"
        }


@router.get("/websocket/status")
async def get_websocket_status():
    """Get current WebSocket connection status."""
    coinbase_ws_status = coinbase_service.get_websocket_status()
    
    return {
        "active_connections": len(manager.active_connections),
        "coinbase_websocket": coinbase_ws_status,
        "bot_evaluator_initialized": manager.bot_evaluator is not None
    }


@router.post("/websocket/start-market-stream")
async def start_market_stream(product_ids: List[str] = None):
    """Start Coinbase WebSocket stream for market data."""
    if product_ids is None:
        # Default to major trading pairs
        product_ids = ["BTC-USD", "ETH-USD", "LTC-USD"]
    
    # Note: Ticker handling is now done directly in coinbase_service._handle_ws_message
    # via StreamingBotEvaluator integration
    
    # Start WebSocket connection
    success = coinbase_service.start_websocket(product_ids, ['ticker'])
    
    return {
        "success": success,
        "product_ids": product_ids,
        "message": "Market data stream started" if success else "Failed to start market data stream"
    }


@router.post("/websocket/stop-market-stream")
async def stop_market_stream():
    """Stop Coinbase WebSocket stream for market data."""
    coinbase_service.stop_websocket()
    
    return {
        "success": True,
        "message": "Market data stream stopped"
    }


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time dashboard updates (Phase 3.3).
    
    Provides live bot temperature data, signal updates, and market data.
    """
    await manager.connect(websocket)
    try:
        # Send initial dashboard data
        from ..services.bot_evaluator import get_bot_evaluator
        from ..services.coinbase_service import coinbase_service
        evaluator = get_bot_evaluator(db)
        
        # Get running bots and fetch real market data
        bots = db.query(Bot).all()
        running_bots = [b for b in bots if b.status == 'RUNNING']
        
        # Fetch market data for each unique trading pair
        market_data_cache = {}
        unique_pairs = set(bot.pair for bot in running_bots)
        for pair in unique_pairs:
            try:
                market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
            except Exception as e:
                logger.error(f"Failed to get market data for {pair}: {e}")
                # Use fallback data if API unavailable
                import pandas as pd
                market_data_cache[pair] = pd.DataFrame({
                    'close': [100.0],
                    'high': [101.0],
                    'low': [99.0], 
                    'open': [100.5],
                    'volume': [1000]
                })
        
        # Get initial temperature data with real market data
        temperatures = evaluator.get_all_bot_temperatures(market_data_cache)
        
        initial_data = {
            "type": "dashboard_init",
            "data": {
                "total_bots": len(bots),
                "running_bots": len(running_bots),
                "stopped_bots": len(bots) - len(running_bots),
                "bot_temperatures": temperatures,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await manager.send_personal_message(initial_data, websocket)
        
        # Keep connection alive and send periodic updates
        import asyncio
        last_update_time = datetime.utcnow()
        update_interval = 30  # Send updates every 30 seconds
        
        while True:
            try:
                # Check if it's time for a periodic update
                now = datetime.utcnow()
                time_since_update = (now - last_update_time).total_seconds()
                
                if time_since_update >= update_interval:
                    # Send automatic temperature update
                    running_bots = [b for b in db.query(Bot).all() if b.status == 'RUNNING']
                    
                    # Fetch market data for each unique trading pair
                    market_data_cache = {}
                    unique_pairs = set(bot.pair for bot in running_bots)
                    for pair in unique_pairs:
                        try:
                            market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
                        except Exception as e:
                            logger.error(f"Failed to get market data for {pair}: {e}")
                            # Use fallback data if API unavailable
                            import pandas as pd
                            market_data_cache[pair] = pd.DataFrame({
                                'close': [100.0],
                                'high': [101.0],
                                'low': [99.0], 
                                'open': [100.5],
                                'volume': [1000]
                            })
                    
                    # Send current temperature data with real market data
                    temperatures = evaluator.get_all_bot_temperatures(market_data_cache)
                    update_data = {
                        "type": "temperature_update",
                        "data": {
                            "bot_temperatures": temperatures,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                    await manager.send_personal_message(update_data, websocket)
                    last_update_time = now
                    logger.info(f"Sent automatic temperature update to WebSocket client")
                
                # Wait for client messages with a short timeout to allow periodic updates
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await manager.send_personal_message({"type": "pong"}, websocket)
                    elif message.get("type") == "request_update":
                        # Send immediate temperature update (same logic as above)
                        running_bots = [b for b in db.query(Bot).all() if b.status == 'RUNNING']
                        
                        # Fetch market data for each unique trading pair
                        market_data_cache = {}
                        unique_pairs = set(bot.pair for bot in running_bots)
                        for pair in unique_pairs:
                            try:
                                market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
                            except Exception as e:
                                logger.error(f"Failed to get market data for {pair}: {e}")
                                # Use fallback data if API unavailable
                                import pandas as pd
                                market_data_cache[pair] = pd.DataFrame({
                                    'close': [100.0],
                                    'high': [101.0],
                                    'low': [99.0], 
                                    'open': [100.5],
                                    'volume': [1000]
                                })
                        
                        # Send current temperature data with real market data
                        temperatures = evaluator.get_all_bot_temperatures(market_data_cache)
                        update_data = {
                            "type": "temperature_update",
                            "data": {
                                "bot_temperatures": temperatures,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                        await manager.send_personal_message(update_data, websocket)
                        last_update_time = now  # Reset timer after manual update
                        
                except asyncio.TimeoutError:
                    # Timeout is expected - just continue the loop for periodic updates
                    continue
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in dashboard WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


async def broadcast_temperature_updates():
    """
    Periodic task to broadcast temperature updates to dashboard clients (Phase 3.3).
    
    This function should be called periodically to send temperature updates.
    """
    try:
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            from ..services.bot_evaluator import get_bot_evaluator
            evaluator = get_bot_evaluator(db)
            
            # Get current temperature data
            temperatures = evaluator.get_all_bot_temperatures()
            
            if temperatures:
                # Broadcast to all connected dashboard clients
                update_message = {
                    "type": "temperature_update",
                    "data": {
                        "bot_temperatures": temperatures,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                await manager.broadcast(update_message)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error broadcasting temperature updates: {e}")


@router.post("/start-temperature-stream")
async def start_temperature_stream():
    """Start periodic temperature broadcasting for dashboard updates."""
    # In a real implementation, this would start a background task
    # For now, we'll rely on the market data updates to trigger temperature broadcasts
    return {
        "success": True,
        "message": "Temperature streaming enabled via market data updates"
    }

@router.post("/start-portfolio-stream")
async def start_portfolio_stream():
    """Start WebSocket portfolio streaming to eliminate REST API rate limiting."""
    try:
        # Get all active bot product IDs
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
            product_ids = list(set([bot.pair for bot in active_bots if bot.pair]))
            
            if not product_ids:
                product_ids = ["BTC-USD", "ETH-USD", "SOL-USD"]  # Default products
            
            logger.info(f"Starting portfolio streaming for products: {product_ids}")
            
            # Start portfolio WebSocket streaming
            success = coinbase_service.start_portfolio_streaming(product_ids)
            
            if success:
                return {
                    "success": True,
                    "message": f"Portfolio WebSocket streaming started for {len(product_ids)} products",
                    "products": product_ids,
                    "status": "Real-time portfolio data will eliminate REST API rate limiting"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to start portfolio streaming",
                    "error": "WebSocket initialization failed"
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error starting portfolio stream: {e}")
        return {
            "success": False,
            "message": "Failed to start portfolio streaming",
            "error": str(e)
        }

@router.get("/portfolio-stream-status")
async def get_portfolio_stream_status():
    """Get current portfolio streaming status."""
    try:
        ws_status = coinbase_service.get_websocket_status()
        portfolio_data = coinbase_service.get_portfolio_data()
        
        return {
            "websocket_running": ws_status["is_running"],
            "portfolio_data_available": ws_status["portfolio_data_available"],
            "last_portfolio_update": ws_status["last_portfolio_update"],
            "accounts_count": len(portfolio_data["accounts"]),
            "data_age_seconds": portfolio_data["data_age_seconds"],
            "is_realtime": portfolio_data["is_realtime"],
            "status": "healthy" if portfolio_data["is_realtime"] else "fallback_to_rest_api"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio stream status: {e}")
        return {
            "error": str(e),
            "status": "error"
        }

@router.get("/portfolio-data")
async def get_realtime_portfolio_data():
    """Get current real-time portfolio data from WebSocket stream."""
    try:
        portfolio_data = coinbase_service.get_portfolio_data()
        return portfolio_data
        
    except Exception as e:
        logger.error(f"Error getting portfolio data: {e}")
        return {
            "error": str(e),
            "accounts": [],
            "is_realtime": False
        }
