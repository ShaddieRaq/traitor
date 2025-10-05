#!/usr/bin/env python3
"""
Phase 8.1: Manual Learning System Activation Script
Quick script to activate the learning system without API dependencies
"""

import sys
import os
sys.path.append('/Users/lazy_genius/Projects/trader/backend')

import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.models import Bot, SignalPredictionRecord
from app.services.adaptive_signal_weighting import get_adaptive_weighting_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_prediction_data():
    """Check the current state of prediction data"""
    db = SessionLocal()
    
    try:
        total_predictions = db.query(SignalPredictionRecord).count()
        evaluated_predictions = db.query(SignalPredictionRecord).filter(
            SignalPredictionRecord.outcome.isnot(None)
        ).count()
        
        print(f"📊 PREDICTION DATA STATUS")
        print(f"   Total predictions: {total_predictions:,}")
        print(f"   Evaluated predictions: {evaluated_predictions:,}")
        print(f"   Unevaluated: {total_predictions - evaluated_predictions:,}")
        print(f"   Evaluation rate: {(evaluated_predictions / total_predictions * 100):.1f}%" if total_predictions > 0 else "0%")
        
        return total_predictions, evaluated_predictions
        
    finally:
        db.close()

def check_bot_eligibility():
    """Check which bots are eligible for learning updates"""
    db = SessionLocal()
    
    try:
        adaptive_service = get_adaptive_weighting_service()
        active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
        
        eligible_bots = []
        ineligible_bots = []
        
        print(f"🤖 BOT ELIGIBILITY CHECK")
        print(f"   Total active bots: {len(active_bots)}")
        
        for bot in active_bots:
            should_update, reason = adaptive_service.should_update_weights(bot, db)
            if should_update:
                eligible_bots.append((bot.id, bot.pair))
                print(f"   ✅ {bot.pair} (Bot {bot.id}): {reason}")
            else:
                ineligible_bots.append((bot.id, bot.pair, reason))
                
        print(f"\n📈 ELIGIBLE BOTS: {len(eligible_bots)}")
        for bot_id, pair in eligible_bots:
            print(f"   • {pair} (Bot {bot_id})")
            
        print(f"\n❌ INELIGIBLE BOTS: {len(ineligible_bots)} (showing first 5)")
        for bot_id, pair, reason in ineligible_bots[:5]:
            print(f"   • {pair} (Bot {bot_id}): {reason}")
            
        return eligible_bots, ineligible_bots
        
    finally:
        db.close()

def activate_learning_for_bot(bot_id):
    """Manually activate learning for a specific bot"""
    db = SessionLocal()
    
    try:
        adaptive_service = get_adaptive_weighting_service()
        
        # Get bot info
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            print(f"❌ Bot {bot_id} not found")
            return False
            
        print(f"🚀 ACTIVATING LEARNING FOR {bot.pair} (Bot {bot_id})")
        
        # Check eligibility
        should_update, reason = adaptive_service.should_update_weights(bot, db)
        print(f"   Eligibility check: {should_update} - {reason}")
        
        if not should_update:
            print(f"   ⚠️ Bot not eligible, but trying anyway...")
        
        # Try to update
        result = adaptive_service.process_bot_weight_update(bot_id)
        
        if result.get('success'):
            print(f"   ✅ Learning update successful!")
            print(f"   📊 Result: {result.get('message')}")
            if 'old_weights' in result and 'new_weights' in result:
                print(f"   🔄 Weight changes:")
                old_weights = result['old_weights']
                new_weights = result['new_weights']
                for signal in old_weights:
                    old_w = old_weights[signal]
                    new_w = new_weights[signal]
                    change = new_w - old_w
                    print(f"      {signal}: {old_w:.3f} → {new_w:.3f} ({change:+.3f})")
            return True
        else:
            print(f"   ❌ Learning update failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"   💥 Error activating learning: {e}")
        return False
    finally:
        db.close()

def main():
    print("🎯 PHASE 8.1: LEARNING SYSTEM ACTIVATION")
    print("=" * 50)
    
    # 1. Check prediction data status
    total_predictions, evaluated_predictions = check_prediction_data()
    
    print("\n")
    
    # 2. Check bot eligibility
    eligible_bots, ineligible_bots = check_bot_eligibility()
    
    print("\n")
    
    # 3. Try to activate learning for eligible bots
    if eligible_bots:
        print(f"🎯 ATTEMPTING TO ACTIVATE LEARNING")
        print(f"   Trying first {min(3, len(eligible_bots))} eligible bots...")
        
        successful_activations = 0
        for bot_id, pair in eligible_bots[:3]:
            print(f"\n🔄 Attempting {pair} (Bot {bot_id})...")
            if activate_learning_for_bot(bot_id):
                successful_activations += 1
                
        print(f"\n✅ LEARNING ACTIVATION RESULTS")
        print(f"   Successful: {successful_activations}/{min(3, len(eligible_bots))}")
        
    else:
        print("❌ NO ELIGIBLE BOTS FOUND")
        if evaluated_predictions < 50:
            print("💡 NEXT STEP: Need to evaluate prediction outcomes first")
            print("   Run prediction outcome evaluation to create learning data")
        else:
            print("💡 NEXT STEP: Check bot prediction data requirements")
            
    print(f"\n🎉 PHASE 8.1 DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    main()