#!/usr/bin/env python3
"""
Test script for Phase 6.1 centralized data management architecture.
Validates Redis connectivity, cache operations, and API coordination.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.shared_cache_service import SharedCacheManager, data_distribution_service
from app.services.api_coordinator import api_coordinator, coordinated_get_ticker
from app.core.config import settings


async def test_redis_connectivity():
    """Test basic Redis connectivity."""
    print("🔍 Testing Redis connectivity...")
    
    try:
        cache_manager = SharedCacheManager()
        if cache_manager.redis_client:
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False


async def test_cache_operations():
    """Test basic cache set/get operations."""
    print("\n🔍 Testing cache operations...")
    
    try:
        from app.services.shared_cache_service import DataType
        
        # Test simple cache operation
        test_data = {"test": "data", "timestamp": "2025-01-27"}
        success = await data_distribution_service.cache_manager.set(
            data_type=DataType.TICKER,
            data=test_data,
            product_id="BTC-USD"
        )
        
        if not success:
            print("❌ Cache set operation failed")
            return False
        
        retrieved = await data_distribution_service.cache_manager.get(
            data_type=DataType.TICKER,
            product_id="BTC-USD"
        )
        
        if retrieved and retrieved.get("test") == "data":
            print("✅ Cache operations successful")
            return True
        else:
            print("❌ Cache operations failed - no data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Cache operations error: {e}")
        return False


async def test_api_coordination():
    """Test API coordination system."""
    print("\n🔍 Testing API coordination...")
    
    try:
        # Test coordinated API call with shorter timeout
        print("   Submitting coordinated ticker request...")
        
        # Use asyncio.wait_for to add our own timeout
        result = await asyncio.wait_for(
            coordinated_get_ticker("BTC-USD"), 
            timeout=10.0  # 10 second timeout instead of 30
        )
        
        if result:
            print("✅ API coordination successful")
            print(f"   Sample result: {str(result)[:100]}...")
            return True
        else:
            print("❌ API coordination failed - no result")
            return False
            
    except asyncio.TimeoutError:
        print("⏰ API coordination timed out - coordinator may not be processing requests")
        return False
    except Exception as e:
        print(f"❌ API coordination error: {e}")
        return False


async def main():
    """Run all validation tests."""
    print("🚀 Phase 6.1 Centralized Data Management - Validation Tests")
    print("=" * 60)
    
    tests = [
        ("Redis Connectivity", test_redis_connectivity),
        ("Cache Operations", test_cache_operations), 
        ("API Coordination", test_api_coordination)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Phase 6.1 architecture ready for deployment!")
        print("   Next steps: Migrate bots to use coordinated API calls")
    else:
        print("\n⚠️  SOME TESTS FAILED - Fix issues before proceeding")
        print("   Review error messages above and fix configuration")
        
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)