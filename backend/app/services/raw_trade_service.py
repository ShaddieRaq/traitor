"""
Service for managing raw trade data from Coinbase API.
This service handles ONLY the clean, unprocessed trade data.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging
from decimal import Decimal

from ..models.models import RawTrade
from ..core.database import SessionLocal
from .market_data_service import MarketDataService

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
            
            # Group trades by product
            trades_by_product = {}
            for trade in raw_trades:
                product_id = trade.product_id
                if product_id not in trades_by_product:
                    trades_by_product[product_id] = []
                trades_by_product[product_id].append(trade)
            
            # Calculate P&L for each product
            for product_id, trades in trades_by_product.items():
                pnl_data = self._calculate_product_pnl(product_id, trades)
                pnl_by_product[product_id] = pnl_data
                
            return pnl_by_product
            
        except Exception as e:
            logger.error(f"Error calculating P&L by product: {e}")
            return {}
    
    def _calculate_product_pnl(self, product_id: str, trades: List) -> Dict[str, Any]:
        """Calculate P&L for a specific product using proper accounting."""
        total_spent = 0.0
        total_received = 0.0
        total_fees = 0.0
        buy_trades = 0
        sell_trades = 0
        realized_pnl = 0.0
        
        # Calculate average buy price for realized P&L
        total_buy_cost = 0.0
        total_buy_size = 0.0
        
        processed_fills = set()
        
        for trade in trades:
            # Skip duplicates
            if trade.fill_id in processed_fills:
                continue
            processed_fills.add(trade.fill_id)
            
            # Skip size_in_quote trades
            if hasattr(trade, 'size_in_quote') and trade.size_in_quote:
                continue
                
            size = float(trade.size)
            price = float(trade.price)
            commission = float(trade.commission) if trade.commission else 0.0
            usd_value = size * price
            
            if trade.side.lower() == 'buy':
                buy_trades += 1
                total_spent += usd_value + commission
                total_buy_cost += usd_value
                total_buy_size += size
            elif trade.side.lower() == 'sell':
                sell_trades += 1
                total_received += usd_value - commission
                
                # Calculate realized P&L for this sell using average cost
                if total_buy_size > 0:
                    avg_buy_price = total_buy_cost / total_buy_size
                    cost_basis = size * avg_buy_price
                    proceeds = usd_value - commission
                    realized_pnl += proceeds - cost_basis
            
            total_fees += commission
        
        return {
            'total_trades': len(processed_fills),
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_spent': total_spent,
            'total_received': total_received,
            'total_fees': total_fees,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': 0.0,  # Will be calculated later
            'current_holdings': 0.0,  # Will be calculated later
            'current_value': 0.0,  # Will be calculated later
            'net_pnl': realized_pnl  # Default to realized only
        }
    
    def calculate_unrealized_pnl_by_product(self) -> Dict[str, Dict[str, Any]]:
        """Calculate P&L including unrealized gains/losses from current market prices."""
        try:
            # Get base P&L calculation
            pnl_by_product = self.calculate_pnl_by_product()
            
            # Import here to avoid circular dependency
            from ..services.sync_coordinated_coinbase_service import get_coordinated_coinbase_service
            coinbase_service = get_coordinated_coinbase_service()
            
            # Calculate current holdings and unrealized P&L for each product
            for product_id, data in pnl_by_product.items():
                try:
                    # Calculate net position from trades
                    current_holdings = self._calculate_net_position(product_id)
                    data['current_holdings'] = current_holdings
                    
                    if current_holdings != 0:
                        # Get current market price using cached data
                        market_data_service = MarketDataService()
                        ticker = market_data_service.get_ticker(product_id)
                        if ticker and ticker.price:
                            current_price = float(ticker.price)
                            current_value = abs(current_holdings) * current_price
                            data['current_value'] = current_value
                            data['current_price'] = current_price
                            
                            # Calculate unrealized P&L for open positions
                            if current_holdings > 0:  # Long position
                                # For long positions: current_value - cost_basis_of_remaining_shares
                                avg_buy_price = self._calculate_average_buy_price(product_id)
                                cost_basis = current_holdings * avg_buy_price
                                unrealized_pnl = current_value - cost_basis
                                data['unrealized_pnl'] = unrealized_pnl
                                data['average_buy_price'] = avg_buy_price
                            else:  # Short position (negative holdings)
                                # For short positions: cost_basis_of_short - current_value
                                avg_short_price = self._calculate_average_short_price(product_id)
                                cost_basis = abs(current_holdings) * avg_short_price
                                unrealized_pnl = cost_basis - current_value
                                data['unrealized_pnl'] = unrealized_pnl
                                data['average_short_price'] = avg_short_price
                            
                            # Total P&L = realized + unrealized
                            data['net_pnl'] = data['realized_pnl'] + data['unrealized_pnl']
                        else:
                            logger.warning(f"Could not get current price for {product_id}")
                    
                except Exception as e:
                    logger.error(f"Error calculating unrealized P&L for {product_id}: {e}")
                    # Keep the realized P&L as fallback
                    continue
            
            return pnl_by_product
            
        except Exception as e:
            logger.error(f"Error calculating unrealized P&L by product: {e}")
            return self.calculate_pnl_by_product()  # Fallback to realized only
    
    def _calculate_net_position(self, product_id: str) -> float:
        """Calculate net position (positive = long, negative = short) for a product."""
        try:
            trades = self.get_raw_trades_by_product(product_id)
            net_position = 0.0
            processed_fills = set()  # Track processed fill_ids to avoid duplicates
            
            for trade in trades:
                # Skip duplicate trades by fill_id
                if trade.fill_id in processed_fills:
                    logger.warning(f"Skipping duplicate trade {trade.fill_id}")
                    continue
                processed_fills.add(trade.fill_id)
                
                # CRITICAL FIX: Handle size_in_quote flag like position_tracking_service
                if hasattr(trade, 'size_in_quote') and trade.size_in_quote:
                    # Skip size_in_quote trades due to data corruption issues (from docs)
                    logger.warning(f"Skipping size_in_quote trade {trade.fill_id or 'unknown'} - data validation needed")
                    continue
                
                # When size_in_quote=False, 'size' is already the coin quantity
                size = float(trade.size)
                if trade.side.lower() == 'buy':
                    net_position += size
                elif trade.side.lower() == 'sell':
                    net_position -= size
            
            logger.info(f"Position calculation for {product_id}: {len(processed_fills)} unique trades, net position: {net_position}")
            return net_position
        except Exception as e:
            logger.error(f"Error calculating net position for {product_id}: {e}")
            return 0.0
    
    def _calculate_average_buy_price(self, product_id: str) -> float:
        """Calculate volume-weighted average buy price for a product."""
        try:
            trades = self.get_raw_trades_by_product(product_id)
            total_cost = 0.0
            total_size = 0.0
            processed_fills = set()  # Track processed fill_ids to avoid duplicates
            
            for trade in trades:
                if trade.side.lower() == 'buy':
                    # Skip duplicate trades
                    if trade.fill_id in processed_fills:
                        continue
                    processed_fills.add(trade.fill_id)
                    
                    # CRITICAL FIX: Handle size_in_quote flag properly
                    if hasattr(trade, 'size_in_quote') and trade.size_in_quote:
                        # Skip problematic trades like position_tracking_service
                        logger.warning(f"Skipping size_in_quote BUY trade for average price calculation")
                        continue
                    
                    # When size_in_quote=False, size is in token units
                    size = float(trade.size)
                    price = float(trade.price)
                    total_cost += size * price
                    total_size += size
            
            return total_cost / total_size if total_size > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating average buy price for {product_id}: {e}")
            return 0.0
    
    def _calculate_average_short_price(self, product_id: str) -> float:
        """Calculate volume-weighted average short (sell) price for a product."""
        try:
            trades = self.get_raw_trades_by_product(product_id)
            total_proceeds = 0.0
            total_size = 0.0
            
            for trade in trades:
                if trade.side.lower() == 'sell':
                    # CRITICAL FIX: Handle size_in_quote flag properly
                    if hasattr(trade, 'size_in_quote') and trade.size_in_quote:
                        # Skip problematic trades like position_tracking_service
                        logger.warning(f"Skipping size_in_quote SELL trade for average price calculation")
                        continue
                    
                    # When size_in_quote=False, size is in token units
                    size = float(trade.size)
                    price = float(trade.price)
                    total_proceeds += size * price
                    total_size += size
            
            return total_proceeds / total_size if total_size > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating average short price for {product_id}: {e}")
            return 0.0
    
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
