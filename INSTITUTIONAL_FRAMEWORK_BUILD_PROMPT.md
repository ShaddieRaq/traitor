# 🎯 INSTITUTIONAL TRADING FRAMEWORK BUILD PROMPT
## Based on $XXX Research Investment - Implement What Actually Works

**Mission:** Build the exact institutional trading framework we researched - regime-aware, correlation-adjusted, transaction-cost-optimized strategies that major firms use to generate consistent profits.

**Rule #1:** NO SCOPE CREEP. Build exactly what's defined below.  
**Rule #2:** NO FEATURE ADDITIONS until core framework is complete and profitable.  
**Rule #3:** MEASURE EVERYTHING against institutional benchmarks.

---

## 🏛️ **INSTITUTIONAL FRAMEWORK REQUIREMENTS**
*Based on research into Goldman Sachs, Citadel, Two Sigma trading systems*

### **Core Framework Components (FIXED SCOPE):**

#### **1. Market Regime Detection Engine** 🌡️
**Purpose:** Stop trading the same strategy in all market conditions (current system's #1 flaw)

**EXACT Implementation:**
```python
class RegimeEngine:
    def classify_regime(self, symbol: str) -> RegimeType:
        """
        TRENDING: ADX > 25 AND Choppiness < 38.2
        RANGING: ADX < 20 AND volatility stable  
        CHOPPY: Choppiness > 61.8 AND high ATR
        CRISIS: Correlation spike > 0.9 AND volume anomaly
        """
        
    def get_strategy_allocation(self, regime: RegimeType) -> Dict[str, float]:
        """
        TRENDING: 60% momentum, 30% trend-following, 10% arbitrage
        RANGING: 50% mean-reversion, 30% pairs-trading, 20% arbitrage  
        CHOPPY: 40% arbitrage, 40% cash, 20% short-term scalping
        CRISIS: 70% cash, 20% arbitrage, 10% emergency liquidation
        """
```

**Success Metric:** >80% regime classification accuracy vs manual labeling

#### **2. Correlation-Adjusted Position Sizing** 🔗
**Purpose:** Stop treating crypto pairs as independent (current system treats 34 pairs as diversified)

**EXACT Implementation:**
```python
class CorrelationEngine:
    def calculate_position_size(self, base_size: float, symbol: str, portfolio: Portfolio) -> float:
        """
        Formula from research: effective_size = base_size * (1 - correlation_to_portfolio)
        
        If BTC-USD and ETH-USD correlation = 0.8:
        - Don't allocate $50 to each ($100 total exposure) 
        - Allocate $50 * (1-0.8) = $10 to ETH-USD
        - Total effective exposure = $60 instead of $100
        """
        
    def portfolio_heat_check(self, portfolio: Portfolio) -> float:
        """
        Calculate true portfolio VaR using correlation matrix
        Alert if effective concentration > 15% of capital in one factor
        """
```

**Success Metric:** Reduce portfolio correlation to BTC from >0.8 to <0.3

#### **3. Transaction Cost Optimization** 💰
**Purpose:** Preserve trading edge (current system ignores 0.1-0.5% fees eating profits)

**EXACT Implementation:**
```python
class ExecutionEngine:
    def optimize_execution(self, order: Order, market_conditions: MarketState) -> ExecutionStrategy:
        """
        SMALL ORDERS (<$1000): Market order (speed over cost)
        MEDIUM ORDERS ($1000-$5000): Limit order if spread <0.2%, else TWAP
        LARGE ORDERS (>$5000): TWAP over 5-15 minutes
        
        TARGET: 60%+ maker orders (vs current 0% maker ratio)
        """
        
    def calculate_total_cost(self, order: Order) -> CostBreakdown:
        """
        fees: 0.1-0.5% (explicit)
        spread: 0.05-0.3% (half-spread cost)  
        slippage: 0.01-0.1% (market impact)
        timing: 0.02-0.05% (delay cost)
        """
```

**Success Metric:** 40%+ reduction in total trading costs vs current naive market orders

#### **4. Risk Management Framework** 🛡️
**Purpose:** Institutional capital protection (current system has no risk controls)

**EXACT Implementation:**
```python
class RiskEngine:
    def calculate_kelly_size(self, strategy_edge: float, win_rate: float) -> float:
        """
        Kelly fraction = (win_rate - loss_rate/odds) 
        Use 1/4 Kelly for safety: kelly_fraction * 0.25
        """
        
    def portfolio_var(self, portfolio: Portfolio, confidence: float = 0.95) -> float:
        """
        Daily VaR using historical simulation + correlation matrix
        TARGET: 95% VaR < 5% of portfolio value
        """
        
    def stress_test(self, portfolio: Portfolio) -> Dict[str, float]:
        """
        BTC -50% scenario: Max loss < 10% of portfolio
        Correlation spike to 0.95: Position sizing adjustment
        Exchange hack: Isolated loss < 5% of portfolio
        """
```

**Success Metrics:** 
- Max drawdown <10% (vs current >15%)
- Daily VaR <5% of portfolio
- Stress test losses <10% in worst case

---

## 📊 **STRATEGY IMPLEMENTATION FRAMEWORK**
*Based on research into successful institutional strategies*

### **Market-Neutral Strategy Suite:**

#### **Strategy 1: Statistical Arbitrage** 📈📉
**Research Basis:** ETH/BTC ratio mean reversion (documented success at major firms)
```python
class StatArbStrategy:
    def __init__(self):
        self.pair = "ETH/BTC"
        self.lookback_period = 60  # days
        self.entry_threshold = 2.0  # standard deviations
        self.exit_threshold = 0.5
        self.stop_loss = 4.0
        
    def generate_signal(self) -> Signal:
        """
        Long ETH, Short BTC when ratio < mean - 2*std
        Short ETH, Long BTC when ratio > mean + 2*std
        Target: Market-neutral, Sharpe >2.0
        """
```

#### **Strategy 2: Cross-Exchange Arbitrage** 🔄
**Research Basis:** Price discrepancies between Coinbase/Binance/Kraken
```python
class ArbitrageStrategy:
    def scan_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Monitor BTC-USD price across exchanges
        Execute when spread > 0.5% after fees
        Target: Low-risk, steady income stream
        """
```

#### **Strategy 3: Volatility Trading** 📊
**Research Basis:** Profit from volatility spikes regardless of direction
```python
class VolatilityStrategy:
    def trade_volatility_breakouts(self) -> Signal:
        """
        Detect vol regime changes using GARCH
        Trade straddles around major events
        Target: Direction-agnostic profits
        """
```

---

## 🎯 **CONCRETE IMPLEMENTATION PLAN**

### **Phase 1: Core Framework (Weeks 1-4)**
**NO OTHER WORK until this is complete**

#### **Week 1: Regime Detection**
- [ ] Build ADX, Choppiness Index, ATR calculators
- [ ] Implement 4-regime classification (TRENDING/RANGING/CHOPPY/CRISIS)
- [ ] Test on 3 years historical data
- [ ] Deploy regime API: `GET /regime/current/{symbol}`

**Acceptance Criteria:**
- 80%+ classification accuracy vs manual labeling
- <5 second classification time
- Real-time regime updates every 15 minutes

#### **Week 2: Correlation Engine**
- [ ] Build dynamic correlation matrix (30-day rolling)
- [ ] Implement PCA analysis for factor identification
- [ ] Build position sizing adjustment algorithm
- [ ] Deploy correlation API: `GET /correlation/matrix`

**Acceptance Criteria:**
- Correlation matrix updates every hour
- Position sizing reduces effective portfolio correlation <0.5
- Portfolio heat check prevents >15% concentration

#### **Week 3: Risk Management**
- [ ] Implement VaR calculation (historical simulation)
- [ ] Build Kelly criterion position sizing
- [ ] Create stress testing scenarios
- [ ] Deploy risk API: `GET /risk/portfolio-var`

**Acceptance Criteria:**
- Daily VaR calculation <2 seconds
- Kelly sizing reduces volatility 30%+
- Stress tests complete in <10 seconds

#### **Week 4: Execution Optimization**
- [ ] Build TWAP/VWAP execution algorithms
- [ ] Implement maker vs taker logic
- [ ] Create cost estimation model
- [ ] Deploy execution API: `POST /execution/optimize`

**Acceptance Criteria:**
- 60%+ maker order ratio achieved
- 40%+ cost reduction vs baseline
- <1 second execution optimization

### **Phase 2: Strategy Implementation (Weeks 5-8)**

#### **Week 5: Statistical Arbitrage**
- [ ] Implement ETH/BTC pairs trading
- [ ] Build cointegration testing
- [ ] Create mean reversion signals
- [ ] Backtest on 2+ years data

**Acceptance Criteria:**
- Sharpe ratio >1.5 in backtests
- Max drawdown <5%
- Market correlation <0.2

#### **Week 6: Cross-Exchange Arbitrage**
- [ ] Build multi-exchange price monitoring
- [ ] Implement arbitrage opportunity detection
- [ ] Create execution coordination
- [ ] Test with paper trading

**Acceptance Criteria:**
- Detect 5+ opportunities per day
- Execute within 2 seconds of detection
- Profit factor >2.0

#### **Week 7: Volatility Strategies**
- [ ] Implement GARCH volatility forecasting
- [ ] Build volatility breakout detection
- [ ] Create direction-agnostic trades
- [ ] Backtest performance

**Acceptance Criteria:**
- Volatility prediction accuracy >65%
- Strategy profitable in all regimes
- Sharpe ratio >1.2

#### **Week 8: Integration & Deployment**
- [ ] Integrate all strategies with regime detection
- [ ] Implement dynamic allocation based on regime
- [ ] Create unified portfolio management
- [ ] Deploy to production with 10% capital

**Acceptance Criteria:**
- All strategies adapt to regime changes
- Portfolio Sharpe >1.5
- Max drawdown <10%

---

## 📏 **SUCCESS METRICS (INSTITUTIONAL BENCHMARKS)**

### **Performance Targets:**
```
Sharpe Ratio: >1.5 (institutional minimum)
Max Drawdown: <10% (risk management requirement)  
Win Rate: >60% (execution quality)
Profit Factor: >1.8 (strategy edge)
Market Correlation: <0.3 (market neutrality)
```

### **Operational Targets:**
```
System Uptime: >99.5%
Signal-to-Order Latency: <1 second
Cost Per Trade: <50 basis points
Risk Calculation: <5 seconds
Cache Hit Rate: >95%
```

### **Business Targets:**
```
Monthly Returns: 2-4% (24-48% annually)
Volatility: <15% annually
Information Ratio: >1.0
Maximum 2 consecutive losing months
Capital Efficiency: >80% deployed
```

---

## 🚨 **SCOPE PROTECTION RULES**

### **NO ADDITIONS Until Core Complete:**
- No new indicators until regime detection works
- No new strategies until stat arb profitable  
- No UI improvements until backend stable
- No "nice to have" features until targets met

### **Weekly Gate Reviews:**
Each week MUST pass acceptance criteria before proceeding
- Week 1: Regime detection working
- Week 2: Correlation engine reducing risk
- Week 3: Risk management preventing losses
- Week 4: Execution saving costs

### **Kill Criteria:**
Stop immediately if:
- Week behind schedule
- Acceptance criteria not met
- Performance below benchmarks
- Scope creep detected

---

## 💡 **IMPLEMENTATION PHILOSOPHY**

### **"Build Like Goldman Sachs":**
- **Measure everything** - if you can't measure it, don't build it
- **Risk first** - capital preservation before profit generation  
- **Incremental deployment** - start with 10% capital, scale based on performance
- **Institutional standards** - Sharpe >1.5 or don't deploy

### **"Research-Driven Development":**
- Every feature based on documented institutional practice
- No "experimental" features in production
- Backtest everything on 3+ years data
- Paper trade before live deployment

### **Technical Principles:**
- Test coverage >80% 
- API-first development
- Configuration over code
- Event-driven architecture
- Comprehensive observability

---

## 🎯 **FINAL SUCCESS CRITERIA**

**After 8 weeks, system MUST achieve:**
1. **Regime-aware trading** - strategies adapt to market conditions
2. **Correlation-adjusted sizing** - portfolio correlation to BTC <0.3  
3. **Cost-optimized execution** - 40%+ cost reduction vs baseline
4. **Institutional performance** - Sharpe >1.5, drawdown <10%
5. **Profitable in all regimes** - positive returns regardless of market direction

**If ANY criteria not met: STOP and fix before adding features.**

This framework implements exactly what we researched - no more, no less. Build this and you'll have an institutional-grade trading system that actually works.