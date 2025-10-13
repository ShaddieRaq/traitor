#!/usr/bin/env python3
"""
Test cache effectiveness in production Celery environment

This script triggers the breakout scanner task multiple times
to verify that the singleton BreakoutDetector instance maintains
its cache across task runs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import time
from app.tasks.trading_tasks import scan_for_breakouts
from celery.result import AsyncResult

def main():
    print("=" * 80)
    print("🧪 PRODUCTION CACHE EFFECTIVENESS TEST")
    print("=" * 80)
    print("")
    print("Testing singleton BreakoutDetector cache in Celery worker...")
    print("")
    
    # Trigger first scan
    print("1️⃣ Triggering first scan (should fetch from API)...")
    result1 = scan_for_breakouts.delay(create_bots=False, min_confidence="MEDIUM")
    print(f"   Task ID: {result1.id}")
    print(f"   Waiting for result...")
    
    # Wait for completion
    outcome1 = result1.get(timeout=30)
    print(f"   ✅ Result: {outcome1.get('breakouts_detected', 0)} breakouts detected")
    print("")
    
    # Wait 2 seconds
    print("⏰ Waiting 2 seconds...")
    time.sleep(2)
    print("")
    
    # Trigger second scan
    print("2️⃣ Triggering second scan (should use cached data)...")
    result2 = scan_for_breakouts.delay(create_bots=False, min_confidence="MEDIUM")
    print(f"   Task ID: {result2.id}")
    print(f"   Waiting for result...")
    
    # Wait for completion
    outcome2 = result2.get(timeout=30)
    print(f"   ✅ Result: {outcome2.get('breakouts_detected', 0)} breakouts detected")
    print("")
    
    # Wait 2 seconds
    print("⏰ Waiting 2 seconds...")
    time.sleep(2)
    print("")
    
    # Trigger third scan
    print("3️⃣ Triggering third scan (should still use cached data)...")
    result3 = scan_for_breakouts.delay(create_bots=False, min_confidence="MEDIUM")
    print(f"   Task ID: {result3.id}")
    print(f"   Waiting for result...")
    
    # Wait for completion
    outcome3 = result3.get(timeout=30)
    print(f"   ✅ Result: {outcome3.get('breakouts_detected', 0)} breakouts detected")
    print("")
    
    print("=" * 80)
    print("📊 CACHE LOG ANALYSIS")
    print("=" * 80)
    print("")
    print("Check celery-worker.log for cache messages:")
    print("  • 'Fetching fresh products list' = API call made")
    print("  • 'Using cached products list' = Cache hit")
    print("")
    print("Expected pattern:")
    print("  Run 1: Fetching fresh products list")
    print("  Run 2: Using cached products list (within 5 min)")
    print("  Run 3: Using cached products list (within 5 min)")
    print("")
    print("=" * 80)

if __name__ == "__main__":
    main()
