#!/usr/bin/env python3
"""
System-Wide Threshold Optimization
=================================

Apply ±0.05 thresholds to all bots based on successful testing results.
The test results show immediate signal activation and improved trading frequency.

Results from testing:
- ETH-USD: Immediate SELL signal activation (was HOLD with ±0.1)
- TOSHI-USD: Immediate SELL signal activation (was HOLD with ±0.1)
- AVAX-USD: No change (validates threshold logic)

Usage:
    python scripts/apply_system_wide_thresholds.py [--dry-run]
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import get_db
from app.models.models import Bot

def apply_system_wide_thresholds(dry_run=False):
    """Apply ±0.05 thresholds to all bots system-wide."""
    
    db = next(get_db())
    
    print("🚀 Applying System-Wide Threshold Optimization")
    print("=" * 60)
    print("New Thresholds: ±0.05 (from ±0.1)")
    print("Based on: Successful test results from ETH-USD, TOSHI-USD, AVAX-USD")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")
    
    try:
        # Get all bots
        bots = db.query(Bot).all()
        print(f"\n📊 Found {len(bots)} bots to update")
        
        updated_count = 0
        already_configured = 0
        
        for bot in bots:
            try:
                # Parse current signal config
                if isinstance(bot.signal_config, str):
                    signal_config = json.loads(bot.signal_config)
                else:
                    signal_config = bot.signal_config or {}
                
                # Check if already configured with thresholds
                if 'trading_thresholds' in signal_config:
                    current_threshold = signal_config['trading_thresholds'].get('sell_threshold', 0.1)
                    if current_threshold == 0.05:
                        print(f"✅ {bot.pair} already optimized (±0.05)")
                        already_configured += 1
                        continue
                
                # Add optimized threshold configuration
                signal_config['trading_thresholds'] = {
                    'buy_threshold': -0.05,
                    'sell_threshold': 0.05,
                    'optimization_applied': True,
                    'applied_date': datetime.now().isoformat(),
                    'based_on_testing': 'ETH-USD, TOSHI-USD, AVAX-USD success',
                    'original_thresholds': {
                        'buy_threshold': -0.1,
                        'sell_threshold': 0.1
                    }
                }
                
                if dry_run:
                    print(f"🧪 DRY RUN: Would update {bot.pair} (ID: {bot.id}) to ±0.05 thresholds")
                else:
                    # Update the bot
                    bot.signal_config = json.dumps(signal_config)
                    updated_count += 1
                    print(f"✅ Updated {bot.pair} (ID: {bot.id}) to ±0.05 thresholds")
                    
            except Exception as e:
                print(f"❌ Error updating {bot.pair}: {e}")
        
        if not dry_run:
            db.commit()
            print(f"\n🎉 System-Wide Optimization Complete!")
            print(f"   Updated: {updated_count} bots")
            print(f"   Already optimized: {already_configured} bots")
            print(f"   Total: {updated_count + already_configured}/{len(bots)} bots")
        else:
            print(f"\n🧪 DRY RUN Summary:")
            print(f"   Would update: {len(bots) - already_configured} bots")
            print(f"   Already optimized: {already_configured} bots")
            
    except Exception as e:
        print(f"❌ Error during system-wide update: {e}")
        if not dry_run:
            db.rollback()
    finally:
        db.close()

def create_system_monitoring_script():
    """Create monitoring script for system-wide optimization."""
    script_content = '''#!/usr/bin/env python3
"""
System-Wide Threshold Monitoring
===============================

Monitors all bots after system-wide ±0.05 threshold optimization.
"""

import requests
import json
from datetime import datetime

def monitor_system_optimization():
    base_url = "http://localhost:8000/api/v1"
    
    print(f"\\n🌟 SYSTEM-WIDE OPTIMIZATION MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # Get enhanced bot status
    response = requests.get(f"{base_url}/bots/status/enhanced")
    if response.status_code == 200:
        bots = response.json()
        
        # Categorize bots by trading activity
        active_signals = []
        confirmation_pending = []
        hold_signals = []
        blocked_bots = []
        
        print(f"\\n📊 ALL BOTS STATUS (±0.05 thresholds):")
        print("   Pair        | Score     | Action | Temp | Status  | Trade Ready | Confirmation")
        print("   " + "-" * 85)
        
        for bot in bots:
            score = bot['current_combined_score']
            intent = bot.get('trading_intent', {})
            action = intent.get('next_action', 'unknown')
            temp = bot['temperature']
            status = bot['status']
            can_trade = bot.get('trade_readiness', {}).get('can_trade', False)
            
            confirmation = bot.get('confirmation', {})
            is_confirming = confirmation.get('is_active', False)
            conf_status = "CONFIRMING" if is_confirming else "READY" if can_trade else "BLOCKED"
            
            print(f"   {bot['pair']:<11} | {score:>8.4f} | {action:<6} | {temp:<4} | {status:<7} | {can_trade:<11} | {conf_status}")
            
            # Categorize for summary
            if action in ['buy', 'sell'] and is_confirming:
                confirmation_pending.append(bot['pair'])
            elif action in ['buy', 'sell'] and can_trade:
                active_signals.append(bot['pair'])
            elif not can_trade:
                blocked_bots.append(bot['pair'])
            else:
                hold_signals.append(bot['pair'])
        
        # Summary
        print(f"\\n📈 OPTIMIZATION IMPACT SUMMARY:")
        print(f"   🔥 Active Signals: {len(active_signals)} pairs")
        if active_signals:
            print(f"      {', '.join(active_signals)}")
        print(f"   ⏳ Confirming Signals: {len(confirmation_pending)} pairs")
        if confirmation_pending:
            print(f"      {', '.join(confirmation_pending)}")
        print(f"   ⏸️  Hold Signals: {len(hold_signals)} pairs")
        print(f"   🚫 Blocked: {len(blocked_bots)} pairs")
        if blocked_bots:
            print(f"      {', '.join(blocked_bots)}")
        
        # Calculate improvement estimate
        total_trading_activity = len(active_signals) + len(confirmation_pending)
        improvement_estimate = (total_trading_activity / len(bots)) * 100
        
        print(f"\\n🎯 TRADING ACTIVITY: {total_trading_activity}/{len(bots)} bots ({improvement_estimate:.1f}% active)")
        print("=" * 90)

if __name__ == "__main__":
    monitor_system_optimization()
'''
    
    script_path = os.path.join(os.path.dirname(__file__), 'monitor_system_optimization.py')
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"📊 Created system monitoring script: {script_path}")
    return script_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    args = parser.parse_args()
    
    apply_system_wide_thresholds(dry_run=args.dry_run)
    
    if not args.dry_run:
        create_system_monitoring_script()
        print(f"\\n🚀 NEXT STEPS:")
        print(f"1. Monitor system: python scripts/monitor_system_optimization.py")
        print(f"2. Check individual performance: python scripts/monitor_enhanced_threshold_test.py")
        print(f"3. System health: ./scripts/status.sh")
        print(f"\\n🎯 Expected: Significant increase in trading activity across all pairs!")
