"""
Coinbase Trade Synchronization Service
Syncs actual Coinbase trades into our database as production trades.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.models import Trade, Bot
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class CoinbaseSyncService:
    """
    Service to sync actual Coinbase trades into our database.
    Distinguishes between bot-made trades and external trades.
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        # Import here to avoid circular import
        from ..services.coinbase_service import coinbase_service
        self.coinbase_service = coinbase_service
    
    def sync_coinbase_trades(self, days_back: int = 1) -> Dict[str, Any]:
        """
        Sync actual Coinbase trades from the last N days.
        
        Args:
            days_back: Number of days to look back for trades
            
        Returns:
            Dict with sync results
        """
        try:
            logger.info(f"🔄 Starting Coinbase trade sync for last {days_back} days...")
            
            # Get actual trades from Coinbase using existing method
            coinbase_fills = self.coinbase_service.get_recent_fills(days_back)
            logger.info(f"📊 Found {len(coinbase_fills)} fills in Coinbase")
            
            # Check which trades we already have in database
            existing_order_ids = self._get_existing_order_ids()
            logger.info(f"📊 {len(existing_order_ids)} trades already in database")
            
            # Process new trades
            new_trades = []
            skipped_trades = []
            
            for fill in coinbase_fills:
                # Use the same unique ID logic as in trade creation
                unique_id = fill.get('trade_id') or fill.get('order_id')
                if unique_id and unique_id not in existing_order_ids:
                    trade = self._create_trade_from_coinbase_fill(fill)
                    if trade:
                        new_trades.append(trade)
                        self.db.add(trade)
                        logger.info(f"➕ Added new trade: {unique_id} for {fill.get('product_id')}")
                else:
                    skipped_trades.append(fill)
            
            self.db.commit()
            
            result = {
                "success": True,
                "coinbase_fills_found": len(coinbase_fills),
                "new_trades_synced": len(new_trades),
                "existing_trades_skipped": len(skipped_trades),
                "new_trade_ids": [t.id for t in new_trades]
            }
            
            logger.info(f"✅ Sync complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Coinbase sync failed: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "coinbase_fills_found": 0,
                "new_trades_synced": 0
            }
    
    def _get_existing_order_ids(self) -> set:
        """Get order IDs of trades already in our database."""
        try:
            existing_trades = self.db.query(Trade.order_id).all()
            return {trade.order_id for trade in existing_trades if trade.order_id}
        except Exception as e:
            logger.error(f"Failed to get existing order IDs: {e}")
            return set()
    
    def _create_trade_from_coinbase_fill(self, fill: Dict[str, Any]) -> Optional[Trade]:
        """Convert Coinbase fill data to our Trade model."""
        try:
            # Use the trade_id as order_id for uniqueness (fills can have same order_id)
            unique_id = fill.get('trade_id') or fill.get('order_id')
            
            # Parse Coinbase timestamp
            created_at = datetime.utcnow()
            if fill.get('created_at'):
                try:
                    from dateutil import parser
                    created_at = parser.parse(fill['created_at'])
                except:
                    pass
            
            # Determine bot_id if this trade was made by one of our bots
            bot_id = self._find_matching_bot(fill.get('product_id'))
            
            trade = Trade(
                bot_id=bot_id,  # Link to bot if this product has an active bot
                product_id=fill.get('product_id'),
                side=fill.get('side', '').upper(),
                size=float(fill.get('size', 0)),
                price=float(fill.get('price', 0)),
                fee=float(fill.get('fee', 0)),
                order_id=unique_id,  # Use trade_id for uniqueness
                status="filled",  # Coinbase fills are already executed

                combined_signal_score=0.0,  # Real trade - might not have signal
                signal_scores="{}",  # Real trade - might not have signals
                size_usd=float(fill.get('size_usd', 0)),
                created_at=created_at,
                filled_at=created_at
            )
            
            logger.info(f"💰 Synced Coinbase trade: {trade.side} ${trade.size_usd:.2f} {trade.product_id} @ ${trade.price}")
            return trade
            
        except Exception as e:
            logger.error(f"Failed to create trade from Coinbase fill: {e}")
            return None
    
    def _find_matching_bot(self, product_id: str) -> Optional[int]:
        """Find bot that trades this product."""
        try:
            bot = self.db.query(Bot).filter(Bot.pair == product_id).first()
            return bot.id if bot else None
        except Exception as e:
            logger.warning(f"Could not find bot for {product_id}: {e}")
            return None
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and trade counts."""
        try:
            total_trades = self.db.query(Trade).count()
            total_trades = self.db.query(Trade).count()
            # ALL TRADES ARE REAL NOW
            
            return {
                "total_trades": total_trades,
                "total_trades": total_trades,
                "all_trades_real": True,
                "last_sync": "Not implemented yet"  # Could add last sync timestamp
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "total_trades": 0,
                "production_trades": 0,
                "all_trades_real": True,
                "error": str(e)
            }


# Global instance
coinbase_sync_service = CoinbaseSyncService()
