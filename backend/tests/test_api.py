"""
Test API endpoints - Live API testing.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestSignalsAPI:
    """Test signals API endpoints."""
    
    def test_get_signals(self, client):
        """Test getting all signals."""
        response = client.get("/api/v1/signals/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the default signals
        assert len(data) >= 2
    
    def test_get_signal_by_id(self, client):
        """Test getting a specific signal."""
        # First get all signals to get a valid ID
        response = client.get("/api/v1/signals/")
        signals = response.json()
        
        if signals:
            signal_id = signals[0]['id']
            response = client.get(f"/api/v1/signals/{signal_id}")
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == signal_id
    
    def test_get_nonexistent_signal(self, client):
        """Test getting a signal that doesn't exist."""
        response = client.get("/api/v1/signals/99999")
        assert response.status_code == 404


class TestMarketAPI:
    """Test market data API endpoints with live Coinbase data."""
    
    def test_get_products(self, client):
        """Test getting market products from live API."""
        response = client.get("/api/v1/market/products")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        
        # Should get many products from live API
        assert len(data['products']) > 100  # Live API has hundreds of products
        
        # Check structure of first product
        if data['products']:
            product = data['products'][0]
            # Products should have at least these fields
            assert 'product_id' in product or hasattr(product, 'product_id')
    
    def test_get_ticker(self, client):
        """Test getting ticker for a product from live API."""
        response = client.get("/api/v1/market/ticker/BTC-USD")
        assert response.status_code == 200
        data = response.json()
        
        assert data['product_id'] == 'BTC-USD'
        assert 'price' in data
        assert isinstance(data['price'], (int, float))
        assert data['price'] > 0  # BTC should have a positive price
    
    def test_get_accounts(self, client):
        """Test getting account data from live API."""
        response = client.get("/api/v1/market/accounts")
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list (may be empty for new accounts)
        assert isinstance(data, list)


class TestTradesAPI:
    """Test trades API endpoints."""
    
    def test_get_trades(self, client):
        """Test getting trade history."""
        response = client.get("/api/v1/trades/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_trade_stats(self, client):
        """Test getting trading statistics."""
        response = client.get("/api/v1/trades/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        data = response.json()
        assert isinstance(data, list)
        # New system might have no trades yet
    
    def test_get_trade_stats(self, client):
        """Test getting trade statistics."""
        response = client.get("/api/v1/trades/stats")
        assert response.status_code == 200
        data = response.json()
        # Should return stats structure even if empty
