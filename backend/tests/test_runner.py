"""
Test runner script for signal calculation unit tests.

Runs comprehensive signal validation tests:
1. Individual signal accuracy (RSI, MA, MACD)
2. Signal aggregation correctness  
3. Research-recommended configurations
4. Weight distribution effects
5. Edge cases and error handling

Usage:
    python test_runner.py [test_category]
    
Test categories:
    - rsi: Test RSI calculations only
    - ma: Test Moving Average calculations only  
    - macd: Test MACD calculations only
    - aggregation: Test signal aggregation logic
    - configurations: Test research configurations
    - all: Run all tests (default)
"""

import sys
import os
import subprocess
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def run_tests(category: str = "all"):
    """Run specified test category."""
    
    test_files = {
        "rsi": "test_signal_calculations.py::TestRSISignalCalculations",
        "ma": "test_signal_calculations.py::TestMovingAverageSignalCalculations", 
        "macd": "test_signal_calculations.py::TestMACDSignalCalculations",
        "aggregation": "test_signal_calculations.py::TestSignalAggregation",
        "thresholds": "test_signal_calculations.py::TestActionDetermination",
        "configurations": "test_signal_configurations.py::TestResearchRecommendedConfigurations",
        "weights": "test_signal_configurations.py::TestWeightDistributionEffects",
        "edge_cases": "test_signal_calculations.py::TestEdgeCasesAndErrorHandling"
    }
    
    if category == "all":
        # Run all test files
        test_targets = [
            "test_signal_calculations.py",
            "test_signal_configurations.py"
        ]
    elif category in test_files:
        test_targets = [test_files[category]]
    else:
        print(f"Unknown test category: {category}")
        print(f"Available categories: {', '.join(test_files.keys())}, all")
        return False
    
    print(f"🧪 Running signal calculation tests: {category}")
    print("="*60)
    
    success = True
    for target in test_targets:
        print(f"\n📋 Running {target}...")
        
        cmd = [
            "python", "-m", "pytest", 
            target,
            "-v",           # Verbose output
            "-x",           # Stop on first failure  
            "--tb=short",   # Short traceback format
            "--no-header"   # No pytest header
        ]
        
        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {target} - All tests passed!")
                print(result.stdout)
            else:
                print(f"❌ {target} - Some tests failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                success = False
                
        except Exception as e:
            print(f"❌ Error running {target}: {e}")
            success = False
    
    if success:
        print(f"\n🎉 All {category} tests completed successfully!")
        return True
    else:
        print(f"\n💥 Some {category} tests failed. Check output above.")
        return False


def validate_setup():
    """Validate test environment setup."""
    print("🔍 Validating test environment...")
    
    # Check if we can import required modules
    try:
        import pandas as pd
        import numpy as np
        print("✅ pandas and numpy available")
    except ImportError as e:
        print(f"❌ Missing data libraries: {e}")
        return False
    
    try:
        import pytest
        print("✅ pytest available")
    except ImportError:
        print("❌ pytest not installed. Run: pip install pytest")
        return False
    
    # Check if backend modules are importable
    try:
        from backend.app.services.signals.technical import RSISignal, MovingAverageSignal, MACDSignal
        from backend.app.services.bot_evaluator import BotSignalEvaluator
        print("✅ Signal calculation modules available")
    except ImportError as e:
        print(f"❌ Cannot import signal modules: {e}")
        print("Make sure you're running from the correct directory and backend is in Python path")
        return False
    
    print("✅ Test environment validation passed!")
    return True


def main():
    """Main test runner entry point."""
    
    if not validate_setup():
        print("\n❌ Environment validation failed. Cannot run tests.")
        sys.exit(1)
    
    # Parse command line argument
    category = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    # Run tests
    success = run_tests(category)
    
    if success:
        print(f"\n✅ Signal calculation tests completed successfully!")
        print("\n📊 Test Summary:")
        print("- Individual signal calculations verified")
        print("- Signal aggregation logic validated") 
        print("- Research configurations tested")
        print("- Edge cases covered")
        print("\n🚀 Ready to configure bots with confidence!")
    else:
        print(f"\n❌ Some tests failed. Fix issues before configuring bots.")
        sys.exit(1)


if __name__ == "__main__":
    main()
