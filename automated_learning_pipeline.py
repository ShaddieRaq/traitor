#!/usr/bin/env python3
"""
Phase 8.2: Automated Learning Pipeline
Apply profit-focused learning to all 8 eligible bots
"""

import sys
sys.path.append('/Users/lazy_genius/Projects/trader/backend')

import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple
from app.core.database import SessionLocal
from app.models.models import Bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot performance data from our analysis
BOT_PERFORMANCE = {
    4: {"pair": "ETH-USD", "pnl": -4.49, "type": "major_loser"},
    6: {"pair": "SOL-USD", "pnl": -1.87, "type": "minor_loser"}, 
    7: {"pair": "XRP-USD", "pnl": -3.12, "type": "minor_loser"},
    8: {"pair": "DOGE-USD", "pnl": -2.45, "type": "minor_loser"},
    12: {"pair": "AERO-USD", "pnl": +1.23, "type": "minor_winner"},
    13: {"pair": "SUI-USD", "pnl": -11.0, "type": "major_loser"},  # Already adjusted
    14: {"pair": "AVAX-USD", "pnl": -5.67, "type": "major_loser"},
    15: {"pair": "TOSHI-USD", "pnl": +0.89, "type": "minor_winner"}
}

def analyze_bot_performance(bot_id: int) -> str:
    """Determine learning strategy based on bot performance"""
    perf = BOT_PERFORMANCE.get(bot_id, {})
    pnl = perf.get("pnl", 0)
    
    if pnl < -5:
        return "aggressive_rebalance"  # Major losers need dramatic changes
    elif pnl < 0:
        return "moderate_rebalance"    # Minor losers need gentle adjustments
    elif pnl > 0:
        return "optimize_winner"       # Winners need fine-tuning
    else:
        return "maintain"              # Neutral bots stay the same

def apply_learning_strategy(signal_config: Dict, strategy: str, bot_pair: str) -> Tuple[Dict, str]:
    """Apply specific learning adjustments based on strategy"""
    
    if strategy == "aggressive_rebalance":
        # Major losers: Dramatically reduce RSI, boost MA
        changes = []
        if 'rsi' in signal_config and signal_config['rsi']:
            old_weight = signal_config['rsi'].get('weight', 0.4)
            new_weight = max(0.15, old_weight - 0.15)  # Aggressive RSI reduction
            signal_config['rsi']['weight'] = new_weight
            changes.append(f"RSI: {old_weight:.3f} → {new_weight:.3f} (aggressive reduction)")
        
        if 'moving_average' in signal_config and signal_config['moving_average']:
            old_weight = signal_config['moving_average'].get('weight', 0.35)
            new_weight = min(0.6, old_weight + 0.15)  # Aggressive MA boost
            signal_config['moving_average']['weight'] = new_weight
            changes.append(f"MA: {old_weight:.3f} → {new_weight:.3f} (aggressive boost)")
            
    elif strategy == "moderate_rebalance":
        # Minor losers: Gentle adjustments
        changes = []
        if 'rsi' in signal_config and signal_config['rsi']:
            old_weight = signal_config['rsi'].get('weight', 0.4)
            new_weight = max(0.2, old_weight - 0.08)  # Moderate RSI reduction
            signal_config['rsi']['weight'] = new_weight
            changes.append(f"RSI: {old_weight:.3f} → {new_weight:.3f} (moderate reduction)")
        
        if 'macd' in signal_config and signal_config['macd']:
            old_weight = signal_config['macd'].get('weight', 0.25)
            new_weight = min(0.5, old_weight + 0.08)  # Moderate MACD boost
            signal_config['macd']['weight'] = new_weight
            changes.append(f"MACD: {old_weight:.3f} → {new_weight:.3f} (moderate boost)")
            
    elif strategy == "optimize_winner":
        # Winners: Fine-tune successful configurations
        changes = []
        if 'moving_average' in signal_config and signal_config['moving_average']:
            old_weight = signal_config['moving_average'].get('weight', 0.35)
            new_weight = min(0.45, old_weight + 0.05)  # Small MA optimization
            signal_config['moving_average']['weight'] = new_weight
            changes.append(f"MA: {old_weight:.3f} → {new_weight:.3f} (winner optimization)")
            
    else:  # maintain
        changes = ["No changes - maintaining current configuration"]
    
    return signal_config, "; ".join(changes)

def normalize_weights(signal_config: Dict) -> Dict:
    """Normalize all signal weights to sum to 1.0"""
    total_weight = sum(config.get('weight', 0) for config in signal_config.values() 
                      if config and config.get('enabled', False) and isinstance(config, dict))
    
    if total_weight > 0:
        for signal_name, config in signal_config.items():
            if config and isinstance(config, dict) and config.get('enabled', False):
                config['weight'] = config['weight'] / total_weight
    
    return signal_config

def apply_learning_to_bot(bot_id: int) -> bool:
    """Apply profit-focused learning to a specific bot"""
    db = SessionLocal()
    
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            print(f"❌ Bot {bot_id} not found")
            return False
        
        # Skip if already processed (SUI-USD was done manually)
        if bot_id == 13:
            print(f"✅ {bot.pair} (Bot {bot_id}) - Already processed manually")
            return True
            
        perf = BOT_PERFORMANCE.get(bot_id, {})
        pnl = perf.get("pnl", 0)
        strategy = analyze_bot_performance(bot_id)
        
        print(f"\n🎯 PROCESSING {bot.pair} (Bot {bot_id})")
        print(f"   Current P&L: ${pnl:.2f}")
        print(f"   Strategy: {strategy}")
        
        # Parse current configuration
        signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
        
        # Apply learning strategy
        updated_config, changes = apply_learning_strategy(signal_config.copy(), strategy, bot.pair)
        
        # Normalize weights
        updated_config = normalize_weights(updated_config)
        
        # Update bot if changes were made
        if changes != "No changes - maintaining current configuration":
            bot.signal_config = json.dumps(updated_config, indent=2)
            bot.last_update = datetime.utcnow()
            db.commit()
            
            print(f"   ✅ Applied: {changes}")
            
            # Show final weights
            print(f"   📊 New weights:")
            for signal_name, config in updated_config.items():
                if config and isinstance(config, dict) and config.get('enabled', False):
                    weight = config.get('weight', 0.0)
                    print(f"      {signal_name}: {weight:.3f}")
        else:
            print(f"   ⏸️  {changes}")
            
        return True
        
    except Exception as e:
        db.rollback()
        print(f"💥 Error processing bot {bot_id}: {e}")
        return False
    finally:
        db.close()

def run_automated_learning_pipeline():
    """Run learning pipeline on all 8 eligible bots"""
    print("🚀 AUTOMATED LEARNING PIPELINE - PHASE 8.2")
    print("=" * 60)
    print("📊 Applying profit-focused learning to 8 eligible bots")
    print()
    
    eligible_bots = list(BOT_PERFORMANCE.keys())
    success_count = 0
    
    for bot_id in eligible_bots:
        if apply_learning_to_bot(bot_id):
            success_count += 1
    
    print(f"\n🎉 PIPELINE COMPLETE!")
    print(f"   Successfully processed: {success_count}/{len(eligible_bots)} bots")
    print(f"   Learning strategies applied based on profit performance")
    print(f"   Major losers: Aggressive rebalancing")
    print(f"   Minor losers: Moderate adjustments") 
    print(f"   Winners: Fine-tuning optimization")
    
    return success_count == len(eligible_bots)

def main():
    print("🧠 PHASE 8: PROFIT-FOCUSED LEARNING SYSTEM")
    print("🎯 Goal: Optimize signal weights for profit, not accuracy")
    print()
    
    success = run_automated_learning_pipeline()
    
    if success:
        print(f"\n✅ SUCCESS: All eligible bots updated with profit-focused learning!")
        print(f"\nNext steps:")
        print(f"1. Monitor bot performance over next 24-48 hours")
        print(f"2. Track P&L improvements from learning adjustments")
        print(f"3. Prepare Phase 9 hybrid scaling system")
    else:
        print(f"\n❌ PARTIAL SUCCESS: Some bots failed to update")

if __name__ == "__main__":
    main()