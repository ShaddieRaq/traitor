#!/usr/bin/env python3
"""
Universal Learning System: Apply profit-focused learning to ALL bots
Based on real-time P&L performance data instead of hardcoded bot list
"""

import sys
sys.path.append('/Users/lazy_genius/Projects/trader/backend')

import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from app.core.database import SessionLocal
from app.models.models import Bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_pnl_data() -> Dict[str, float]:
    """Fetch real-time P&L data for all trading pairs"""
    try:
        response = requests.get("http://localhost:8000/api/v1/raw-trades/pnl-by-product", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return {item['product_id']: item['net_pnl_usd'] for item in data.get('products', [])}
        else:
            logger.error(f"Failed to fetch P&L data: {response.status_code}")
            return {}
    except requests.exceptions.Timeout:
        logger.warning("P&L API timeout - using fallback strategy")
        # Fallback: Apply learning to all bots with neutral strategy
        return get_fallback_pnl_data()
    except Exception as e:
        logger.error(f"Error fetching P&L data: {e}")
        return get_fallback_pnl_data()

def get_fallback_pnl_data() -> Dict[str, float]:
    """Fallback P&L data when API is unavailable"""
    logger.info("🔄 Using fallback strategy - applying gentle learning to all bots")
    # Get all bot pairs from the database
    session = SessionLocal()
    try:
        bots = session.query(Bot).filter(Bot.status == 'RUNNING').all()
        # Return neutral P&L (0.0) for all bots to trigger gentle optimization
        return {bot.pair: 0.0 for bot in bots}
    except Exception as e:
        logger.error(f"Error getting bot pairs: {e}")
        return {}
    finally:
        session.close()

def categorize_bot_performance(pnl: float) -> str:
    """Categorize bot performance based on P&L"""
    if pnl < -10:
        return "major_loser"      # Significant losses - aggressive rebalancing
    elif pnl < -2:
        return "minor_loser"      # Small losses - moderate adjustments
    elif pnl < 2:
        return "neutral"          # Break-even - gentle optimization
    elif pnl < 10:
        return "minor_winner"     # Small profits - optimize winning signals
    else:
        return "major_winner"     # Significant profits - fine-tune only

def determine_learning_strategy(category: str) -> str:
    """Map performance category to learning strategy"""
    strategy_map = {
        "major_loser": "aggressive_rebalance",
        "minor_loser": "moderate_rebalance", 
        "neutral": "gentle_optimization",
        "minor_winner": "optimize_winner",
        "major_winner": "fine_tune"
    }
    return strategy_map.get(category, "maintain")

def apply_universal_learning_strategy(signal_config: Dict, strategy: str, pnl: float) -> Tuple[Dict, str]:
    """Apply learning adjustments based on performance category"""
    changes = []
    
    if strategy == "aggressive_rebalance":
        # Major losers: Dramatic signal rebalancing
        if 'rsi' in signal_config and signal_config['rsi']:
            old_weight = signal_config['rsi'].get('weight', 0.4)
            new_weight = max(0.1, old_weight - 0.2)  # Aggressive RSI reduction
            signal_config['rsi']['weight'] = new_weight
            changes.append(f"RSI: {old_weight:.1%} → {new_weight:.1%}")
        
        if 'moving_average' in signal_config and signal_config['moving_average']:
            old_weight = signal_config['moving_average'].get('weight', 0.35)
            new_weight = min(0.7, old_weight + 0.2)  # Aggressive MA boost
            signal_config['moving_average']['weight'] = new_weight
            changes.append(f"MA: {old_weight:.1%} → {new_weight:.1%}")
            
    elif strategy == "moderate_rebalance":
        # Minor losers: Moderate adjustments
        if 'rsi' in signal_config and signal_config['rsi']:
            old_weight = signal_config['rsi'].get('weight', 0.4)
            new_weight = max(0.2, old_weight - 0.1)
            signal_config['rsi']['weight'] = new_weight
            changes.append(f"RSI: {old_weight:.1%} → {new_weight:.1%}")
        
        if 'macd' in signal_config and signal_config['macd']:
            old_weight = signal_config['macd'].get('weight', 0.25)
            new_weight = min(0.4, old_weight + 0.1)
            signal_config['macd']['weight'] = new_weight
            changes.append(f"MACD: {old_weight:.1%} → {new_weight:.1%}")
            
    elif strategy == "gentle_optimization":
        # Neutral bots: Small optimizations
        if 'moving_average' in signal_config and signal_config['moving_average']:
            old_weight = signal_config['moving_average'].get('weight', 0.35)
            new_weight = min(0.4, old_weight + 0.03)
            signal_config['moving_average']['weight'] = new_weight
            changes.append(f"MA: {old_weight:.1%} → {new_weight:.1%} (gentle)")
            
    elif strategy == "optimize_winner":
        # Minor winners: Enhance successful patterns
        if 'moving_average' in signal_config and signal_config['moving_average']:
            old_weight = signal_config['moving_average'].get('weight', 0.35)
            new_weight = min(0.45, old_weight + 0.05)
            signal_config['moving_average']['weight'] = new_weight
            changes.append(f"MA: {old_weight:.1%} → {new_weight:.1%} (winner boost)")
            
    elif strategy == "fine_tune":
        # Major winners: Minimal adjustments to preserve success
        if 'rsi' in signal_config and signal_config['rsi']:
            old_weight = signal_config['rsi'].get('weight', 0.4)
            new_weight = min(0.45, old_weight + 0.02)
            signal_config['rsi']['weight'] = new_weight
            changes.append(f"RSI: {old_weight:.1%} → {new_weight:.1%} (fine-tune)")
    else:
        changes = ["No changes - maintaining current configuration"]
    
    return signal_config, "; ".join(changes)

def normalize_weights(signal_config: Dict) -> Dict:
    """Normalize all signal weights to sum to 1.0"""
    # Get all enabled signal configs
    enabled_signals = {}
    for signal_name, config in signal_config.items():
        if (config and isinstance(config, dict) and 
            config.get('enabled', False) and 'weight' in config):
            enabled_signals[signal_name] = config
    
    if not enabled_signals:
        return signal_config
    
    # Calculate total weight
    total_weight = sum(config['weight'] for config in enabled_signals.values())
    
    if total_weight > 0:
        # Normalize weights to sum to 1.0
        for signal_name, config in enabled_signals.items():
            config['weight'] = config['weight'] / total_weight
    
    return signal_config

def apply_learning_to_all_bots():
    """Apply learning system to all 45 bots based on their P&L performance"""
    
    # Fetch real-time P&L data
    logger.info("🔍 Fetching real-time P&L data for all trading pairs...")
    pnl_data = fetch_all_pnl_data()
    
    if not pnl_data:
        logger.error("❌ No P&L data available and fallback failed - cannot proceed with learning")
        return
    
    logger.info(f"📊 Retrieved P&L data for {len(pnl_data)} trading pairs")
    
    # Get database session
    session = SessionLocal()
    
    try:
        # Get all active bots
        bots = session.query(Bot).filter(Bot.status == 'RUNNING').all()
        logger.info(f"🤖 Processing {len(bots)} running bots for learning optimization")
        
        learning_applied = 0
        performance_categories = {"major_loser": 0, "minor_loser": 0, "neutral": 0, "minor_winner": 0, "major_winner": 0}
        
        for bot in bots:
            # Get P&L for this bot's trading pair
            bot_pnl = pnl_data.get(bot.pair, 0.0)
            
            # Categorize performance
            category = categorize_bot_performance(bot_pnl)
            strategy = determine_learning_strategy(category)
            performance_categories[category] += 1
            
            # Parse current signal config
            current_config = json.loads(bot.signal_config) if bot.signal_config else {}
            
            # Apply learning strategy
            updated_config, changes = apply_universal_learning_strategy(current_config.copy(), strategy, bot_pnl)
            
            # Normalize weights
            updated_config = normalize_weights(updated_config)
            
            # Update bot configuration
            bot.signal_config = json.dumps(updated_config)
            bot.updated_at = datetime.utcnow()
            
            logger.info(f"🧠 {bot.pair}: ${bot_pnl:+.2f} ({category}) → {strategy}")
            logger.info(f"   Changes: {changes}")
            
            learning_applied += 1
        
        # Commit all changes
        session.commit()
        
        logger.info("🎉 UNIVERSAL LEARNING SYSTEM DEPLOYED!")
        logger.info(f"✅ Applied learning to {learning_applied}/{len(bots)} bots")
        logger.info("📊 Performance Distribution:")
        for category, count in performance_categories.items():
            logger.info(f"   {category.replace('_', ' ').title()}: {count} bots")
        
        # Summary by P&L ranges
        major_losers = sum(1 for pnl in pnl_data.values() if pnl < -10)
        minor_losers = sum(1 for pnl in pnl_data.values() if -10 <= pnl < -2)
        neutral = sum(1 for pnl in pnl_data.values() if -2 <= pnl < 2)
        minor_winners = sum(1 for pnl in pnl_data.values() if 2 <= pnl < 10)
        major_winners = sum(1 for pnl in pnl_data.values() if pnl >= 10)
        
        logger.info("💰 P&L Distribution:")
        logger.info(f"   Major Losers (<-$10): {major_losers} bots")
        logger.info(f"   Minor Losers (-$10 to -$2): {minor_losers} bots")
        logger.info(f"   Neutral (-$2 to +$2): {neutral} bots")
        logger.info(f"   Minor Winners (+$2 to +$10): {minor_winners} bots")
        logger.info(f"   Major Winners (>+$10): {major_winners} bots")
        
    except Exception as e:
        logger.error(f"❌ Error applying learning system: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main execution function"""
    logger.info("🚀 Starting Universal Learning System for ALL bots...")
    logger.info("📈 This will apply profit-focused learning to all 45 bots based on real-time P&L performance")
    
    try:
        apply_learning_to_all_bots()
        logger.info("🎯 Universal learning system deployment COMPLETE!")
        logger.info("🔄 All bots now have optimized signal weights based on their individual performance")
        
    except Exception as e:
        logger.error(f"💥 Universal learning deployment failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())