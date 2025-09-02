"""
Trading Bot Backend Tests

This package contains tests for the trading bot backend functionality.

Test Structure:
- test_api.py: API endpoint tests
- test_coinbase.py: Coinbase integration tests  
- test_signals.py: Signal processing tests
- conftest.py: Test configuration and fixtures

Usage:
    # Run all tests
    ./scripts/test.sh
    
    # Run with coverage
    ./scripts/test.sh --coverage
    
    # Run only unit tests
    ./scripts/test.sh --unit
    
    # Run only integration tests (requires Coinbase credentials)
    ./scripts/test.sh --integration
"""
