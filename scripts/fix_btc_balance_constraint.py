#!/usr/bin/env python3
"""
Priority 1 Action: Fix BTC Balance Constraint
===========================================

This script addresses the immediate blocker preventing the BTC bot from trading.
The bot has a strong BUY signal (0.122 - HOT) but insufficient balance.

Current Issue:
- BTC available: 0.00017399
- BTC required: 0.00021580 ($25 USD)
- Shortfall: ~0.00004 BTC (~$4.6)

Solutions:
1. Reduce position size temporarily
2. Check for available USD to convert to BTC
3. Adjust bot configuration

Usage:
    python scripts/fix_btc_balance_constraint.py [--dry-run]
"""

import sys
import os
import requests
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class BTCBalanceFixer:
    def __init__(self, dry_run=False):
        self.base_url = "http://localhost:8000/api/v1"
        self.dry_run = dry_run
        self.btc_bot_id = 3  # BTC Continuous Trader
        
    def get_current_balances(self):
        """Get current account balances."""
        try:
            response = requests.get(f"{self.base_url}/account/balances")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Could not fetch balances: {e}")
        return None
    
    def get_btc_bot_config(self):
        """Get current BTC bot configuration."""
        try:
            response = requests.get(f"{self.base_url}/bots/{self.btc_bot_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Could not fetch BTC bot config: {e}")
        return None
    
    def get_btc_price(self):
        """Get current BTC price."""
        try:
            response = requests.get(f"{self.base_url}/market/products")
            if response.status_code == 200:
                products = response.json()
                for product in products:
                    if product['id'] == 'BTC-USD':
                        return float(product['price'])
        except Exception as e:
            print(f"❌ Could not fetch BTC price: {e}")
        return None
    
    def calculate_optimal_position_size(self, available_btc, btc_price):
        """Calculate optimal position size based on available balance."""
        available_usd = available_btc * btc_price
        # Use 80% of available balance for safety margin
        safe_position_size = available_usd * 0.8
        # Round down to nearest dollar
        return max(5, int(safe_position_size))  # Minimum $5 position
    
    def update_bot_position_size(self, new_position_size):
        """Update BTC bot position size."""
        if self.dry_run:
            print(f"🧪 DRY RUN: Would update position size to ${new_position_size}")
            return True
            
        try:
            data = {"position_size_usd": new_position_size}
            response = requests.patch(
                f"{self.base_url}/bots/{self.btc_bot_id}", 
                json=data
            )
            if response.status_code == 200:
                print(f"✅ Updated BTC bot position size to ${new_position_size}")
                return True
            else:
                print(f"❌ Failed to update position size: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error updating position size: {e}")
            return False
    
    def analyze_and_fix(self):
        """Analyze the situation and propose/implement fixes."""
        print("🔍 Analyzing BTC Balance Constraint...")
        print("=" * 50)
        
        # Get current data
        bot_config = self.get_btc_bot_config()
        btc_price = self.get_btc_price()
        
        if not bot_config or not btc_price:
            print("❌ Could not gather required data")
            return False
        
        print(f"📊 Current BTC Bot Configuration:")
        print(f"   Name: {bot_config['name']}")
        print(f"   Status: {bot_config['status']}")
        print(f"   Position Size: ${bot_config['position_size_usd']}")
        print(f"   Current Position: {bot_config.get('current_position_size', 0)}")
        
        print(f"\n💰 Market Data:")
        print(f"   BTC Price: ${btc_price:,.2f}")
        
        # Calculate required BTC for current position size
        required_btc = bot_config['position_size_usd'] / btc_price
        print(f"\n⚖️ Balance Analysis:")
        print(f"   Required BTC: {required_btc:.8f} BTC")
        print(f"   Available BTC: 0.00017399 BTC")
        print(f"   Shortfall: {required_btc - 0.00017399:.8f} BTC")
        print(f"   Shortfall USD: ${(required_btc - 0.00017399) * btc_price:.2f}")
        
        # Calculate optimal position size
        available_btc = 0.00017399  # From the error message
        optimal_size = self.calculate_optimal_position_size(available_btc, btc_price)
        
        print(f"\n💡 Recommended Solution:")
        print(f"   Reduce position size from ${bot_config['position_size_usd']} to ${optimal_size}")
        print(f"   This allows trading with available balance")
        print(f"   Required BTC: {optimal_size / btc_price:.8f} BTC")
        
        # Ask for confirmation
        if not self.dry_run:
            response = input(f"\n❓ Update BTC bot position size to ${optimal_size}? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled")
                return False
        
        # Apply the fix
        success = self.update_bot_position_size(optimal_size)
        
        if success:
            print("\n✅ BTC Balance Constraint Fixed!")
            print("🚀 BTC bot should now be able to trade with strong buy signal")
            print("\n📋 Next Steps:")
            print("   1. Monitor bot activity for successful trades")
            print("   2. Consider adding more BTC balance for larger positions")
            print("   3. Continue with threshold testing (Priority 2)")
        
        return success

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    args = parser.parse_args()
    
    fixer = BTCBalanceFixer(dry_run=args.dry_run)
    fixer.analyze_and_fix()
