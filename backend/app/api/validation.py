"""
Data validation endpoints for P&L accuracy verification
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.models import Trade
from ..utils.trade_utils import get_trade_usd_value
from ..services.coinbase_service import CoinbaseService
from ..models.models import Trade

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/validate-pnl")
async def validate_pnl_calculations(db: Session = Depends(get_db)):
    """
    Comprehensive P&L validation comparing multiple calculation methods
    """
    try:
        coinbase_service = CoinbaseService()
        
        # Method 1: Direct database calculation using size_usd field only
        db_query = text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN LOWER(side) = 'buy' THEN 1 END) as buy_trades,
                COUNT(CASE WHEN LOWER(side) = 'sell' THEN 1 END) as sell_trades,
                SUM(CASE WHEN LOWER(side) = 'buy' THEN size_usd ELSE 0 END) as total_spent,
                SUM(CASE WHEN LOWER(side) = 'sell' THEN size_usd ELSE 0 END) as total_received,
                SUM(CASE WHEN LOWER(side) = 'sell' THEN size_usd ELSE -size_usd END) as net_pnl,
                SUM(fee) as total_fees,
                MIN(created_at) as first_trade,
                MAX(created_at) as last_trade,
                COUNT(CASE WHEN order_id IS NOT NULL AND order_id != '' THEN 1 END) as trades_with_order_id
            FROM trades 
            WHERE order_id IS NOT NULL AND order_id != ''
        """)
        
        db_result = db.execute(db_query).fetchone()
        
        # Method 2: Current API calculation (from profitability endpoint)
        api_result = None
        try:
            # Get current P&L API response for comparison
            from ..api.trades import calculate_profitability_data
            api_result = calculate_profitability_data(db)
        except Exception as e:
            logger.error(f"Error getting API result: {e}")
        
        # Method 3: Coinbase balance validation
        coinbase_balances = None
        try:
            accounts = coinbase_service.get_accounts()
            usd_balance = 0
            crypto_value = 0
            
            for account in accounts:
                if account.get('currency') == 'USD':
                    usd_balance = float(account.get('available_balance', 0))
                else:
                    crypto_value += float(account.get('available_balance_fiat', 0))
            
            coinbase_balances = {
                'usd_balance': usd_balance,
                'crypto_value': crypto_value,
                'portfolio_total': usd_balance + crypto_value
            }
        except Exception as e:
            logger.error(f"Error getting Coinbase balances: {e}")
            coinbase_balances = {'error': str(e)}
        
        # Data integrity checks
        integrity_checks = {
            'all_trades_have_order_id': db_result.trades_with_order_id == db_result.total_trades,
            'buy_sell_total_matches': (db_result.buy_trades + db_result.sell_trades) == db_result.total_trades,
            'reasonable_pnl_range': -200000 <= db_result.net_pnl <= 200000,  # Sanity check
            'reasonable_trade_count': 1000 <= db_result.total_trades <= 10000,  # Expected range
            'recent_activity': db_result.last_trade and 
                             (datetime.fromisoformat(db_result.last_trade.replace('Z', '+00:00')) > 
                              datetime.now().replace(tzinfo=None) - timedelta(days=7))
        }
        
        # Calculate discrepancies if API data available
        discrepancies = {}
        if api_result:
            discrepancies = {
                'trade_count_diff': abs(db_result.total_trades - api_result.get('total_trades', 0)),
                'pnl_diff': abs(db_result.net_pnl - api_result.get('net_pnl', 0)),
                'volume_diff': abs((db_result.total_spent + db_result.total_received) - 
                                 api_result.get('total_volume_usd', 0))
            }
        
        return {
            'validation_timestamp': datetime.now().isoformat(),
            'database_calculation': {
                'total_trades': int(db_result.total_trades),
                'buy_trades': int(db_result.buy_trades),
                'sell_trades': int(db_result.sell_trades),
                'total_spent': float(db_result.total_spent),
                'total_received': float(db_result.total_received),
                'net_pnl': float(db_result.net_pnl),
                'total_fees': float(db_result.total_fees or 0),
                'first_trade': db_result.first_trade,
                'last_trade': db_result.last_trade,
                'trades_with_order_id': int(db_result.trades_with_order_id)
            },
            'api_calculation': api_result,
            'coinbase_balances': coinbase_balances,
            'integrity_checks': integrity_checks,
            'discrepancies': discrepancies,
            'validation_summary': {
                'data_integrity': all(integrity_checks.values()),
                'calculation_accuracy': all(abs(diff) < 0.01 for diff in discrepancies.values()) if discrepancies else None,
                'coinbase_sync': coinbase_balances and 'error' not in coinbase_balances
            }
        }
        
    except Exception as e:
        logger.error(f"P&L validation error: {e}")
        return {
            'error': str(e),
            'validation_timestamp': datetime.now().isoformat(),
            'status': 'failed'
        }

@router.get("/validate-recent-trades")
async def validate_recent_trades(db: Session = Depends(get_db), limit: int = 20):
    """
    Validate recent trades for data consistency
    """
    try:
        recent_trades_query = text("""
            SELECT 
                id, bot_id, product_id, side, size, price, fee, order_id, status,
                created_at, filled_at, COALESCE(size_usd, size * price) as trade_value
            FROM trades 
            WHERE order_id IS NOT NULL AND order_id != ''
            ORDER BY created_at DESC 
            LIMIT :limit
        """)
        
        trades = db.execute(recent_trades_query, {'limit': limit}).fetchall()
        
        validation_results = []
        total_value = 0
        
        for trade in trades:
            trade_dict = dict(trade._mapping)
            
            # Validate each trade
            validation = {
                'trade_id': trade_dict['id'],
                'order_id': trade_dict['order_id'],
                'has_order_id': bool(trade_dict['order_id']),
                'has_reasonable_size': 0.0001 <= float(trade_dict['size']) <= 10.0,
                'has_reasonable_price': 100 <= float(trade_dict['price']) <= 100000,
                'has_valid_side': trade_dict['side'].lower() in ['buy', 'sell'],
                'trade_value': float(trade_dict['trade_value']),
                'created_at': trade_dict['created_at']
            }
            
            total_value += validation['trade_value']
            validation_results.append(validation)
        
        return {
            'validation_timestamp': datetime.now().isoformat(),
            'trades_validated': len(validation_results),
            'total_recent_value': total_value,
            'all_valid': all(
                trade['has_order_id'] and 
                trade['has_reasonable_size'] and 
                trade['has_reasonable_price'] and 
                trade['has_valid_side']
                for trade in validation_results
            ),
            'trade_details': validation_results
        }
        
    except Exception as e:
        logger.error(f"Recent trades validation error: {e}")
        return {
            'error': str(e),
            'validation_timestamp': datetime.now().isoformat(),
            'status': 'failed'
        }
