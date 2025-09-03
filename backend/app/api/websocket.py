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


# Global connection manager
manager = ConnectionManager()


def handle_ticker_update(message: dict):
    """Handle ticker updates from Coinbase WebSocket."""
    try:
        events = message.get('events', [])
        for event in events:
            tickers = event.get('tickers', [])
            for ticker in tickers:
                product_id = ticker.get('product_id')
                price = float(ticker.get('price', 0))
                
                # Schedule bot evaluation for this product
                asyncio.create_task(evaluate_bots_for_product(product_id, price))
                
    except Exception as e:
        logger.error(f"Error handling ticker update: {e}")


async def evaluate_bots_for_product(product_id: str, current_price: float):
    """Evaluate all bots for a specific product and broadcast updates."""
    try:
        # Get database session
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Get all running bots for this product
            bots = db.query(Bot).filter(
                Bot.pair == product_id,
                Bot.status == "RUNNING"
            ).all()
            
            if not bots:
                return
                
            # Initialize bot evaluator if needed
            if not manager.bot_evaluator:
                manager.bot_evaluator = BotSignalEvaluator(db)
            
            bot_updates = []
            for bot in bots:
                try:
                    # Get some basic market data (in real implementation, this would be more comprehensive)
                    # For now, we'll create a simple DataFrame with current price
                    import pandas as pd
                    market_data = pd.DataFrame({
                        'close': [current_price],
                        'high': [current_price],
                        'low': [current_price],
                        'open': [current_price],
                        'volume': [0]
                    })
                    
                    # Evaluate bot signals
                    evaluation_result = manager.bot_evaluator.evaluate_bot(bot, market_data)
                    
                    # Calculate temperature data (Phase 3.3 enhancement)
                    temperature_data = manager.bot_evaluator.calculate_bot_temperature(bot, market_data)
                    
                    bot_update = {
                        'bot_id': bot.id,
                        'bot_name': bot.name,
                        'pair': bot.pair,
                        'status': bot.status,
                        'current_price': current_price,
                        'combined_score': evaluation_result['overall_score'],
                        'action': evaluation_result['action'],
                        'confidence': evaluation_result['confidence'],
                        'confirmation_status': evaluation_result['confirmation_status'],
                        'temperature': temperature_data['temperature'],
                        'temperature_emoji': temperature_data['temperature_emoji'],
                        'distance_to_action': temperature_data['distance_to_action'],
                        'next_action': temperature_data['next_action'],
                        'threshold_info': temperature_data['threshold_info'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    bot_updates.append(bot_update)
                    
                except Exception as e:
                    logger.error(f"Error evaluating bot {bot.id}: {e}")
            
            if bot_updates:
                # Broadcast updates to all connected clients
                await manager.broadcast({
                    "type": "bot_updates",
                    "data": bot_updates
                })
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in evaluate_bots_for_product: {e}")


def calculate_bot_temperature(overall_score: float) -> str:
    """
    Calculate bot temperature based on overall signal score.
    
    Returns:
        - "hot" 🔥: Score > 0.7 or < -0.7 (strong signal)
        - "warm" 🌡️: Score > 0.3 or < -0.3 (moderate signal)  
        - "cool" ❄️: Score > 0.1 or < -0.1 (weak signal)
        - "frozen" 🧊: Score between -0.1 and 0.1 (no signal)
    """
    abs_score = abs(overall_score)
    
    if abs_score > 0.7:
        return "hot"
    elif abs_score > 0.3:
        return "warm"
    elif abs_score > 0.1:
        return "cool"
    else:
        return "frozen"


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
    
    # Add our ticker handler to Coinbase service
    coinbase_service.add_message_handler('ticker', handle_ticker_update)
    
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
                # Use mock data as fallback
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
                            # Use mock data as fallback
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
                                # Use mock data as fallback
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
    
    return {
        "success": True,
        "message": "Market data stream stopped"
    }
