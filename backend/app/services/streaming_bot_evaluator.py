"""
Streaming bot evaluator for real-time WebSocket-driven bot evaluation.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.models import Bot
from ..services.bot_evaluator import BotSignalEvaluator
from ..services.coinbase_service import coinbase_service

logger = logging.getLogger(__name__)


class StreamingBotEvaluator:
    """
    Handles real-time bot evaluation triggered by WebSocket ticker updates.
    Extends the existing BotSignalEvaluator for streaming capabilities.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.bot_evaluator = BotSignalEvaluator(db)
        self._ticker_cache = {}  # Cache recent ticker data
        self._market_data_cache = {}  # Cache market data to avoid repeated API calls
        
    def evaluate_bots_on_ticker_update(self, product_id: str, ticker_data: dict):
        """
        Evaluate all running bots for a specific product when ticker updates arrive.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            ticker_data: Real-time ticker data from WebSocket
        """
        try:
            # Update ticker cache
            self._ticker_cache[product_id] = {
                'price': float(ticker_data.get('price', 0)),
                'timestamp': datetime.utcnow(),
                'volume_24h': float(ticker_data.get('volume_24h', 0)),
                'best_bid': float(ticker_data.get('best_bid', 0)),
                'best_ask': float(ticker_data.get('best_ask', 0))
            }
            
            # Find all running bots for this product
            running_bots = self.db.query(Bot).filter(
                and_(
                    Bot.pair == product_id,
                    Bot.status == "RUNNING"
                )
            ).all()
            
            if not running_bots:
                logger.debug(f"No running bots found for {product_id}")
                return
                
            logger.info(f"Evaluating {len(running_bots)} running bots for {product_id} ticker update")
            
            # Get or refresh market data for signal calculations
            market_data = self._get_market_data_for_evaluation(product_id)
            
            if market_data.empty:
                logger.warning(f"No market data available for {product_id} bot evaluation")
                return
            
            # Evaluate each running bot
            evaluation_results = []
            for bot in running_bots:
                try:
                    result = self.bot_evaluator.evaluate_bot(bot, market_data)
                    evaluation_results.append({
                        'bot_id': bot.id,
                        'bot_name': bot.name,
                        'result': result
                    })
                    
                    logger.debug(f"Bot {bot.name}: {result.get('action', 'unknown')} "
                              f"(score: {result.get('overall_score', 0):.3f})")
                    
                except Exception as e:
                    logger.error(f"Error evaluating bot {bot.name}: {e}")
                    
            # Broadcast results to WebSocket clients if needed
            self._broadcast_evaluation_results(product_id, evaluation_results)
            
        except Exception as e:
            logger.error(f"Error in streaming bot evaluation for {product_id}: {e}")
    
    def _get_market_data_for_evaluation(self, product_id: str) -> pd.DataFrame:
        """
        Get market data for bot evaluation, using cache to avoid repeated API calls.
        """
        try:
            # Check if we have recent market data (within last 30 seconds)
            now = datetime.utcnow()
            cache_key = product_id
            
            if (cache_key in self._market_data_cache and 
                (now - self._market_data_cache[cache_key]['timestamp']).total_seconds() < 30):
                
                logger.debug(f"Using cached market data for {product_id}")
                return self._market_data_cache[cache_key]['data']
            
            # Fetch fresh market data
            logger.debug(f"Fetching fresh market data for {product_id}")
            market_data = coinbase_service.get_historical_data(
                product_id=product_id,
                granularity=3600,  # 1-hour candles
                limit=100
            )
            
            # Cache the data
            self._market_data_cache[cache_key] = {
                'data': market_data,
                'timestamp': now
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {product_id}: {e}")
            return pd.DataFrame()
    
    def _broadcast_evaluation_results(self, product_id: str, results: List[Dict]):
        """
        Broadcast evaluation results to WebSocket clients for real-time updates.
        """
        try:
            # Import here to avoid circular imports
            from ..api.websocket import manager
            
            # Prepare broadcast message
            message = {
                'type': 'bot_evaluation_update',
                'product_id': product_id,
                'timestamp': datetime.utcnow().isoformat(),
                'bot_count': len(results),
                'evaluations': []
            }
            
            # Add evaluation summaries
            for result in results:
                bot_result = result['result']
                message['evaluations'].append({
                    'bot_id': result['bot_id'],
                    'bot_name': result['bot_name'],
                    'action': bot_result.get('action', 'hold'),
                    'score': bot_result.get('overall_score', 0),
                    'confidence': bot_result.get('confidence', 0),
                    'temperature': bot_result.get('temperature', 'frozen')
                })
            
            # Broadcast to all connected WebSocket clients
            import asyncio
            try:
                # Run the broadcast in an async context
                loop = asyncio.get_event_loop()
                loop.create_task(manager.broadcast(message))
            except RuntimeError:
                # If no event loop is running, log instead
                logger.info(f"Would broadcast bot evaluation results: {len(results)} bots evaluated for {product_id}")
                
        except Exception as e:
            logger.error(f"Error broadcasting evaluation results: {e}")
    
    def get_active_products(self) -> List[str]:
        """
        Get list of products that have running bots.
        Used to determine which WebSocket subscriptions are needed.
        """
        try:
            active_products = self.db.query(Bot.pair).filter(
                Bot.status == "RUNNING"
            ).distinct().all()
            
            return [product[0] for product in active_products]
            
        except Exception as e:
            logger.error(f"Error getting active products: {e}")
            return []
    
    def clear_caches(self):
        """Clear internal caches - useful for testing or manual refresh."""
        self._ticker_cache.clear()
        self._market_data_cache.clear()
        logger.info("Streaming bot evaluator caches cleared")
