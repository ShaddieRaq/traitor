"""
Correct P&L Calculation using FIFO accounting
"""

from typing import List, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def calculate_realized_pnl_fifo(trades: List[Any]) -> float:
    """
    Calculate realized P&L using FIFO (First In, First Out) matching of buy/sell orders.
    
    This is the correct way to calculate realized gains/losses - only when you actually
    sell assets do you realize a gain or loss.
    
    Args:
        trades: List of trade objects with side, size, price, created_at
        
    Returns:
        float: Realized P&L from completed buy->sell cycles only
    """
    from .trade_utils import get_trade_usd_value
    
    buy_queue = []  # FIFO queue of buy orders
    realized_pnl = 0.0
    
    # Sort trades by creation time to process in chronological order
    sorted_trades = sorted(trades, key=lambda t: t.created_at)
    
    for trade in sorted_trades:
        if trade.side.upper() == 'BUY':
            # Add to buy queue
            buy_queue.append({
                'size': float(trade.size),
                'price': float(trade.price),
                'value': get_trade_usd_value(trade),
                'trade_id': trade.id
            })
            
        elif trade.side.upper() == 'SELL':
            sell_size = float(trade.size)
            sell_price = float(trade.price)
            
            # Match against buy orders (FIFO)
            while sell_size > 0 and buy_queue:
                buy_order = buy_queue[0]
                
                if buy_order['size'] <= sell_size:
                    # Sell entire buy order (complete match)
                    proceeds = buy_order['size'] * sell_price
                    cost = buy_order['value']
                    cycle_pnl = proceeds - cost
                    realized_pnl += cycle_pnl
                    
                    logger.debug(f"Complete cycle: sold {buy_order['size']} @ ${sell_price} "
                               f"(cost ${buy_order['price']}) = ${cycle_pnl:.2f}")
                    
                    sell_size -= buy_order['size']
                    buy_queue.pop(0)
                    
                else:
                    # Partial sell (sell less than buy order size)
                    proceeds = sell_size * sell_price
                    cost = sell_size * buy_order['price']
                    cycle_pnl = proceeds - cost
                    realized_pnl += cycle_pnl
                    
                    logger.debug(f"Partial cycle: sold {sell_size} @ ${sell_price} "
                               f"(cost ${buy_order['price']}) = ${cycle_pnl:.2f}")
                    
                    # Update remaining buy order
                    buy_order['size'] -= sell_size
                    buy_order['value'] -= cost
                    sell_size = 0
    
    return realized_pnl

def calculate_unrealized_pnl(trades: List[Any], current_price: float) -> Dict[str, float]:
    """
    Calculate unrealized P&L for remaining open position.
    
    Args:
        trades: List of trade objects
        current_price: Current market price
        
    Returns:
        Dict with unrealized_pnl, current_position, average_cost_basis
    """
    from .trade_utils import get_trade_usd_value
    
    # Calculate net position
    total_bought = 0.0
    total_sold = 0.0
    total_buy_cost = 0.0
    
    for trade in trades:
        if trade.side.upper() == 'BUY':
            total_bought += float(trade.size)
            total_buy_cost += get_trade_usd_value(trade)
        elif trade.side.upper() == 'SELL':
            total_sold += float(trade.size)
    
    current_position = total_bought - total_sold
    
    if current_position <= 0:
        return {
            'unrealized_pnl': 0.0,
            'current_position': 0.0,
            'average_cost_basis': 0.0
        }
    
    # Calculate average cost basis for remaining position
    average_cost_basis = (total_buy_cost / total_bought) if total_bought > 0 else 0.0
    
    # Calculate unrealized P&L
    current_value = current_position * current_price
    cost_basis = current_position * average_cost_basis
    unrealized_pnl = current_value - cost_basis
    
    return {
        'unrealized_pnl': unrealized_pnl,
        'current_position': current_position,
        'average_cost_basis': average_cost_basis
    }

def calculate_correct_pnl(trades: List[Any], current_price: float) -> Dict[str, float]:
    """
    Calculate both realized and unrealized P&L correctly.
    
    Returns:
        Dict with realized_pnl, unrealized_pnl, total_pnl, current_position, etc.
    """
    realized_pnl = calculate_realized_pnl_fifo(trades)
    unrealized_data = calculate_unrealized_pnl(trades, current_price)
    
    return {
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_data['unrealized_pnl'],
        'total_pnl': realized_pnl + unrealized_data['unrealized_pnl'],
        'current_position': unrealized_data['current_position'],
        'average_cost_basis': unrealized_data['average_cost_basis']
    }
