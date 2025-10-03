# Service Testing & Parameter Strategy
## Ensuring Services Actually Work Together

### **Testing Philosophy**

**Rule 1:** Every service interaction must have integration tests  
**Rule 2:** All parameters must have documented valid ranges and fallback values  
**Rule 3:** Test failure scenarios, not just happy paths  

---

## **Service Parameter Specifications**

### **Market Data Gateway Parameters**

```python
class MarketDataConfig:
    # API Rate Limiting
    COINBASE_REQUESTS_PER_SECOND: int = 10  # Coinbase limit
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 600  # 10 req/sec * 60 sec
    
    # Caching
    PRICE_CACHE_TTL_SECONDS: int = 30  # Real-time pricing
    OHLCV_CACHE_TTL_SECONDS: int = 300  # 5 min historical data
    REDIS_CONNECTION_TIMEOUT: int = 5
    
    # Retries & Timeouts
    COINBASE_REQUEST_TIMEOUT: int = 10
    COINBASE_MAX_RETRIES: int = 3
    COINBASE_RETRY_BACKOFF: float = 1.5  # Exponential backoff
    
    # Data Validation
    MAX_PRICE_DEVIATION_PERCENT: float = 10.0  # Price sanity check
    MIN_VOLUME_THRESHOLD: float = 1000.0  # Ignore low volume periods
    
    # Health Check
    HEALTH_CHECK_SYMBOLS: List[str] = ["BTC-USD", "ETH-USD"]
    HEALTH_CHECK_TIMEOUT: int = 5
```

### **Regime Detection Parameters**

```python
class RegimeDetectionConfig:
    # Technical Indicators
    ADX_PERIOD: int = 14  # Standard ADX calculation
    ADX_TRENDING_THRESHOLD: float = 25.0  # Above = trending
    ADX_RANGING_THRESHOLD: float = 20.0   # Below = ranging
    
    CHOPPINESS_PERIOD: int = 20
    CHOPPINESS_CHOPPY_THRESHOLD: float = 61.8  # Above = choppy
    CHOPPINESS_TRENDING_THRESHOLD: float = 38.2  # Below = trending
    
    VOLATILITY_WINDOW: int = 20  # ATR calculation period
    VOLATILITY_HIGH_THRESHOLD: float = 0.05  # 5% daily volatility
    VOLATILITY_LOW_THRESHOLD: float = 0.02   # 2% daily volatility
    
    # Regime Classification
    REGIME_CONFIDENCE_THRESHOLD: float = 0.7  # Minimum confidence to classify
    REGIME_CACHE_TTL_SECONDS: int = 900  # 15 minutes
    
    # Crisis Detection
    CORRELATION_SPIKE_THRESHOLD: float = 0.9  # All assets moving together
    VOLUME_ANOMALY_MULTIPLIER: float = 3.0   # 3x average volume
    
    # Data Requirements
    MIN_PERIODS_REQUIRED: int = 60  # Need 60 periods for reliable signals
    MARKET_DATA_TIMEOUT: int = 5
```

### **Risk Management Parameters**

```python
class RiskManagementConfig:
    # Position Sizing
    MAX_POSITION_SIZE_PERCENT: float = 0.20  # 20% of portfolio max
    KELLY_FRACTION_MULTIPLIER: float = 0.25  # Use 1/4 Kelly for safety
    MIN_POSITION_SIZE_USD: float = 100.0
    MAX_POSITION_SIZE_USD: float = 50000.0
    
    # Portfolio Risk
    MAX_PORTFOLIO_VAR_PERCENT: float = 0.05  # 5% daily VaR limit
    MAX_CONCENTRATION_PERCENT: float = 0.30  # 30% in single asset max
    MAX_CORRELATION_THRESHOLD: float = 0.70  # Alert if portfolio corr > 70%
    
    # Regime-Based Adjustments
    REGIME_MULTIPLIERS = {
        "TRENDING": 1.0,     # Normal position sizing
        "RANGING": 0.8,      # Reduce positions 20%
        "CHOPPY": 0.5,       # Reduce positions 50%
        "CRISIS": 0.1        # Emergency - tiny positions only
    }
    
    # Risk Calculations
    VAR_CONFIDENCE_LEVEL: float = 0.95  # 95% VaR
    VAR_LOOKBACK_DAYS: int = 252        # 1 year historical data
    STRESS_TEST_SCENARIOS: int = 10     # Number of stress scenarios
    
    # Circuit Breakers
    MAX_DAILY_LOSS_PERCENT: float = 0.05    # Stop trading at 5% daily loss
    MAX_DRAWDOWN_PERCENT: float = 0.15      # Stop at 15% total drawdown
    COOLING_OFF_PERIOD_HOURS: int = 24      # Wait before resuming
```

### **Execution Service Parameters**

```python
class ExecutionConfig:
    # Order Sizing
    SMALL_ORDER_THRESHOLD_USD: float = 1000.0   # Market order
    LARGE_ORDER_THRESHOLD_USD: float = 5000.0   # TWAP required
    
    # Execution Algorithms
    TWAP_DURATION_MINUTES: int = 10       # Spread large orders over time
    TWAP_SLICE_COUNT: int = 5             # Number of child orders
    LIMIT_ORDER_SPREAD_THRESHOLD: float = 0.002  # 0.2% max spread for limits
    
    # Maker/Taker Optimization
    TARGET_MAKER_RATIO: float = 0.60      # 60% maker orders target
    MAKER_ORDER_TIMEOUT_SECONDS: int = 30 # Cancel unfilled limit orders
    
    # Cost Calculation
    COINBASE_TAKER_FEE: float = 0.005     # 0.5%
    COINBASE_MAKER_FEE: float = 0.005     # 0.5% (varies by volume)
    ESTIMATED_SLIPPAGE_BPS: float = 5.0   # 5 basis points avg slippage
    
    # Risk Integration
    RISK_CHECK_TIMEOUT: int = 3           # Max time for risk approval
    RISK_CHECK_RETRIES: int = 2
```

---

## **Service Integration Tests**

### **Test 1: Full Trading Flow**

```python
class TestTradingFlow:
    """Test complete flow from market data to trade execution"""
    
    async def test_successful_trade_execution(self):
        """Happy path: All services working, trade approved and executed"""
        
        # 1. Market Data Gateway responds with valid data
        market_data_mock = {
            "symbol": "BTC-USD",
            "price": 45000.0,
            "timestamp": "2025-10-03T10:30:00Z"
        }
        
        # 2. Regime Detection classifies as TRENDING
        regime_mock = {
            "symbol": "BTC-USD", 
            "regime": "TRENDING",
            "confidence": 0.85
        }
        
        # 3. Risk Management approves trade
        risk_approval_mock = {
            "approved": True,
            "max_amount": 1000.0,
            "adjusted_amount": 800.0  # Reduced for risk
        }
        
        # 4. Execution Service places order
        execution_result = await execute_trade({
            "symbol": "BTC-USD",
            "side": "buy", 
            "amount": 1000.0
        })
        
        assert execution_result["status"] == "filled"
        assert execution_result["executed_amount"] == 800.0  # Risk-adjusted
        
    async def test_regime_crisis_blocks_trade(self):
        """Crisis regime should block new trades"""
        
        # Force CRISIS regime
        regime_mock = {"regime": "CRISIS", "confidence": 0.95}
        
        risk_approval = await risk_service.approve_trade({
            "symbol": "BTC-USD",
            "amount": 1000.0
        })
        
        assert risk_approval["approved"] == False
        assert "CRISIS" in risk_approval["reason"]
        
    async def test_market_data_failure_fallback(self):
        """Market data service down - should use fallback"""
        
        # Mock market data service failure
        with mock_service_down("market_data"):
            
            regime_result = await regime_service.get_regime("BTC-USD")
            
            # Should return UNKNOWN regime with low confidence
            assert regime_result["regime"] == "UNKNOWN" 
            assert regime_result["confidence"] < 0.5
```

### **Test 2: Service Communication Resilience**

```python
class TestServiceResilience:
    """Test service interactions under failure conditions"""
    
    async def test_circuit_breaker_opens(self):
        """Circuit breaker should open after repeated failures"""
        
        # Simulate 5 consecutive failures
        for i in range(5):
            with pytest.raises(ServiceUnavailableError):
                await regime_service.get_regime("BTC-USD")
        
        # Circuit breaker should now be OPEN
        assert regime_service.circuit_breaker.state == "OPEN"
        
        # Next call should fail immediately without hitting service
        start_time = time.time()
        with pytest.raises(ServiceUnavailableError):
            await regime_service.get_regime("BTC-USD")
        
        # Should fail quickly (< 100ms) not wait for timeout
        assert (time.time() - start_time) < 0.1
        
    async def test_service_discovery_update(self):
        """Services should handle endpoint changes"""
        
        # Start with localhost
        assert regime_service.market_data_url == "http://localhost:8001"
        
        # Update service discovery
        update_service_endpoint("market_data", "http://market-data:8001")
        
        # Service should pick up new endpoint
        assert regime_service.market_data_url == "http://market-data:8001"
        
    async def test_timeout_handling(self):
        """Services should timeout appropriately"""
        
        # Mock slow response (6 seconds)
        with mock_slow_response("market_data", delay=6):
            start_time = time.time()
            
            with pytest.raises(TimeoutError):
                await regime_service.get_regime("BTC-USD")
            
            # Should timeout in ~5 seconds (configured timeout)
            elapsed = time.time() - start_time
            assert 4.5 < elapsed < 5.5
```

### **Test 3: Parameter Validation**

```python
class TestParameterValidation:
    """Test parameter ranges and validation"""
    
    def test_regime_parameters_valid_ranges(self):
        """All regime detection parameters in valid ranges"""
        
        config = RegimeDetectionConfig()
        
        # ADX thresholds should be logical
        assert config.ADX_RANGING_THRESHOLD < config.ADX_TRENDING_THRESHOLD
        assert 0 < config.ADX_RANGING_THRESHOLD < 50
        assert 0 < config.ADX_TRENDING_THRESHOLD < 50
        
        # Choppiness thresholds should be logical  
        assert config.CHOPPINESS_TRENDING_THRESHOLD < config.CHOPPINESS_CHOPPY_THRESHOLD
        assert 0 < config.CHOPPINESS_TRENDING_THRESHOLD < 100
        assert 0 < config.CHOPPINESS_CHOPPY_THRESHOLD < 100
        
        # Periods should be reasonable
        assert config.MIN_PERIODS_REQUIRED > max(config.ADX_PERIOD, config.CHOPPINESS_PERIOD)
        
    def test_risk_parameters_sensible(self):
        """Risk parameters should prevent blow-ups"""
        
        config = RiskManagementConfig()
        
        # Position sizing constraints
        assert 0 < config.MAX_POSITION_SIZE_PERCENT <= 0.5  # Never > 50%
        assert 0 < config.KELLY_FRACTION_MULTIPLIER <= 0.5  # Conservative Kelly
        
        # Portfolio constraints
        assert 0 < config.MAX_PORTFOLIO_VAR_PERCENT <= 0.10  # Never > 10% VaR
        assert 0 < config.MAX_CONCENTRATION_PERCENT <= 0.50  # Never > 50% in one asset
        
        # Regime multipliers should reduce risk
        assert all(0 < mult <= 1.0 for mult in config.REGIME_MULTIPLIERS.values())
        assert config.REGIME_MULTIPLIERS["CRISIS"] <= 0.2  # Very small in crisis
```

### **Test 4: Performance & Load Testing**

```python
class TestPerformance:
    """Test services under load"""
    
    async def test_market_data_throughput(self):
        """Market data should handle expected load"""
        
        # 100 concurrent requests
        tasks = []
        for i in range(100):
            task = asyncio.create_task(
                market_data_service.get_price("BTC-USD")
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Should complete in < 2 seconds (with caching)
        assert elapsed < 2.0
        assert all(r["price"] > 0 for r in results)
        
    async def test_regime_detection_latency(self):
        """Regime detection should be fast enough for trading"""
        
        # Single regime detection should be < 1 second
        start_time = time.time()
        regime = await regime_service.get_regime("BTC-USD")
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0
        assert regime["regime"] in ["TRENDING", "RANGING", "CHOPPY", "CRISIS", "UNKNOWN"]
```

---

## **Test Environment Setup**

### **Docker Compose for Testing**

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  market-data-test:
    build: ./market-data-gateway
    environment:
      - TESTING=true
      - REDIS_URL=redis://redis-test:6379
      - COINBASE_MOCK=true  # Use mock responses
    depends_on: [redis-test]
    
  regime-test:
    build: ./regime-detection
    environment:
      - TESTING=true
      - MARKET_DATA_URL=http://market-data-test:8001
    depends_on: [market-data-test]
    
  redis-test:
    image: redis:alpine
    
  test-runner:
    build: ./tests
    volumes:
      - ./tests:/app/tests
    command: pytest tests/ -v
    depends_on: [market-data-test, regime-test]
```

### **CI/CD Integration Tests**

```bash
#!/bin/bash
# run_integration_tests.sh

set -e

echo "Starting test environment..."
docker-compose -f docker-compose.test.yml up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Running integration tests..."
docker-compose -f docker-compose.test.yml run test-runner

echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down
```

---

## **Success Criteria**

### **Service Quality Gates**

Each service must pass:
1. **Unit Tests**: >90% coverage
2. **Integration Tests**: All service interactions tested
3. **Performance Tests**: Meet latency/throughput requirements
4. **Resilience Tests**: Handle failures gracefully
5. **Parameter Validation**: All config ranges validated

### **System-Level Gates**

Before production deployment:
1. **End-to-End Tests**: Complete trading flows work
2. **Chaos Testing**: Services recover from random failures  
3. **Load Testing**: Handle expected production traffic
4. **Security Testing**: No exposed credentials or vulnerabilities

This testing strategy ensures services actually work together instead of just working in isolation.