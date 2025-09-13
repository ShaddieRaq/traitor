"""
Service for managing raw trade data from Coinbase API.
This service handles ONLY the clean, unprocessed trade data.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging

from ..models.models import RawTrade
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class RawTradeService:
    """Service for accessing clean raw trade data."""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def get_all_raw_trades(self, limit: int = 1000) -> List[RawTrade]:
        """Get all raw trades from the database."""
        try:
            return self.db.query(RawTrade).order_by(desc(RawTrade.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching raw trades: {e}")
            return []
    
    def get_raw_trades_by_product(self, product_id: str, limit: int = 1000) -> List[RawTrade]:
        """Get raw trades for a specific trading pair."""
        try:
            return self.db.query(RawTrade).filter(
                RawTrade.product_id == product_id
            ).order_by(desc(RawTrade.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching raw trades for {product_id}: {e}")
            return []
    
    def get_raw_trade_by_fill_id(self, fill_id: str) -> Optional[RawTrade]:
        """Get a specific raw trade by Coinbase fill ID."""
        try:
            return self.db.query(RawTrade).filter(RawTrade.fill_id == fill_id).first()
        except Exception as e:
            logger.error(f"Error fetching raw trade {fill_id}: {e}")
            return None
    
    def get_raw_trades_by_order_id(self, order_id: str) -> List[RawTrade]:
        """Get all raw trades for a specific order ID."""
        try:
            return self.db.query(RawTrade).filter(RawTrade.order_id == order_id).all()
        except Exception as e:
            logger.error(f"Error fetching raw trades for order {order_id}: {e}")
            return []
    
    def calculate_pnl_by_product(self) -> Dict[str, Dict[str, Any]]:
        """Calculate P&L by trading pair using clean raw data."""
        try:
            raw_trades = self.get_all_raw_trades()
            pnl_by_product = {}
            
            for trade in raw_trades:
                product_id = trade.product_id
                if product_id not in pnl_by_product:
                    pnl_by_product[product_id] = {
                        'total_trades': 0,
                        'buy_trades': 0,
                        'sell_trades': 0,
                        'total_spent': 0.0,  # Buy orders
                        'total_received': 0.0,  # Sell orders
                        'total_fees': 0.0,
                        'net_pnl': 0.0
                    }
                
                # Calculate USD value correctly based on size_in_quote flag
                if trade.size_in_quote:
                    # Size is already in USD (quote currency)
                    usd_value = float(trade.size)
                else:
                    # Size is in base currency, multiply by price
                    usd_value = float(trade.size) * float(trade.price)
                
                # Add commission/fees
                commission = float(trade.commission) if trade.commission else 0.0
                
                # Track by side
                side_lower = trade.side.lower()
                pnl_by_product[product_id]['total_trades'] += 1
                
                if side_lower == 'buy':
                    pnl_by_product[product_id]['buy_trades'] += 1
                    pnl_by_product[product_id]['total_spent'] += usd_value + commission
                elif side_lower == 'sell':
                    pnl_by_product[product_id]['sell_trades'] += 1
                    pnl_by_product[product_id]['total_received'] += usd_value - commission
                
                pnl_by_product[product_id]['total_fees'] += commission
            
            # Calculate net P&L for each product
            for product_id, data in pnl_by_product.items():
                data['net_pnl'] = data['total_received'] - data['total_spent']
            
            return pnl_by_product
            
        except Exception as e:
            logger.error(f"Error calculating P&L by product: {e}")
            return {}
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get overall trading statistics from raw data."""
        try:
            total_trades = self.db.query(RawTrade).count()
            
            if total_trades == 0:
                return {
                    'total_trades': 0,
                    'total_products': 0,
                    'total_volume_usd': 0.0,
                    'total_fees': 0.0,
                    'net_pnl': 0.0
                }
            
            # Get all products
            products = self.db.query(RawTrade.product_id).distinct().all()
            total_products = len(products)
            
            # Calculate totals
            pnl_by_product = self.calculate_pnl_by_product()
            total_volume_usd = sum(
                data['total_spent'] + data['total_received'] 
                for data in pnl_by_product.values()
            )
            total_fees = sum(data['total_fees'] for data in pnl_by_product.values())
            net_pnl = sum(data['net_pnl'] for data in pnl_by_product.values())
            
            return {
                'total_trades': total_trades,
                'total_products': total_products,
                'total_volume_usd': total_volume_usd,
                'total_fees': total_fees,
                'net_pnl': net_pnl
            }
            
        except Exception as e:
            logger.error(f"Error calculating trading stats: {e}")
            return {}
    
    def store_raw_trade(self, fill_data: Dict[str, Any]) -> Optional[RawTrade]:
        """Store a raw trade from Coinbase fill data."""
        try:
            # Check if trade already exists
            existing_trade = self.get_raw_trade_by_fill_id(fill_data.get('trade_id'))
            if existing_trade:
                logger.debug(f"Raw trade {fill_data.get('trade_id')} already exists")
                return existing_trade
            
            # Create new raw trade record
            raw_trade = RawTrade(
                fill_id=fill_data.get('trade_id'),
                order_id=fill_data.get('order_id'),
                product_id=fill_data.get('product_id'),
                side=fill_data.get('side', '').upper(),
                size=float(fill_data.get('size', 0)),
                size_in_quote=bool(fill_data.get('size_in_quote', False)),
                price=float(fill_data.get('price', 0)),
                commission=float(fill_data.get('commission', 0)) if fill_data.get('commission') else None,
                created_at=fill_data.get('trade_time', datetime.utcnow().isoformat())
            )
            
            self.db.add(raw_trade)
            self.db.commit()
            self.db.refresh(raw_trade)
            
            logger.info(f"✅ Stored raw trade: {raw_trade.fill_id} - {raw_trade.side} {raw_trade.size} {raw_trade.product_id}")
            return raw_trade
            
        except Exception as e:
            logger.error(f"Error storing raw trade: {e}")
            self.db.rollback()
            return None


# Global instance
raw_trade_service = RawTradeService()
