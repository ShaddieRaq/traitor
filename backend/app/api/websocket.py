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
                    evaluation = manager.bot_evaluator.evaluate_bot(bot, market_data)
                    
                    # Calculate bot temperature based on signal scores
                    temperature = calculate_bot_temperature(evaluation.get('overall_score', 0))
                    
                    bot_update = {
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "pair": bot.pair,
                        "current_price": current_price,
                        "overall_score": evaluation.get('overall_score', 0),
                        "action": evaluation.get('action', 'hold'),
                        "confidence": evaluation.get('confidence', 0),
                        "temperature": temperature,
                        "confirmation_status": evaluation.get('confirmation_status', {}),
                        "timestamp": datetime.utcnow().isoformat()
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
