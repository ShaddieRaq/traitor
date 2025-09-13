"""
Trade utility functions for consistent USD value calculation and P&L.
"""
from typing import Dict, List, Any


def get_trade_usd_value(trade) -> float:
    """
    Get correct USD value for any trade using the size_in_quote flag.
    
    This function respects Coinbase's size_in_quote flag to properly interpret
    the size field, fixing the P&L calculation issues.
    
    Args:
        trade: Trade object with size, price, and size_in_quote fields
        
    Returns:
        float: Correct USD value of the trade
    """
    if not hasattr(trade, 'size') or trade.size is None:
        return 0.0
    
    size = float(trade.size)
    
    # Use size_in_quote flag if available (new trades)
    if hasattr(trade, 'size_in_quote'):
        if trade.size_in_quote:
            # size is already in USD
            return size
        else:
            # size is in crypto units, multiply by price
            if hasattr(trade, 'price') and trade.price:
                return size * float(trade.price)
    
    # Fallback for old trades without size_in_quote field
    # Heuristic: if size is small, it's likely USD; if large, it's crypto units
    if size < 100:  # Likely USD amount
        return size
    else:  # Likely crypto units
        if hasattr(trade, 'price') and trade.price:
            return size * float(trade.price)
    
    return 0.0


def calculate_portfolio_pnl(trades) -> Dict[str, Any]:
    """
    Single P&L calculation method for all trade lists.
    
    Args:
        trades: List of trade objects
        
    Returns:
        Dict with P&L metrics using standardized trade value calculation
    """
    total_buys = 0.0
    total_sells = 0.0
    total_fees = 0.0
    buy_count = 0
    sell_count = 0
    
    for trade in trades:
        trade_value = get_trade_usd_value(trade)
        
        # Get fee (prefer commission over fee field)
        fee = 0.0
        if hasattr(trade, 'commission') and trade.commission:
            fee = float(trade.commission)
        elif hasattr(trade, 'fee') and trade.fee:
            fee = float(trade.fee)
        
        total_fees += fee
        
        if trade.side and trade.side.upper() == 'BUY':
            total_buys += trade_value
            buy_count += 1
        elif trade.side and trade.side.upper() == 'SELL':
            total_sells += trade_value
            sell_count += 1
    
    # Calculate net P&L (sells - buys - fees)
    net_pnl = total_sells - total_buys - total_fees
    total_volume = total_buys + total_sells
    
    return {
        'net_pnl': net_pnl,
        'total_buys': total_buys,
        'total_sells': total_sells,
        'total_fees': total_fees,
        'total_volume': total_volume,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'roi_pct': (net_pnl / total_buys * 100) if total_buys > 0 else 0.0
    }


def validate_trade_data_integrity(trades, known_deposits: float = 600.0) -> Dict[str, Any]:
    """
    Validate trade data for integrity issues.
    
    Args:
        trades: List of trade objects
        known_deposits: Known amount user deposited
        
    Returns:
        Dict with validation results
    """
    pnl_data = calculate_portfolio_pnl(trades)
    
    # Calculate ratios to detect phantom trades
    buy_deposit_ratio = pnl_data['total_buys'] / known_deposits if known_deposits > 0 else 0
    
    # Determine status
    if buy_deposit_ratio > 2.0:  # More than 2x deposits in buys
        status = "SUSPICIOUS"
        action = "DATA_AUDIT_REQUIRED"
    elif buy_deposit_ratio > 1.5:  # 1.5x-2x might be normal with trading
        status = "REVIEW"
        action = "MANUAL_VERIFICATION"
    else:
        status = "OK"
        action = "NONE"
    
    return {
        'total_trades': len(trades),
        'total_buy_volume': pnl_data['total_buys'],
        'total_sell_volume': pnl_data['total_sells'],
        'known_deposits': known_deposits,
        'buy_deposit_ratio': buy_deposit_ratio,
        'integrity_status': status,
        'recommended_action': action,
        'pnl_summary': pnl_data
    }
