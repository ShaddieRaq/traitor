"""
Phase 8.2: Market Selection Learning Service
Automatically pause losing bots and scale winning bots based on P&L performance

Key Features:
- Auto-pause consistently unprofitable bots (major coins)
- Auto-scale consistently profitable bots (alt-coins) 
- Use existing infrastructure for safety and coordination
- Learn market characteristics that drive profitability
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
from ..models.models import Bot, Trade, RawTrade
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class MarketSelectionLearner:
    """
    Service for learning which markets/pairs are profitable and adjusting bot behavior accordingly.
    
    Based on Phase 8 analysis:
    - Alt-coins average +$2.89 profit (AVNT, XAN, USELESS)
    - Major coins average -$4.49 loss (BTC, ETH, SUI, ADA)
    """
    
    def __init__(self):
        # Performance thresholds for market classification
        self.min_profit_threshold = 5.0   # $5+ profit = winner
        self.min_loss_threshold = -10.0   # -$10 loss = loser 
        self.min_trades_required = 10     # Minimum trades for classification
        self.evaluation_period_days = 30  # Look at last 30 days
        
        # Known performance data from Phase 8 analysis
        self.known_winners = {
            'AVNT-USD': 60.31,
            'XAN-USD': 8.11, 
            'USELESS-USD': 3.02
        }
        self.known_losers = {
            'SQD-USD': -25.44,
            'ZORA-USD': -19.28,
            'IP-USD': -9.38
        }
        
    def analyze_market_performance(self, db: Session) -> Dict[str, Any]:
        """
        Analyze all bot performance to classify markets as winners/losers.
        
        Returns:
            Dict with market classifications and recommendations
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'winners': [],
            'losers': [], 
            'neutral': [],
            'recommendations': {},
            'total_bots_analyzed': 0
        }
        
        try:
            # Get all active bots
            bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
            result['total_bots_analyzed'] = len(bots)
            
            for bot in bots:
                performance = self._calculate_bot_performance(bot, db)
                classification = self._classify_market_performance(bot.pair, performance)
                
                bot_data = {
                    'bot_id': bot.id,
                    'pair': bot.pair,
                    'name': bot.name,
                    'total_pnl': performance['total_pnl'],
                    'trade_count': performance['trade_count'],
                    'avg_pnl_per_trade': performance['avg_pnl_per_trade'],
                    'win_rate': performance['win_rate'],
                    'recommendation': classification['recommendation']
                }
                
                if classification['category'] == 'winner':
                    result['winners'].append(bot_data)
                    result['recommendations'][bot.pair] = 'scale_up'
                elif classification['category'] == 'loser':
                    result['losers'].append(bot_data)
                    result['recommendations'][bot.pair] = 'pause'
                else:
                    result['neutral'].append(bot_data)
                    result['recommendations'][bot.pair] = 'monitor'
                    
            # Sort by performance
            result['winners'].sort(key=lambda x: x['total_pnl'], reverse=True)
            result['losers'].sort(key=lambda x: x['total_pnl'])
            
            logger.info(f"📊 Market analysis complete: {len(result['winners'])} winners, {len(result['losers'])} losers")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market performance: {e}")
            result['error'] = str(e)
            return result
    
    def _calculate_bot_performance(self, bot: Bot, db: Session) -> Dict[str, float]:
        """Calculate performance metrics for a bot over the evaluation period."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.evaluation_period_days)
        
        # First try to get performance from known data
        if bot.pair in self.known_winners:
            return {
                'total_pnl': self.known_winners[bot.pair],
                'trade_count': 50,  # Estimated
                'avg_pnl_per_trade': self.known_winners[bot.pair] / 50,
                'win_rate': 0.65,  # Estimated
                'data_source': 'known_winner'
            }
        elif bot.pair in self.known_losers:
            return {
                'total_pnl': self.known_losers[bot.pair],
                'trade_count': 30,  # Estimated
                'avg_pnl_per_trade': self.known_losers[bot.pair] / 30,
                'win_rate': 0.35,  # Estimated
                'data_source': 'known_loser'
            }
        
        # For other bots, try to calculate from trade data
        try:
            trades = db.query(Trade).filter(
                and_(
                    Trade.bot_id == bot.id,
                    Trade.status.in_(['filled', 'completed']),
                    Trade.filled_at >= cutoff_date
                )
            ).all()
            
            if not trades:
                return {
                    'total_pnl': 0.0,
                    'trade_count': 0,
                    'avg_pnl_per_trade': 0.0,
                    'win_rate': 0.0,
                    'data_source': 'no_trades'
                }
            
            total_pnl = sum(trade.pnl_usd or 0.0 for trade in trades)
            trade_count = len(trades)
            winning_trades = sum(1 for trade in trades if (trade.pnl_usd or 0) > 0)
            
            return {
                'total_pnl': total_pnl,
                'trade_count': trade_count,
                'avg_pnl_per_trade': total_pnl / trade_count if trade_count > 0 else 0.0,
                'win_rate': winning_trades / trade_count if trade_count > 0 else 0.0,
                'data_source': 'calculated'
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance for bot {bot.id}: {e}")
            return {
                'total_pnl': 0.0,
                'trade_count': 0,
                'avg_pnl_per_trade': 0.0,
                'win_rate': 0.0,
                'data_source': 'error'
            }
    
    def _classify_market_performance(self, pair: str, performance: Dict[str, float]) -> Dict[str, str]:
        """Classify a market as winner, loser, or neutral based on performance."""
        total_pnl = performance['total_pnl']
        trade_count = performance['trade_count']
        
        if trade_count < self.min_trades_required and pair not in {**self.known_winners, **self.known_losers}:
            return {
                'category': 'neutral',
                'reason': f'Insufficient data ({trade_count} trades)',
                'recommendation': 'Continue monitoring - need more trade data'
            }
        
        if total_pnl >= self.min_profit_threshold:
            return {
                'category': 'winner',
                'reason': f'Profitable: ${total_pnl:.2f}',
                'recommendation': 'Scale up position sizes and increase trading frequency'
            }
        elif total_pnl <= self.min_loss_threshold:
            return {
                'category': 'loser', 
                'reason': f'Losing: ${total_pnl:.2f}',
                'recommendation': 'Pause bot to prevent further losses'
            }
        else:
            return {
                'category': 'neutral',
                'reason': f'Neutral: ${total_pnl:.2f}',
                'recommendation': 'Monitor performance - within acceptable range'
            }
    
    def auto_pause_losers(self, db: Session, dry_run: bool = True) -> Dict[str, Any]:
        """
        Automatically pause bots that are consistently losing money.
        
        Args:
            db: Database session
            dry_run: If True, only simulate the action without actually pausing
            
        Returns:
            Dict with pause results
        """
        result = {
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'bots_paused': [],
            'bots_skipped': [],
            'total_loss_prevented': 0.0
        }
        
        try:
            analysis = self.analyze_market_performance(db)
            
            for loser in analysis['losers']:
                bot_id = loser['bot_id']
                pair = loser['pair']
                total_pnl = loser['total_pnl']
                
                # Safety check - only pause if significant losses
                if total_pnl <= self.min_loss_threshold:
                    if not dry_run:
                        # Actually pause the bot
                        bot = db.query(Bot).filter(Bot.id == bot_id).first()
                        if bot and bot.status == 'RUNNING':
                            bot.status = 'STOPPED'
                            bot.auto_paused_at = datetime.utcnow()
                            bot.auto_pause_reason = f'Market selection learning: ${total_pnl:.2f} loss'
                            db.commit()
                            
                            logger.info(f"🛑 Auto-paused bot {bot_id} ({pair}): ${total_pnl:.2f} loss")
                    
                    result['bots_paused'].append({
                        'bot_id': bot_id,
                        'pair': pair,
                        'total_pnl': total_pnl,
                        'action': 'paused' if not dry_run else 'would_pause'
                    })
                    result['total_loss_prevented'] += abs(total_pnl)
                else:
                    result['bots_skipped'].append({
                        'bot_id': bot_id,
                        'pair': pair,
                        'total_pnl': total_pnl,
                        'reason': 'Loss not significant enough'
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto_pause_losers: {e}")
            result['error'] = str(e)
            return result
    
    def auto_scale_winners(self, db: Session, dry_run: bool = True) -> Dict[str, Any]:
        """
        Automatically scale up bots that are consistently profitable.
        
        This would integrate with existing position sizing engine.
        """
        result = {
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'bots_scaled': [],
            'total_profit_potential': 0.0,
            'message': 'Auto-scaling integration with position sizing engine needed'
        }
        
        try:
            analysis = self.analyze_market_performance(db)
            
            for winner in analysis['winners']:
                bot_id = winner['bot_id']
                pair = winner['pair'] 
                total_pnl = winner['total_pnl']
                
                if total_pnl >= self.min_profit_threshold:
                    # For now, just identify profitable bots
                    # Future: Integrate with position sizing engine
                    result['bots_scaled'].append({
                        'bot_id': bot_id,
                        'pair': pair,
                        'total_pnl': total_pnl,
                        'suggested_action': 'increase_position_size',
                        'current_size': '10.0',  # Would get from bot config
                        'suggested_size': '15.0'  # 50% increase for profitable bots
                    })
                    result['total_profit_potential'] += total_pnl
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto_scale_winners: {e}")
            result['error'] = str(e)
            return result


# Global instance
_market_selection_learner = None

def get_market_selection_learner() -> MarketSelectionLearner:
    """Get global market selection learner instance."""
    global _market_selection_learner
    if _market_selection_learner is None:
        _market_selection_learner = MarketSelectionLearner()
    return _market_selection_learner