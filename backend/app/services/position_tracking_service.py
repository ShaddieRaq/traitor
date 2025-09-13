"""
Position Tracking Service - Proper position and P&L calculation
Tracks actual positions and calculates realistic P&L using FIFO method.
"""

import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import SessionLocal
from app.models.models import RawTrade

logger = logging.getLogger(__name__)

@dataclass
class PositionLot:
    """Represents a lot/parcel of a position (from a single buy)"""
    quantity: Decimal
    cost_basis: Decimal  # Price paid per unit
    purchase_date: datetime
    fill_id: str

@dataclass
class Position:
    """Current position for a trading pair"""
    product_id: str
    total_quantity: Decimal
    lots: List[PositionLot]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_fees: Decimal
    
    @property
    def average_cost_basis(self) -> Decimal:
        if not self.lots or self.total_quantity == 0:
            return Decimal('0')
        total_cost = sum(lot.quantity * lot.cost_basis for lot in self.lots)
        return total_cost / self.total_quantity

@dataclass
class PositionSummary:
    """Summary view for UI display"""
    product_id: str
    current_quantity: Decimal
    average_cost_basis: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    total_fees: Decimal
    trade_count: int
    buy_count: int
    sell_count: int

class PositionTrackingService:
    """Service for tracking positions and calculating realistic P&L"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def calculate_positions(self) -> Dict[str, Position]:
        """Calculate current positions for all trading pairs"""
        try:
            # Get all trades ordered by time (oldest first for FIFO)
            trades = self.db.query(RawTrade).order_by(RawTrade.created_at).all()
            
            positions = {}
            
            for trade in trades:
                product_id = trade.product_id
                
                if product_id not in positions:
                    positions[product_id] = Position(
                        product_id=product_id,
                        total_quantity=Decimal('0'),
                        lots=[],
                        realized_pnl=Decimal('0'),
                        unrealized_pnl=Decimal('0'),
                        total_fees=Decimal('0')
                    )
                
                position = positions[product_id]
                price = Decimal(str(trade.price))
                commission = Decimal(str(trade.commission or 0))
                
                # Handle size_in_quote flag properly  
                if trade.size_in_quote:
                    # Skip size_in_quote trades for now due to data corruption issues
                    logger.warning(f"Skipping size_in_quote trade {trade.fill_id} - data validation needed")
                    continue
                else:
                    # When size_in_quote=False, 'size' is already the coin quantity
                    quantity = Decimal(str(trade.size))
                
                position.total_fees += commission
                
                if trade.side.upper() == 'BUY':
                    self._process_buy(position, quantity, price, trade.created_at, trade.fill_id)
                elif trade.side.upper() == 'SELL':
                    self._process_sell(position, quantity, price)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error calculating positions: {e}")
            return {}
    
    def _process_buy(self, position: Position, quantity: Decimal, price: Decimal, 
                    purchase_date: datetime, fill_id: str):
        """Process a buy order - add to position"""
        lot = PositionLot(
            quantity=quantity,
            cost_basis=price,
            purchase_date=purchase_date,
            fill_id=fill_id
        )
        position.lots.append(lot)
        position.total_quantity += quantity
    
    def _process_sell(self, position: Position, quantity: Decimal, sell_price: Decimal):
        """Process a sell order - reduce position using FIFO and calculate realized P&L"""
        remaining_to_sell = quantity
        
        while remaining_to_sell > 0 and position.lots:
            lot = position.lots[0]  # FIFO - oldest first
            
            if lot.quantity <= remaining_to_sell:
                # Sell entire lot
                sell_quantity = lot.quantity
                position.lots.pop(0)
            else:
                # Partial sell of lot
                sell_quantity = remaining_to_sell
                lot.quantity -= sell_quantity
            
            # Calculate realized P&L for this portion
            cost = sell_quantity * lot.cost_basis
            proceeds = sell_quantity * sell_price
            realized_gain = proceeds - cost
            position.realized_pnl += realized_gain
            
            position.total_quantity -= sell_quantity
            remaining_to_sell -= sell_quantity
        
        if remaining_to_sell > 0:
            # Selling more than we own - this is a short position or error
            logger.warning(f"Short selling detected for {position.product_id}: "
                         f"Sold {remaining_to_sell} more than owned")
    
    def get_position_summaries(self) -> List[PositionSummary]:
        """Get position summaries for UI display"""
        positions = self.calculate_positions()
        summaries = []
        
        for product_id, position in positions.items():
            # Get trade counts
            trades = self.db.query(RawTrade).filter(
                RawTrade.product_id == product_id
            ).all()
            
            buy_count = sum(1 for t in trades if t.side.upper() == 'BUY')
            sell_count = sum(1 for t in trades if t.side.upper() == 'SELL')
            
            summary = PositionSummary(
                product_id=product_id,
                current_quantity=position.total_quantity,
                average_cost_basis=position.average_cost_basis,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=position.unrealized_pnl,
                total_pnl=position.realized_pnl + position.unrealized_pnl,
                total_fees=position.total_fees,
                trade_count=len(trades),
                buy_count=buy_count,
                sell_count=sell_count
            )
            summaries.append(summary)
        
        return summaries
    
    def get_position_by_product(self, product_id: str) -> Optional[Position]:
        """Get position for a specific trading pair"""
        positions = self.calculate_positions()
        return positions.get(product_id)
    
    def calculate_unrealized_pnl(self, current_prices: Dict[str, Decimal]) -> Dict[str, Position]:
        """Calculate unrealized P&L using current market prices"""
        positions = self.calculate_positions()
        
        for product_id, position in positions.items():
            if product_id in current_prices and position.total_quantity > 0:
                current_price = current_prices[product_id]
                current_value = position.total_quantity * current_price
                cost_value = position.total_quantity * position.average_cost_basis
                position.unrealized_pnl = current_value - cost_value
        
        return positions
