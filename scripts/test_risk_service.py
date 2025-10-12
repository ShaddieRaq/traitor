#!/usr/bin/env python3
"""
Test script to verify RiskAdjustmentService is working correctly.
Shows risk multipliers for all active bots based on current performance.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.models import Bot
from app.services.risk_adjustment_service import RiskAdjustmentService

def main():
    db = SessionLocal()
    risk_service = RiskAdjustmentService(db)
    
    try:
        print("\n" + "="*80)
        print("🎲 RISK ADJUSTMENT SERVICE - LIVE TEST")
        print("="*80)
        print(f"Formula: risk_multiplier = (signal*2.0 + confidence*0.5) * (1.0 + avg_pnl*10.0)")
        print(f"Range: 0.2x (max risk reduction) to 3.0x (max risk amplification)")
        print("="*80 + "\n")
        
        # Get all active bots (status = "RUNNING")
        bots = db.query(Bot).filter(Bot.status == "RUNNING").order_by(Bot.pair).all()
        
        if not bots:
            print("❌ No active bots found!")
            return
        
        print(f"Found {len(bots)} active bots\n")
        
        # Group by risk multiplier ranges
        high_risk_bots = []  # 2.0x - 3.0x (winners)
        medium_risk_bots = []  # 1.0x - 2.0x (neutral/slight winners)
        low_risk_bots = []  # 0.2x - 1.0x (losers)
        
        for bot in bots:
            # Use current bot signals
            signal_strength = abs(bot.current_combined_score) if bot.current_combined_score else 0.05
            confidence = 0.8  # Default confidence
            
            # Get risk assessment
            risk_data = risk_service.get_bot_risk_multiplier(
                bot_id=bot.id,
                product_id=bot.pair,
                signal_strength=signal_strength,
                confidence=confidence
            )
            
            risk_multiplier = risk_data['risk_multiplier']
            reason = risk_data['calculation_reason']
            
            bot_info = {
                'bot': bot,
                'risk_multiplier': risk_multiplier,
                'reason': reason,
                'signal_strength': signal_strength
            }
            
            if risk_multiplier >= 2.0:
                high_risk_bots.append(bot_info)
            elif risk_multiplier >= 1.0:
                medium_risk_bots.append(bot_info)
            else:
                low_risk_bots.append(bot_info)
        
        # Display results grouped by risk level
        print("🔥 HIGH RISK BOTS (2.0x - 3.0x) - WINNERS GET BIGGER POSITIONS")
        print("-" * 80)
        if high_risk_bots:
            for info in sorted(high_risk_bots, key=lambda x: x['risk_multiplier'], reverse=True):
                print(f"{info['bot'].pair:12} | {info['risk_multiplier']:.2f}x | Signal: {info['signal_strength']:.3f} | {info['reason']}")
        else:
            print("None")
        
        print("\n🌡️  MEDIUM RISK BOTS (1.0x - 2.0x) - NEUTRAL/SLIGHT WINNERS")
        print("-" * 80)
        if medium_risk_bots:
            for info in sorted(medium_risk_bots, key=lambda x: x['risk_multiplier'], reverse=True):
                print(f"{info['bot'].pair:12} | {info['risk_multiplier']:.2f}x | Signal: {info['signal_strength']:.3f} | {info['reason']}")
        else:
            print("None")
        
        print("\n❄️  LOW RISK BOTS (0.2x - 1.0x) - LOSERS GET SMALLER POSITIONS")
        print("-" * 80)
        if low_risk_bots:
            for info in sorted(low_risk_bots, key=lambda x: x['risk_multiplier'], reverse=True):
                print(f"{info['bot'].pair:12} | {info['risk_multiplier']:.2f}x | Signal: {info['signal_strength']:.3f} | {info['reason']}")
        else:
            print("None")
        
        # Summary statistics
        print("\n" + "="*80)
        print("📊 SUMMARY STATISTICS")
        print("="*80)
        print(f"Total Bots: {len(bots)}")
        print(f"High Risk (2.0x-3.0x): {len(high_risk_bots)} bots - {len(high_risk_bots)/len(bots)*100:.1f}%")
        print(f"Medium Risk (1.0x-2.0x): {len(medium_risk_bots)} bots - {len(medium_risk_bots)/len(bots)*100:.1f}%")
        print(f"Low Risk (0.2x-1.0x): {len(low_risk_bots)} bots - {len(low_risk_bots)/len(bots)*100:.1f}%")
        
        avg_multiplier = sum(info['risk_multiplier'] for info in high_risk_bots + medium_risk_bots + low_risk_bots) / len(bots)
        print(f"\nAverage Risk Multiplier: {avg_multiplier:.2f}x")
        print(f"Expected Portfolio Impact: {'Capital flowing to winners ✅' if avg_multiplier > 1.0 else 'Capital protection mode ⚠️'}")
        
        print("\n✅ RiskAdjustmentService is active and calculating multipliers!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error testing RiskAdjustmentService: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
