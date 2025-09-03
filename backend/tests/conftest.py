"""
Test configuration and fixtures.
"""

import pytest
from app.core.config import Settings


@pytest.fixture
def test_settings():
    """Test settings for live Coinbase testing."""
    return Settings()

import pytest
import os
import sys
from unittest.mock import Mock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_coinbase_client():
    """Mock Coinbase client for testing without API calls."""
    mock_client = Mock()
    
    # Mock common methods
    mock_client.get_accounts.return_value = Mock(
        accounts=[
            Mock(currency='USD', available_balance=Mock(value='1000.00')),
            Mock(currency='BTC', available_balance=Mock(value='0.01'))
        ]
    )
    
    mock_client.get_products.return_value = Mock(
        products=[
            Mock(product_id='BTC-USD', price='50000.00', status='online'),
            Mock(product_id='ETH-USD', price='3000.00', status='online')
        ]
    )
    
    mock_client.get_product.return_value = Mock(
        product_id='BTC-USD',
        price='50000.00',
        volume_24h='1000000'
    )
    
    return mock_client

@pytest.fixture
def test_settings():
    """Test settings that don't require real API credentials."""
    from app.core.config import Settings
    
    return Settings(
        coinbase_api_key="test_key",
        coinbase_api_secret="test_secret",
        database_url="sqlite:///./test.db",
        redis_url="redis://localhost:6379/1",
        environment="test"
    )


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for testing."""
    from app.core.database import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.models import Base
    
    # Create test database
    engine = create_engine("sqlite:///./test_signal_confirmation.db")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up test database
        import os
        if os.path.exists("./test_signal_confirmation.db"):
            os.remove("./test_signal_confirmation.db")
