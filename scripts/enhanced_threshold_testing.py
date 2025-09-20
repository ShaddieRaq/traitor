#!/usr/bin/env python3
"""
Priority 2: Enhanced Threshold Testing Implementation
===================================================

This approach modifies the bot evaluator to support per-bot threshold testing
while maintaining system safety and allowing easy rollback.

Strategy:
1. Add threshold configuration to bot signal_config
2. Modify bot evaluator to respect per-bot thresholds
3. Test on selected pairs with ±0.05 thresholds
4. Monitor and analyze results

Target Pairs (from 7-day analysis):
- ETH-USD: 0.069 score → would become BUY signal
- AVAX-USD: 0.068 score → would become BUY signal  
- TOSHI-USD: 0.075 score → would become BUY signal

Usage:
    python scripts/enhanced_threshold_testing.py [--dry-run]
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class EnhancedThresholdTester:
    def __init__(self, dry_run=False):
        self.base_url = "http://localhost:8000/api/v1"
        self.dry_run = dry_run
        self.test_pairs = ["ETH-USD", "AVAX-USD", "TOSHI-USD"]
        self.current_threshold = 0.1
        self.test_threshold = 0.05
        
    def get_bot_by_pair(self, pair: str) -> Dict:
        """Get bot configuration for a specific trading pair."""
        try:
            response = requests.get(f"{self.base_url}/bots/")
            if response.status_code == 200:
                bots = response.json()
                for bot in bots:
                    if bot['pair'] == pair:
                        return bot
        except Exception as e:
            print(f"❌ Error fetching bot for {pair}: {e}")
        return None
    
    def add_threshold_config_to_bot(self, bot_id: int, bot_config: Dict) -> bool:
        """Add threshold configuration to bot's signal_config."""
        
        # Add trading thresholds to signal config
        enhanced_config = bot_config['signal_config'].copy()
        enhanced_config['trading_thresholds'] = {
            'buy_threshold': -self.test_threshold,
            'sell_threshold': self.test_threshold,
            'test_mode': True,
            'test_start': datetime.now().isoformat(),
            'test_duration_hours': 72
        }
        
        update_data = {
            'signal_config': enhanced_config
        }
        
        if self.dry_run:
            print(f"🧪 DRY RUN: Would update bot {bot_id} with thresholds ±{self.test_threshold}")
            print(f"   Config: {json.dumps(enhanced_config.get('trading_thresholds'), indent=4)}")
            return True
        
        try:
            response = requests.put(
                f"{self.base_url}/bots/{bot_id}",
                json=update_data
            )
            if response.status_code == 200:
                print(f"✅ Updated bot {bot_id} with test thresholds ±{self.test_threshold}")
                return True
            else:
                print(f"❌ Failed to update bot {bot_id}: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error updating bot {bot_id}: {e}")
        
        return False
    
    def create_bot_evaluator_patch(self):
        """Create a patch file for the bot evaluator to support per-bot thresholds."""
        
        patch_content = '''# Bot Evaluator Threshold Patch
# Add this to the _determine_action method in bot_evaluator.py

def _determine_action(self, overall_score: float, bot: Bot) -> str:
    """
    Determine trading action based on overall score and bot-specific thresholds.
    
    Supports per-bot threshold configuration via signal_config.trading_thresholds
    Falls back to default thresholds if not configured.
    """
    
    # Check for bot-specific thresholds in signal_config
    try:
        signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
        if signal_config and 'trading_thresholds' in signal_config:
            thresholds = signal_config['trading_thresholds']
            buy_threshold = thresholds.get('buy_threshold', -0.1)
            sell_threshold = thresholds.get('sell_threshold', 0.1)
            print(f"🎯 Using custom thresholds for {bot.pair}: buy={buy_threshold}, sell={sell_threshold}")
        else:
            # Default thresholds
            buy_threshold = -0.1
            sell_threshold = 0.1
    except Exception as e:
        # Fallback to default if any error
        buy_threshold = -0.1
        sell_threshold = 0.1
        print(f"⚠️ Error reading thresholds for {bot.pair}, using defaults: {e}")
    
    if overall_score <= buy_threshold:
        return 'buy'
    elif overall_score >= sell_threshold:
        return 'sell'
    else:
        return 'hold'
'''
        
        patch_path = os.path.join(os.path.dirname(__file__), 'bot_evaluator_threshold_patch.py')
        with open(patch_path, 'w') as f:
            f.write(patch_content)
        
        print(f"📄 Created bot evaluator patch: {patch_path}")
        return patch_path
    
    def backup_bot_evaluator(self):
        """Create a backup of the current bot evaluator."""
        import shutil
        
        original_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'services', 'bot_evaluator.py')
        backup_path = os.path.join(os.path.dirname(__file__), 'analysis', f'bot_evaluator_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
        
        # Create analysis directory if it doesn't exist
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        if self.dry_run:
            print(f"🧪 DRY RUN: Would backup {original_path} to {backup_path}")
            return backup_path
        
        try:
            shutil.copy2(original_path, backup_path)
            print(f"💾 Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None
    
    def apply_evaluator_patch(self):
        """Apply the threshold patch to bot_evaluator.py."""
        
        evaluator_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'services', 'bot_evaluator.py')
        
        if self.dry_run:
            print(f"🧪 DRY RUN: Would patch {evaluator_path}")
            return True
        
        try:
            # Read current file
            with open(evaluator_path, 'r') as f:
                content = f.read()
            
            # Find the _determine_action method and replace it
            old_method = '''    def _determine_action(self, overall_score: float) -> str:
        """
        Determine trading action based on overall score.
        
        Uses configurable thresholds for buy/sell decisions.
        Default thresholds: buy <= -0.3, sell >= 0.3, hold otherwise
        """
        buy_threshold = -0.1  # Lowered for testing (was -0.3)
        sell_threshold = 0.1   # Lowered for testing (was 0.3)
        
        if overall_score <= buy_threshold:
            return 'buy'
        elif overall_score >= sell_threshold:
            return 'sell'
        else:
            return 'hold' '''
            
            new_method = '''    def _determine_action(self, overall_score: float, bot: Bot) -> str:
        """
        Determine trading action based on overall score and bot-specific thresholds.
        
        Supports per-bot threshold configuration via signal_config.trading_thresholds
        Falls back to default thresholds if not configured.
        """
        
        # Check for bot-specific thresholds in signal_config
        try:
            signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
            if signal_config and 'trading_thresholds' in signal_config:
                thresholds = signal_config['trading_thresholds']
                buy_threshold = thresholds.get('buy_threshold', -0.1)
                sell_threshold = thresholds.get('sell_threshold', 0.1)
                logger.info(f"Using custom thresholds for {bot.pair}: buy={buy_threshold}, sell={sell_threshold}")
            else:
                # Default thresholds
                buy_threshold = -0.1
                sell_threshold = 0.1
        except Exception as e:
            # Fallback to default if any error
            buy_threshold = -0.1
            sell_threshold = 0.1
            logger.warning(f"Error reading thresholds for {bot.pair}, using defaults: {e}")
        
        if overall_score <= buy_threshold:
            return 'buy'
        elif overall_score >= sell_threshold:
            return 'sell'
        else:
            return 'hold' '''
            
            if old_method in content:
                # Replace the method
                updated_content = content.replace(old_method, new_method)
                
                # Also need to update the method call to pass the bot parameter
                updated_content = updated_content.replace(
                    'action = self._determine_action(overall_score)',
                    'action = self._determine_action(overall_score, bot)'
                )
                
                # Write the updated file
                with open(evaluator_path, 'w') as f:
                    f.write(updated_content)
                
                print(f"✅ Applied threshold patch to {evaluator_path}")
                return True
            else:
                print(f"❌ Could not find target method in {evaluator_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error applying patch: {e}")
            return False
    
    def create_monitoring_script(self):
        """Create enhanced monitoring script for threshold testing."""
        script_content = f'''#!/usr/bin/env python3
"""
Enhanced Threshold Test Monitoring
=================================

Monitors performance of threshold testing on selected pairs.
Test Threshold: ±{self.test_threshold}
Default Threshold: ±{self.current_threshold}
Test Pairs: {', '.join(self.test_pairs)}
"""

import requests
import json
from datetime import datetime

def monitor_threshold_test():
    base_url = "http://localhost:8000/api/v1"
    
    print(f"\\n🔬 THRESHOLD TEST MONITORING - {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print("=" * 80)
    
    # Get enhanced bot status
    response = requests.get(f"{{base_url}}/bots/status/enhanced")
    if response.status_code == 200:
        bots = response.json()
        
        test_pairs = {repr(self.test_pairs)}
        
        print(f"\\n🧪 TEST BOTS (±{self.test_threshold} threshold):")
        print("   Pair        | Score     | Action    | Temp | Status  | Trade Ready")
        print("   " + "-" * 70)
        
        for bot in bots:
            if bot['pair'] in test_pairs:
                score = bot['current_combined_score']
                intent = bot.get('trading_intent', {{}})
                action = intent.get('next_action', 'unknown')
                temp = bot['temperature']
                status = bot['status']
                can_trade = bot.get('trade_readiness', {{}}).get('can_trade', False)
                
                print(f"   {{bot['pair']:<11}} | {{score:>8.4f}} | {{action:<8}} | {{temp:<4}} | {{status:<7}} | {{can_trade}}")
        
        # Show signals that would be different with default thresholds
        print(f"\\n📊 THRESHOLD IMPACT ANALYSIS:")
        print("   Pair        | Score     | ±0.05 Action | ±0.10 Action | Impact")
        print("   " + "-" * 70)
        
        for bot in bots:
            if bot['pair'] in test_pairs:
                score = bot['current_combined_score']
                
                # Calculate actions for both thresholds
                action_005 = 'buy' if score <= -0.05 else ('sell' if score >= 0.05 else 'hold')
                action_010 = 'buy' if score <= -0.10 else ('sell' if score >= 0.10 else 'hold')
                
                impact = "🔄 DIFFERENT" if action_005 != action_010 else "⏸️  SAME"
                
                print(f"   {{bot['pair']:<11}} | {{score:>8.4f}} | {{action_005:<11}} | {{action_010:<11}} | {{impact}}")
        
        print("\\n" + "=" * 80)

if __name__ == "__main__":
    monitor_threshold_test()
'''
        
        script_path = os.path.join(os.path.dirname(__file__), 'monitor_enhanced_threshold_test.py')
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        print(f"📊 Created enhanced monitoring script: {script_path}")
        return script_path
    
    def implement_enhanced_threshold_testing(self):
        """Main function to implement enhanced threshold testing."""
        print("🔬 Starting Enhanced Threshold Testing Implementation")
        print("=" * 70)
        print(f"Test Threshold: ±{self.test_threshold}")
        print(f"Default Threshold: ±{self.current_threshold}")
        print(f"Test Pairs: {', '.join(self.test_pairs)}")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")
        
        # Step 1: Create backup
        backup_path = self.backup_bot_evaluator()
        if not backup_path and not self.dry_run:
            print("❌ Could not create backup, aborting for safety")
            return False
        
        # Step 2: Create patch file
        patch_path = self.create_bot_evaluator_patch()
        
        # Step 3: Apply evaluator patch
        if not self.apply_evaluator_patch():
            print("❌ Failed to apply evaluator patch")
            return False
        
        # Step 4: Configure test bots
        configured_bots = 0
        for pair in self.test_pairs:
            print(f"\\n🔧 Configuring threshold testing for {pair}...")
            
            bot = self.get_bot_by_pair(pair)
            if not bot:
                print(f"❌ Could not find bot for {pair}")
                continue
            
            if self.add_threshold_config_to_bot(bot['id'], bot):
                configured_bots += 1
                print(f"✅ Configured {pair} for ±{self.test_threshold} threshold testing")
        
        # Step 5: Create monitoring tools
        monitor_script = self.create_monitoring_script()
        
        # Summary
        print(f"\\n✅ ENHANCED THRESHOLD TESTING SETUP COMPLETE")
        print("=" * 70)
        print(f"📊 Configured bots: {configured_bots}/{len(self.test_pairs)}")
        print(f"💾 Backup created: {backup_path}")
        print(f"📄 Patch file: {patch_path}")
        print(f"🔍 Monitor script: {monitor_script}")
        
        if not self.dry_run and configured_bots > 0:
            print(f"\\n🚀 NEXT STEPS:")
            print(f"1. Restart backend to apply evaluator changes: ./scripts/restart.sh")
            print(f"2. Monitor progress: python {monitor_script}")
            print(f"3. After 72 hours: Analyze results and decide on system-wide implementation")
            print(f"\\n⚠️  IMPORTANT: To rollback, restore from backup: {backup_path}")
        
        return configured_bots > 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    args = parser.parse_args()
    
    tester = EnhancedThresholdTester(dry_run=args.dry_run)
    tester.implement_enhanced_threshold_testing()
