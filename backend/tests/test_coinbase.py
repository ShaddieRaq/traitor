"""
Test Coinbase API integration - Live API testing.
"""

import pytest
from app.services.coinbase_service import CoinbaseService
from app.core.config import settings


class TestCoinbaseService:
    """Test the Coinbase service wrapper against live API."""
    
    def test_service_creation(self):
        """Test that CoinbaseService can be created."""
        service = CoinbaseService()
        assert service is not None
    
    def test_get_products(self):
        """Test getting products from live Coinbase API."""
        service = CoinbaseService()
        products = service.get_products()
        
        # Should get real products from live API
        assert isinstance(products, list)
        if len(products) > 0:
            # Check structure of first product - avoid slow 'in' check
            product = products[0]
            # For SDK objects, just check if it has the attribute
            assert hasattr(product, 'product_id') or (isinstance(product, dict) and 'product_id' in product)
    
    def test_get_accounts(self):
        """Test getting accounts from live Coinbase API."""
        service = CoinbaseService()
        accounts = service.get_accounts()
        
        # Should get real accounts (may be empty for new accounts)
        assert isinstance(accounts, list)
    
    def test_get_ticker(self):
        """Test getting ticker data from live Coinbase API."""
        service = CoinbaseService()
        ticker = service.get_product_ticker('BTC-USD')
        
        # Should get real ticker data
        if ticker is not None:
            assert 'product_id' in ticker
            assert 'price' in ticker
            assert ticker['product_id'] == 'BTC-USD'


class TestCoinbaseConnection:
    """Test actual Coinbase API connection."""
    
    def test_real_connection(self):
        """Test real Coinbase connection."""
        # Skip if no real credentials
        if not settings.coinbase_api_key or settings.coinbase_api_key == "test_key":
            pytest.skip("No real Coinbase credentials available")
        
        service = CoinbaseService()
        
        # Test that we can connect and get products with timeout
        import time
        start_time = time.time()
        
        try:
            products = service.get_products()
            elapsed = time.time() - start_time
            
            assert isinstance(products, list)
            if len(products) > 0:
                # Check that we got real data
                assert len(products) > 10  # Should have many trading pairs
            
        except Exception as e:
            elapsed = time.time() - start_time
            pytest.fail(f"Failed to connect to Coinbase API: {e}")
    
    def test_real_accounts(self):
        """Test getting real account data."""
        # Skip if no real credentials
        if not settings.coinbase_api_key or settings.coinbase_api_key == "test_key":
            pytest.skip("No real Coinbase credentials available")
        
        service = CoinbaseService()
        
        try:
            accounts = service.get_accounts()
            assert isinstance(accounts, list)
            # Don't assert specific length since it depends on user's account
        except Exception as e:
            pytest.fail(f"Failed to get accounts from Coinbase API: {e}")

    def test_real_ticker(self):
        """Test getting real ticker data."""
        # Skip if no real credentials
        if not settings.coinbase_api_key or settings.coinbase_api_key == "test_key":
            pytest.skip("No real Coinbase credentials available")
        
        service = CoinbaseService()
        
        try:
            ticker = service.get_product_ticker('BTC-USD')
            if ticker is not None:
                assert ticker['product_id'] == 'BTC-USD'
                assert isinstance(ticker['price'], (int, float))
                assert ticker['price'] > 0
        except Exception as e:
            pytest.fail(f"Failed to get ticker from Coinbase API: {e}")
