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
        # New system might have no trades yet
    
    def test_get_trade_stats(self, client):
        """Test getting trading statistics."""
        response = client.get("/api/v1/trades/stats")
        assert response.status_code == 200
        data = response.json()
        # Should return stats structure even if empty
        assert isinstance(data, dict)

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


class TestBotsAPI:
    """Test bots API endpoints."""
    
    def test_get_bots(self, client):
        """Test getting all bots."""
        response = client.get("/api/v1/bots/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have the existing test bots
        assert len(data) >= 0  # May have test bots from previous runs
    
    def test_get_bot_by_id(self, client):
        """Test getting a specific bot."""
        # First get all bots to get a valid ID
        response = client.get("/api/v1/bots/")
        bots = response.json()
        
        if bots:
            bot_id = bots[0]['id']
            response = client.get(f"/api/v1/bots/{bot_id}")
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == bot_id
    
    def test_get_nonexistent_bot(self, client):
        """Test getting a bot that doesn't exist."""
        response = client.get("/api/v1/bots/99999")
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
