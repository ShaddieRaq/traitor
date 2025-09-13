# 🔄 System Redesign Plan - September 11, 2025

**Issue**: Fundamental architectural flaws in trade management and bot-trade coupling  
**Goal**: Clean separation of concerns with portfolio-centric design  
**Status**: Complete redesign required to eliminate conceptual contradictions

## 🎯 **Core Design Principles**

### **1. Portfolio-Centric Architecture**
- **Trades are portfolio transactions** - no artificial bot ownership
- **Bots are decision engines** - they generate signals and trigger actions
- **P&L is calculated on overall portfolio** - not segmented by bot
- **Position management is unified** - one position per trading pair, regardless of which bot triggered trades

### **2. Clean Separation of Concerns**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SIGNALS   │ -> │   TRADES    │ -> │  PORTFOLIO  │
│             │    │             │    │             │
│ Bot 1: RSI  │    │ BUY $100    │    │ BTC: +0.5   │
│ Bot 2: MACD │    │ SELL $50    │    │ Cash: $450  │
│ Bot 3: MA   │    │ BUY $25     │    │ P&L: +$25   │
└─────────────┘    └─────────────┘    └─────────────┘
    Decision           Action            Result
```

### **3. Elimination of Bot-Trade Coupling**
- **Remove `bot_id` from Trade model** - trades don't "belong" to bots
- **Add `triggered_by` metadata** - optional attribution for debugging only
- **Focus on trade execution quality** - not which bot made the decision

## 📊 **New Database Schema**

### **Redesigned Trade Model**
```python
class Trade(Base):
    """Portfolio transaction record - bot-agnostic"""
    __tablename__ = "trades"
    
    # Core trade data
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(20), index=True, nullable=False)  # e.g., "BTC-USD"
    side = Column(String(4), nullable=False)  # "BUY" or "SELL" (consistent casing)
    size_usd = Column(Numeric(precision=20, scale=8), nullable=False)  # Always in USD
    size_crypto = Column(Numeric(precision=20, scale=8), nullable=False)  # Crypto amount
    price = Column(Numeric(precision=20, scale=8), nullable=False)  # Execution price
    
    # Exchange integration
    order_id = Column(String(100), unique=True, nullable=False)  # Coinbase order ID
    status = Column(String(20), nullable=False)  # "pending", "filled", "cancelled"
    commission = Column(Numeric(precision=20, scale=8), default=0)  # Trading fees
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional metadata (for debugging/analytics only)
    triggered_by = Column(String(100), nullable=True)  # "bot:1", "manual", "sync", etc.
    signal_context = Column(JSON, nullable=True)  # Signal data when trade was triggered
```

### **Simplified Bot Model**
```python
class Bot(Base):
    """Signal generation and decision engine"""
    __tablename__ = "bots"
    
    # Identity
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    product_id = Column(String(20), index=True, nullable=False)  # e.g., "BTC-USD"
    status = Column(String(20), default="STOPPED")  # RUNNING, STOPPED, ERROR
    
    # Signal configuration
    signal_config = Column(JSON, nullable=False)  # Signal weights and parameters
    
    # Decision parameters
    confirmation_minutes = Column(Integer, default=5)
    cooldown_minutes = Column(Integer, default=15)
    trade_size_usd = Column(Numeric(precision=20, scale=8), default=10.0)
    
    # Current evaluation state (computed, not stored long-term)
    last_evaluation_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### **New Portfolio Model**
```python
class Portfolio(Base):
    """Current portfolio state - computed from trade history"""
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(20), unique=True, index=True)  # e.g., "BTC-USD"
    
    # Position data
    crypto_balance = Column(Numeric(precision=20, scale=8), default=0)  # Total crypto held
    usd_invested = Column(Numeric(precision=20, scale=8), default=0)    # Total USD invested
    average_cost_basis = Column(Numeric(precision=20, scale=8), nullable=True)  # Weighted avg price
    
    # Performance
    unrealized_pnl = Column(Numeric(precision=20, scale=8), default=0)
    realized_pnl = Column(Numeric(precision=20, scale=8), default=0)
    
    # Metadata
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 🔄 **New Service Architecture**

### **1. Portfolio Service** (New)
```python
class PortfolioService:
    """Manages overall portfolio state and P&L calculations"""
    
    def calculate_position(self, product_id: str) -> Dict:
        """Calculate current position from trade history"""
        trades = self.get_all_trades(product_id)
        
        crypto_balance = 0
        usd_invested = 0
        total_cost = 0
        
        for trade in trades:
            if trade.side == "BUY":
                crypto_balance += trade.size_crypto
                usd_invested += trade.size_usd
                total_cost += trade.size_usd
            else:  # SELL
                # Calculate realized P&L on FIFO basis
                crypto_balance -= trade.size_crypto
                usd_invested -= (trade.size_crypto * avg_cost_basis)
                
        return {
            "crypto_balance": crypto_balance,
            "usd_invested": usd_invested,
            "average_cost_basis": total_cost / crypto_balance if crypto_balance > 0 else 0,
            "current_value": crypto_balance * current_price,
            "unrealized_pnl": (crypto_balance * current_price) - usd_invested
        }
    
    def get_total_pnl(self) -> Dict:
        """Calculate total portfolio P&L across all positions"""
        pass
```

### **2. Trade Service** (Simplified)
```python
class TradeService:
    """Handles trade execution - bot-agnostic"""
    
    def execute_trade(self, product_id: str, side: str, size_usd: float, 
                     triggered_by: str = None) -> Dict:
        """Execute a trade without bot coupling"""
        
        # Size validation
        if size_usd < 10.0:
            raise ValueError("Minimum trade size is $10 USD")
            
        # Balance check
        if not self._validate_balance(product_id, side, size_usd):
            raise ValueError("Insufficient balance")
            
        # Execute with Coinbase
        order_response = self.coinbase_service.place_order(
            product_id=product_id,
            side=side,
            size_usd=size_usd
        )
        
        # Record trade (no bot_id!)
        trade = Trade(
            product_id=product_id,
            side=side.upper(),
            size_usd=size_usd,
            size_crypto=order_response['size_crypto'],
            price=order_response['price'],
            order_id=order_response['order_id'],
            status="pending",
            triggered_by=triggered_by  # Optional attribution
        )
        
        # Update portfolio
        self.portfolio_service.refresh_position(product_id)
        
        return trade
```

### **3. Signal Service** (Renamed from BotEvaluator)
```python
class SignalService:
    """Generates trading signals - separated from execution"""
    
    def evaluate_bot_signals(self, bot: Bot) -> Dict:
        """Evaluate signals for a bot"""
        market_data = self.get_market_data(bot.product_id)
        config = bot.signal_config
        
        # Calculate individual signals
        signals = {
            'rsi': self._calculate_rsi(market_data, config.get('RSI', {})),
            'macd': self._calculate_macd(market_data, config.get('MACD', {})),
            'ma': self._calculate_ma(market_data, config.get('MA', {}))
        }
        
        # Weighted combination
        combined_score = sum(
            signal['score'] * signal.get('weight', 0) 
            for signal in signals.values() 
            if signal.get('enabled', False)
        )
        
        return {
            'bot_id': bot.id,
            'combined_score': combined_score,
            'individual_signals': signals,
            'temperature': self._score_to_temperature(combined_score),
            'recommended_action': self._score_to_action(combined_score)
        }
    
    def should_execute_trade(self, bot: Bot, signal_result: Dict) -> bool:
        """Determine if signal is strong enough to trigger trade"""
        # Check confirmation period, cooldown, etc.
        pass
```

## 🎯 **New API Architecture**

### **Portfolio-Centric Endpoints**
```python
# Portfolio overview
GET /api/v1/portfolio/
{
    "total_usd_balance": 1250.00,
    "positions": [
        {
            "product_id": "BTC-USD",
            "crypto_balance": 0.025,
            "usd_invested": 1000.00,
            "current_value": 1100.00,
            "unrealized_pnl": 100.00,
            "pnl_pct": 10.0
        }
    ],
    "total_pnl": 100.00
}

# All trades (no bot segmentation)
GET /api/v1/trades/
[
    {
        "id": 1,
        "product_id": "BTC-USD",
        "side": "BUY",
        "size_usd": 100.00,
        "size_crypto": 0.0025,
        "price": 40000.00,
        "status": "filled",
        "filled_at": "2025-09-11T10:30:00Z",
        "triggered_by": "bot:1"  // Optional
    }
]

# Bot signals (no trade data)
GET /api/v1/bots/signals/
[
    {
        "bot_id": 1,
        "product_id": "BTC-USD",
        "temperature": "HOT",
        "combined_score": 0.85,
        "recommended_action": "BUY",
        "last_evaluation": "2025-09-11T10:35:00Z",
        "ready_to_trade": true
    }
]

# Manual trade execution
POST /api/v1/trades/execute
{
    "product_id": "BTC-USD",
    "side": "BUY",
    "size_usd": 50.00
}
```

### **Bot Management Endpoints**
```python
# Bot configuration (no trade history)
GET /api/v1/bots/{id}/
{
    "id": 1,
    "name": "BTC Momentum Bot",
    "product_id": "BTC-USD",
    "status": "RUNNING",
    "signal_config": {...},
    "trade_size_usd": 10.00,
    "last_evaluation": "2025-09-11T10:35:00Z"
}

# Trigger bot evaluation (may result in trade)
POST /api/v1/bots/{id}/evaluate
{
    "forced": true,
    "result": {
        "temperature": "HOT",
        "trade_executed": true,
        "trade_id": 123
    }
}
```

## 🔧 **Migration Strategy**

### **Phase 1: Data Migration**
1. **Backup existing database** - critical before any changes
2. **Create new schema** alongside existing tables
3. **Migrate trade data** - copy to new Trade model without bot_id
4. **Calculate initial portfolio state** from migrated trades
5. **Validate data integrity** - ensure P&L matches

### **Phase 2: Service Refactoring**
1. **Implement PortfolioService** - new portfolio calculations
2. **Refactor TradeService** - remove bot coupling
3. **Update SignalService** - separate signal generation from execution
4. **Create new API endpoints** - portfolio-centric design

### **Phase 3: Frontend Updates**
1. **Portfolio dashboard** - unified P&L view
2. **Trade history** - no bot segmentation
3. **Bot status panel** - signals only, no trade data
4. **Manual trading interface** - direct trade execution

### **Phase 4: Cleanup**
1. **Remove old schema** - drop bot_id foreign keys
2. **Remove redundant endpoints** - consolidate trade APIs
3. **Update documentation** - reflect new architecture

## 📊 **Expected Benefits**

### **User Experience**
- **Clear portfolio view** - unified P&L across all trading activity
- **Simplified trade history** - no artificial bot segmentation
- **Faster decision making** - focus on signals, not bot management
- **Reduced confusion** - trades are just trades

### **Technical Benefits**
- **Simplified P&L calculations** - single source of truth
- **Easier debugging** - clear data flow without bot coupling
- **Better scalability** - portfolio-centric design supports multiple strategies
- **Cleaner codebase** - elimination of artificial abstractions

### **Development Velocity**
- **Fewer API endpoints** - consolidated portfolio management
- **Simpler testing** - portfolio state is deterministic
- **Clearer architecture** - separation of concerns
- **Easier feature additions** - new signals don't require trade model changes

## ⚠️ **Implementation Notes**

### **Critical Success Factors**
1. **Zero data loss** - all existing trades must be preserved
2. **Accurate P&L migration** - calculations must match before/after
3. **Minimal downtime** - migration should be reversible
4. **User communication** - clear explanation of changes

### **Risk Mitigation**
1. **Comprehensive testing** - automated migration validation
2. **Rollback plan** - ability to revert to old schema
3. **Staged deployment** - gradual rollout of new features
4. **Data validation** - extensive cross-checking during migration

---

**Redesign Summary**: Transform from bot-centric to portfolio-centric architecture, eliminating artificial trade ownership and focusing on unified position management. This addresses the fundamental conceptual flaw while preserving all trading functionality and improving user experience.

**Next Steps**: Review this plan, then begin with Phase 1 (data migration) in a safe, reversible manner.
