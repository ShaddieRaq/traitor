#!/usr/bin/env python3
"""
Threshold Test Monitoring - Generated 2025-09-20T14:40:52.960955
=====================================================

Monitors performance of test bots vs original bots for threshold validation.
Test Duration: 72 hours
Test Threshold: ±0.05
Control Threshold: ±0.1

Test Bots:
[
  {
    "id": -1,
    "name": "ETH Continuous Trader_TEST_005"
  },
  {
    "id": -1,
    "name": "Auto-Avalanche-USD Bot_TEST_005"
  },
  {
    "id": -1,
    "name": "Auto-Toshi-USD Bot_TEST_005"
  }
]
"""

import requests
import json
from datetime import datetime

def monitor_test_performance():
    base_url = "http://localhost:8000/api/v1"
    
    # Get current status of all bots
    response = requests.get(f"{base_url}/bots/status/enhanced")
    if response.status_code == 200:
        bots = response.json()
        
        print(f"\n📊 THRESHOLD TEST MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        test_bots = [bot for bot in bots if "_TEST_005" in bot.get('name', '')]
        control_bots = [bot for bot in bots if bot['pair'] in ['ETH-USD', 'AVAX-USD', 'TOSHI-USD'] and "_TEST_005" not in bot.get('name', '')]
        
        print(f"\n🧪 TEST BOTS (±0.05 threshold):")
        for bot in test_bots:
            print(f"   {bot['pair']}: Score={bot['current_combined_score']:.4f}, Status={bot['status']}, Temp={bot['temperature']}")
        
        print(f"\n🎯 CONTROL BOTS (±0.1 threshold):")
        for bot in control_bots:
            print(f"   {bot['pair']}: Score={bot['current_combined_score']:.4f}, Status={bot['status']}, Temp={bot['temperature']}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    monitor_test_performance()
