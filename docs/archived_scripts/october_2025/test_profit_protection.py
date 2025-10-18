#!/usr/bin/env python3
"""
Phase 9A Test Script - Profit Protection Logic Verification
Test the new profit protection features before full deployment.
"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.models import Bot
from app.services.bot_evaluator import BotSignalEvaluator

def test_profit_protection():
    """Test profit protection logic with real bot data."""
    
    db = SessionLocal()
    try:
        # Test with AVNT-USD bot (has both realized and unrealized P&L)
        bot = db.query(Bot).filter(Bot.pair == 'AVNT-USD').first()
        
        if not bot:
            print("❌ AVNT-USD bot not found")
            return False
        
        print(f"\n{'='*60}")
        print(f"Testing Profit Protection with {bot.pair} (Bot #{bot.id})")
        print(f"{'='*60}\n")
        
        # Initialize evaluator
        evaluator = BotSignalEvaluator(db)
        
        # Test 1: P&L Calculation
        print("📊 Test 1: P&L Calculation")
        print("-" * 60)
        pnl_percent = evaluator.calculate_position_pnl_percent(bot)
        
        if pnl_percent is None:
            print("⚠️  No position found for AVNT-USD")
            print("   This could mean:")
            print("   - No holdings currently")
            print("   - No BUY trades in history")
            print("   - Unable to get current price")
        else:
            print(f"✅ P&L Calculation: {pnl_percent:+.2f}%")
            print(f"   Status: {'🟢 PROFIT' if pnl_percent > 0 else '🔴 LOSS'}")
        
        # Test 2: Profit Protection Logic
        print(f"\n📊 Test 2: Profit Protection Logic")
        print("-" * 60)
        print(f"Bot Settings:")
        print(f"   Take Profit: {bot.take_profit_pct}%")
        print(f"   Stop Loss: {bot.stop_loss_pct}%")
        
        if pnl_percent is not None:
            should_sell, reason = evaluator.should_sell_for_profit_protection(bot, pnl_percent)
            
            print(f"\nProfit Protection Decision:")
            print(f"   Should Sell: {'✅ YES' if should_sell else '❌ NO'}")
            print(f"   Reason: {reason}")
            
            if should_sell:
                if "TAKE_PROFIT" in reason:
                    print(f"   💰 TAKE PROFIT would trigger!")
                    print(f"   Current P&L ({pnl_percent:+.2f}%) >= Target ({bot.take_profit_pct}%)")
                elif "STOP_LOSS" in reason:
                    print(f"   🛑 STOP LOSS would trigger!")
                    print(f"   Current P&L ({pnl_percent:+.2f}%) <= Limit (-{bot.stop_loss_pct}%)")
            else:
                print(f"   ⏸️  P&L within safe range")
                print(f"   Range: -{bot.stop_loss_pct}% to +{bot.take_profit_pct}%")
        
        # Test 3: Existing Position Check
        print(f"\n📊 Test 3: Existing Position Check")
        print("-" * 60)
        has_position = evaluator.has_existing_position(bot)
        print(f"Has Position: {'✅ YES' if has_position else '❌ NO'}")
        
        if has_position:
            print(f"   ⏸️  BUY trades would be blocked (prevent double positions)")
        else:
            print(f"   ✅ BUY trades would be allowed (no existing position)")
        
        # Test 4: Integration Test - Full Decision Flow
        print(f"\n📊 Test 4: Full Trading Decision Flow")
        print("-" * 60)
        
        # Get market data
        from app.services.market_data_service import get_market_data_service
        market_service = get_market_data_service()
        market_data = market_service.get_candles(bot.pair, granularity='ONE_HOUR', limit=30)
        
        if not market_data.empty:
            # Evaluate bot with profit protection enabled
            result = evaluator.evaluate_bot(bot, market_data)
            
            print(f"Signal Score: {result['overall_score']:.4f}")
            print(f"Recommended Action: {result['action'].upper()}")
            print(f"Confidence: {result['confidence']:.2%}")
            
            # Check last_trade_reason if set
            if bot.last_trade_reason:
                print(f"Last Trade Reason: {bot.last_trade_reason}")
            
            # Explain the decision
            print(f"\nDecision Breakdown:")
            if pnl_percent is not None and pnl_percent >= bot.take_profit_pct:
                print(f"   ✅ TAKE PROFIT triggered (Priority 1)")
            elif pnl_percent is not None and pnl_percent <= -bot.stop_loss_pct:
                print(f"   ✅ STOP LOSS triggered (Priority 1)")
            elif result['action'] == 'buy' and has_position:
                print(f"   ⏸️  BUY signal blocked by existing position (Priority 2)")
            elif result['action'] == 'buy':
                print(f"   ✅ BUY signal from technical analysis (Priority 3)")
            elif result['action'] == 'sell':
                print(f"   ✅ SELL signal from technical analysis (Priority 3)")
            else:
                print(f"   ⏸️  HOLD - no trade conditions met")
        
        print(f"\n{'='*60}")
        print(f"✅ All Tests Complete!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_all_bots_pnl():
    """Quick scan of all bots with positions to see profit protection status."""
    
    db = SessionLocal()
    try:
        print(f"\n{'='*60}")
        print(f"Profit Protection Status - All Active Bots")
        print(f"{'='*60}\n")
        
        evaluator = BotSignalEvaluator(db)
        
        # Get all running bots
        bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
        
        bots_with_positions = []
        
        for bot in bots:
            pnl_percent = evaluator.calculate_position_pnl_percent(bot)
            
            if pnl_percent is not None:
                should_sell, reason = evaluator.should_sell_for_profit_protection(bot, pnl_percent)
                
                bots_with_positions.append({
                    'pair': bot.pair,
                    'pnl': pnl_percent,
                    'should_sell': should_sell,
                    'reason': reason,
                    'take_profit': bot.take_profit_pct,
                    'stop_loss': bot.stop_loss_pct
                })
        
        # Sort by P&L
        bots_with_positions.sort(key=lambda x: x['pnl'])
        
        print(f"Found {len(bots_with_positions)} bots with positions:\n")
        print(f"{'Pair':<15} {'P&L':>8} {'Status':<12} {'Action':<25}")
        print("-" * 60)
        
        for bot_data in bots_with_positions:
            pnl = bot_data['pnl']
            status = '🟢 PROFIT' if pnl > 0 else '🔴 LOSS'
            
            if bot_data['should_sell']:
                action = f"⚠️  {bot_data['reason']}"
            else:
                action = "✅ HOLD (safe range)"
            
            print(f"{bot_data['pair']:<15} {pnl:>7.2f}% {status:<12} {action}")
        
        # Summary
        print("\n" + "=" * 60)
        take_profit_triggers = sum(1 for b in bots_with_positions if 'TAKE_PROFIT' in b['reason'])
        stop_loss_triggers = sum(1 for b in bots_with_positions if 'STOP_LOSS' in b['reason'])
        safe_positions = len(bots_with_positions) - take_profit_triggers - stop_loss_triggers
        
        print(f"Summary:")
        print(f"   Total Positions: {len(bots_with_positions)}")
        print(f"   💰 Take Profit Triggers: {take_profit_triggers}")
        print(f"   🛑 Stop Loss Triggers: {stop_loss_triggers}")
        print(f"   ✅ Safe Positions: {safe_positions}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔬 Phase 9A - Profit Protection Test Suite\n")
    
    # Run detailed test with AVNT-USD
    test_profit_protection()
    
    # Run quick scan of all bots
    test_all_bots_pnl()
    
    print("\n✅ Testing complete! Review results above before deploying to production.\n")
