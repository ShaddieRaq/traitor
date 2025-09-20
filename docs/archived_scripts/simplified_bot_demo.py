"""
Bot Configuration for Raw Trades System
=======================================

This script demonstrates how to configure trading bots to use the new raw_trades 
table exclusively, without any dependency on the old corrupted trades table.

Key Changes:
1. Bots no longer track which specific trades they made
2. P&L is calculated from clean Coinbase data in raw_trades table
3. Position management uses real-time balance checks instead of trade history
4. Simplified architecture without metadata tracking
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from app.services.raw_trade_service import RawTradeService
from app.services.coinbase_service import CoinbaseService
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SimplifiedBot:
    """
    Simplified bot that uses only raw_trades data.
    No bot metadata tracking - just clean trade execution.
    """
    
    def __init__(self, bot_config: Dict[str, Any]):
        self.config = bot_config
        self.db = SessionLocal()
        self.raw_trade_service = RawTradeService(self.db)
        self.coinbase_service = CoinbaseService()
    
    def execute_trade(self, product_id: str, side: str, size_usd: float) -> Dict[str, Any]:
        """
        Execute a trade using only clean systems.
        No trade metadata tracking - just place order and let sync handle the rest.
        """
        try:
            logger.info(f"🚀 Executing {side} ${size_usd} {product_id}")
            
            # 1. Validate balance (using real-time Coinbase data)
            validation = self._validate_trade_balance(product_id, side, size_usd)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': validation['message'],
                    'balance_issue': True
                }
            
            # 2. Place order with Coinbase (no local tracking)
            order_result = self.coinbase_service.place_market_order(
                product_id=product_id,
                side=side.lower(),
                size=self._calculate_base_size(product_id, side, size_usd)
            )
            
            if not order_result:
                return {
                    'success': False,
                    'message': 'Order placement failed',
                    'coinbase_error': True
                }
            
            # 3. Let the background sync process handle recording
            # No immediate database writes - sync_raw_coinbase.py will handle it
            logger.info(f"✅ Order placed: {order_result['order_id']}")
            
            return {
                'success': True,
                'order_id': order_result['order_id'],
                'message': f'{side} order placed successfully',
                'sync_note': 'Trade will be recorded by background sync process'
            }
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return {
                'success': False,
                'message': f'Trade execution error: {str(e)}',
                'exception': True
            }
    
    def get_performance_metrics(self, product_id: str = None) -> Dict[str, Any]:
        """
        Get performance metrics using only clean raw_trades data.
        No bot-specific filtering - just overall portfolio performance.
        """
        try:
            if product_id:
                # Get metrics for specific product
                pnl_data = self.raw_trade_service.calculate_pnl_by_product()
                if product_id not in pnl_data:
                    return {
                        'product_id': product_id,
                        'total_trades': 0,
                        'net_pnl': 0.0,
                        'message': 'No trades found for this product'
                    }
                
                data = pnl_data[product_id]
                return {
                    'product_id': product_id,
                    'total_trades': data['total_trades'],
                    'buy_trades': data['buy_trades'],
                    'sell_trades': data['sell_trades'],
                    'net_pnl': data['net_pnl'],
                    'total_volume': data['total_spent'] + data['total_received'],
                    'total_fees': data['total_fees']
                }
            else:
                # Get overall portfolio metrics
                stats = self.raw_trade_service.get_trading_stats()
                return {
                    'portfolio_performance': stats,
                    'message': 'Overall portfolio metrics from clean data'
                }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def _validate_trade_balance(self, product_id: str, side: str, size_usd: float) -> Dict[str, Any]:
        """Validate balance using real-time Coinbase data."""
        try:
            current_price = self._get_current_price(product_id)
            return self.coinbase_service.validate_trade_balance(
                product_id, side, size_usd, current_price
            )
        except Exception as e:
            return {
                'valid': False,
                'message': f'Balance validation error: {str(e)}'
            }
    
    def _calculate_base_size(self, product_id: str, side: str, size_usd: float) -> float:
        """Calculate base currency size for the order."""
        try:
            current_price = self._get_current_price(product_id)
            if side.upper() == 'BUY':
                # For buy orders, convert USD to base currency
                return size_usd / current_price
            else:
                # For sell orders, we need the base currency amount
                # This would typically come from balance check
                base_currency = product_id.split('-')[0]
                available_balance = self.coinbase_service.get_available_balance(base_currency)
                
                # Sell up to the requested USD value, but not more than available
                max_sellable_usd = available_balance * current_price
                actual_size_usd = min(size_usd, max_sellable_usd)
                return actual_size_usd / current_price
                
        except Exception as e:
            logger.error(f"Error calculating base size: {e}")
            return 0.0
    
    def _get_current_price(self, product_id: str) -> float:
        """Get current market price."""
        try:
            ticker = self.coinbase_service.get_product_ticker(product_id)
            return float(ticker['price']) if ticker else 0.0
        except Exception:
            return 0.0


def demo_simplified_bot_usage():
    """
    Demonstration of simplified bot usage without trade table dependency.
    """
    print("🤖 Simplified Bot Configuration Demo")
    print("=" * 50)
    
    # Create simplified bot configuration
    bot_config = {
        'name': 'Clean Data Bot',
        'product_id': 'BTC-USD',
        'trade_size_usd': 10.0,
        'description': 'Uses only clean raw_trades data'
    }
    
    # Initialize bot
    bot = SimplifiedBot(bot_config)
    
    # Demo 1: Get current performance metrics
    print("\n📊 Current Performance Metrics:")
    performance = bot.get_performance_metrics('BTC-USD')
    print(f"BTC-USD Performance: {performance}")
    
    # Demo 2: Portfolio overview
    print("\n💼 Portfolio Overview:")
    portfolio = bot.get_performance_metrics()
    print(f"Portfolio Stats: {portfolio}")
    
    # Demo 3: Show how trade execution would work (simulation)
    print("\n🚀 Trade Execution Simulation:")
    print("Note: This would place a real order if executed")
    
    # Simulated trade parameters
    trade_params = {
        'product_id': 'BTC-USD',
        'side': 'BUY',
        'size_usd': 10.0
    }
    
    print(f"Would execute: {trade_params}")
    print("✅ Order would be placed and recorded automatically by sync process")
    
    print("\n🎯 Key Benefits of Simplified Architecture:")
    print("- No corrupted data dependencies")
    print("- Real-time balance validation")
    print("- Clean P&L calculations")
    print("- Automatic background sync")
    print("- Simplified bot configuration")
    
    print("\n📋 Next Steps:")
    print("1. Update existing bots to use SimplifiedBot class")
    print("2. Remove dependencies on trades table")
    print("3. Test with small trade amounts")
    print("4. Monitor background sync performance")


if __name__ == "__main__":
    demo_simplified_bot_usage()
