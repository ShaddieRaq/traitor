"""
New Trading Pair Detection Service

Monitors Coinbase for newly listed trading pairs and provides early opportunity alerts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.models import TradingPair, Notification
from ..core.database import get_db
from .coinbase_service import CoinbaseService
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


class NewPairDetector:
    """Service for detecting newly listed trading pairs on Coinbase."""
    
    def __init__(self):
        self.coinbase_service = CoinbaseService()
    
    def scan_for_new_pairs(self, db: Session) -> Dict[str, Any]:
        """
        Scan Coinbase for new trading pairs and update our tracking.
        
        Returns:
            Dict with scan results and any new pairs found
        """
        try:
            logger.info("🔍 Scanning for new trading pairs...")
            
            # Get all current products from Coinbase
            products = self.coinbase_service.get_products()
            if not products:
                return {"error": "Unable to fetch products from Coinbase"}
            
            # Get existing pairs from our database
            existing_pairs = {pair.product_id for pair in db.query(TradingPair).all()}
            
            new_pairs = []
            updated_pairs = []
            
            for product in products:
                product_id = getattr(product, 'product_id', None) or product.get('product_id', '') if hasattr(product, 'get') else getattr(product, 'product_id', '')
                
                if not product_id:
                    continue
                
                # Check if this is a new pair
                if product_id not in existing_pairs:
                    new_pair = self._create_new_pair_record(product, db)
                    if new_pair:
                        new_pairs.append(new_pair)
                        logger.info(f"🆕 New pair discovered: {product_id}")
                else:
                    # Update existing pair status
                    updated = self._update_existing_pair(product, db)
                    if updated:
                        updated_pairs.append(updated)
            
            # Create notifications for new USD pairs
            usd_new_pairs = [pair for pair in new_pairs if pair.quote_currency_id == 'USD']
            if usd_new_pairs:
                self._create_new_pair_notifications(usd_new_pairs)
            
            db.commit()
            
            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "total_products_scanned": len(products),
                "existing_pairs_tracked": len(existing_pairs),
                "new_pairs_found": len(new_pairs),
                "usd_pairs_found": len(usd_new_pairs),
                "pairs_updated": len(updated_pairs),
                "new_pairs": [
                    {
                        "product_id": pair.product_id,
                        "base_name": pair.base_name,
                        "initial_price": pair.initial_price,
                        "initial_volume": pair.initial_volume_24h
                    }
                    for pair in usd_new_pairs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error scanning for new pairs: {e}")
            db.rollback()
            return {"error": str(e)}
    
    def _create_new_pair_record(self, product, db: Session) -> Optional[TradingPair]:
        """Create a new TradingPair record from Coinbase product data."""
        try:
            product_id = getattr(product, 'product_id', None) or product.get('product_id', '') if hasattr(product, 'get') else getattr(product, 'product_id', '')
            base_currency_id = getattr(product, 'base_currency_id', None) or product.get('base_currency_id', '') if hasattr(product, 'get') else getattr(product, 'base_currency_id', '')
            quote_currency_id = getattr(product, 'quote_currency_id', None) or product.get('quote_currency_id', '') if hasattr(product, 'get') else getattr(product, 'quote_currency_id', '')
            base_name = getattr(product, 'base_name', None) or product.get('base_name', '') if hasattr(product, 'get') else getattr(product, 'base_name', '')
            status = getattr(product, 'status', None) or product.get('status', 'online') if hasattr(product, 'get') else getattr(product, 'status', 'online')
            trading_disabled = getattr(product, 'trading_disabled', False) or product.get('trading_disabled', False) if hasattr(product, 'get') else getattr(product, 'trading_disabled', False)
            is_disabled = getattr(product, 'is_disabled', False) or product.get('is_disabled', False) if hasattr(product, 'get') else getattr(product, 'is_disabled', False)
            
            # Get initial market data
            price = float(getattr(product, 'price', 0) or product.get('price', 0) if hasattr(product, 'get') else getattr(product, 'price', 0))
            volume_24h = float(getattr(product, 'approximate_quote_24h_volume', 0) or product.get('approximate_quote_24h_volume', 0) if hasattr(product, 'get') else getattr(product, 'approximate_quote_24h_volume', 0))
            
            new_pair = TradingPair(
                product_id=product_id,
                base_currency_id=base_currency_id,
                quote_currency_id=quote_currency_id,
                base_name=base_name,
                status=status,
                trading_disabled=trading_disabled,
                is_disabled=is_disabled,
                initial_price=price,
                initial_volume_24h=volume_24h,
                is_new_listing=True
            )
            
            db.add(new_pair)
            return new_pair
            
        except Exception as e:
            logger.error(f"Error creating new pair record for {product_id}: {e}")
            return None
    
    def _update_existing_pair(self, product, db: Session) -> Optional[TradingPair]:
        """Update existing pair status and info."""
        try:
            product_id = getattr(product, 'product_id', None) or product.get('product_id', '') if hasattr(product, 'get') else getattr(product, 'product_id', '')
            
            pair = db.query(TradingPair).filter(TradingPair.product_id == product_id).first()
            if not pair:
                return None
            
            # Update status fields
            status = getattr(product, 'status', None) or product.get('status', 'online') if hasattr(product, 'get') else getattr(product, 'status', 'online')
            trading_disabled = getattr(product, 'trading_disabled', False) or product.get('trading_disabled', False) if hasattr(product, 'get') else getattr(product, 'trading_disabled', False)
            is_disabled = getattr(product, 'is_disabled', False) or product.get('is_disabled', False) if hasattr(product, 'get') else getattr(product, 'is_disabled', False)
            
            # Check if status changed
            status_changed = (
                pair.status != status or
                pair.trading_disabled != trading_disabled or
                pair.is_disabled != is_disabled
            )
            
            if status_changed:
                pair.status = status
                pair.trading_disabled = trading_disabled
                pair.is_disabled = is_disabled
                pair.last_updated = datetime.utcnow()
                
                logger.info(f"📊 Updated status for {product_id}: {status}")
                return pair
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating pair {product_id}: {e}")
            return None
    
    def _create_new_pair_notifications(self, new_pairs: List[TradingPair]):
        """Create notifications for newly discovered USD pairs."""
        try:
            notification_service = get_notification_service()
            
            for pair in new_pairs:
                title = f"🆕 New Trading Pair: {pair.product_id}"
                message = f"New USD pair {pair.product_id} ({pair.base_name}) detected on Coinbase!"
                
                if pair.initial_price and pair.initial_volume_24h:
                    message += f"\n💰 Initial Price: ${pair.initial_price:.4f}"
                    message += f"\n📊 Initial Volume: ${pair.initial_volume_24h/1000000:.1f}M"
                
                message += f"\n⏰ First seen: {pair.first_seen.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                message += "\n\n🔍 Consider analyzing for trading potential!"
                
                notification_service.create_notification(
                    type="new_pair_alert",
                    title=title,
                    message=message,
                    priority="high",
                    data={
                        "product_id": pair.product_id,
                        "base_name": pair.base_name,
                        "initial_price": pair.initial_price,
                        "initial_volume_24h": pair.initial_volume_24h,
                        "first_seen": pair.first_seen.isoformat()
                    }
                )
            
            logger.info(f"📢 Created {len(new_pairs)} new pair notifications")
            
        except Exception as e:
            logger.error(f"Error creating new pair notifications: {e}")
    
    def get_recent_new_pairs(self, db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently discovered trading pairs."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            recent_pairs = db.query(TradingPair).filter(
                TradingPair.first_seen >= cutoff_date,
                TradingPair.quote_currency_id == 'USD'
            ).order_by(TradingPair.first_seen.desc()).all()
            
            return [
                {
                    "product_id": pair.product_id,
                    "base_name": pair.base_name,
                    "base_currency_id": pair.base_currency_id,
                    "status": pair.status,
                    "trading_disabled": pair.trading_disabled,
                    "first_seen": pair.first_seen.isoformat(),
                    "initial_price": pair.initial_price,
                    "initial_volume_24h": pair.initial_volume_24h,
                    "is_new_listing": pair.is_new_listing,
                    "days_since_listing": (datetime.utcnow() - pair.first_seen).days
                }
                for pair in recent_pairs
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent new pairs: {e}")
            return []
    
    def mark_pairs_as_processed(self, db: Session, product_ids: List[str]):
        """Mark new pairs as processed (no longer 'new')."""
        try:
            db.query(TradingPair).filter(
                TradingPair.product_id.in_(product_ids)
            ).update(
                {"is_new_listing": False},
                synchronize_session=False
            )
            db.commit()
            logger.info(f"Marked {len(product_ids)} pairs as processed")
            
        except Exception as e:
            logger.error(f"Error marking pairs as processed: {e}")
            db.rollback()


def get_new_pair_detector() -> NewPairDetector:
    """Get a singleton instance of the new pair detector."""
    return NewPairDetector()
