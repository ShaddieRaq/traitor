#!/usr/bin/env python3
"""
Test script to debug the trends API error.
This will help isolate where the error is occurring.
"""

import sys
import os
import traceback

# Add the backend directory to Python path
sys.path.insert(0, '/Users/lazy_genius/Projects/trader/backend')

def test_trend_engine():
    """Test the trend detection engine directly."""
    try:
        print("🔍 Testing trend detection engine...")
        
        # Test import
        print("1. Testing import...")
        from app.services.trend_detection_engine import get_trend_engine
        print("✅ Import successful")
        
        # Test initialization
        print("2. Testing initialization...")
        trend_engine = get_trend_engine()
        print(f"✅ Engine initialized: {type(trend_engine)}")
        
        # Test analyze_trend method
        print("3. Testing analyze_trend method...")
        result = trend_engine.analyze_trend("BTC-USD")
        print(f"✅ Analysis successful: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in trend engine test: {e}")
        print(f"📋 Traceback:")
        traceback.print_exc()
        return False

def test_api_import():
    """Test the API imports."""
    try:
        print("🔍 Testing API imports...")
        
        # Test trends API import
        print("1. Testing trends API import...")
        from app.api.trends import router
        print(f"✅ API import successful: {type(router)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in API import test: {e}")
        print(f"📋 Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Debugging trends API error...")
    print("=" * 50)
    
    # Test 1: API imports
    api_success = test_api_import()
    print()
    
    # Test 2: Trend engine
    engine_success = test_trend_engine()
    print()
    
    if api_success and engine_success:
        print("🎉 All tests passed - the error might be elsewhere")
    else:
        print("💥 Found the source of the error")
        sys.exit(1)