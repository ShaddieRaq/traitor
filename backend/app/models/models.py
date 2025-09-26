from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Bot(Base):
    """Trading bot configuration and state."""
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    pair = Column(String(20), index=True)  # e.g., "BTC-USD"
    status = Column(String(20), default="STOPPED")  # RUNNING, STOPPED, ERROR
    
    # Position sizing
    position_size_usd = Column(Float, default=100.0)  # Fixed dollar amount per trade
    max_positions = Column(Integer, default=5)  # Maximum concurrent positions
    
    # Risk management
    stop_loss_pct = Column(Float, default=5.0)  # Stop loss percentage
    take_profit_pct = Column(Float, default=10.0)  # Take profit percentage
    confirmation_minutes = Column(Integer, default=5)  # Signal confirmation time
    trade_step_pct = Column(Float, default=2.0)  # Minimum price change % between trades
    cooldown_minutes = Column(Integer, default=15)  # Time to wait between trades
    
    # Signal configuration (JSON string)
    signal_config = Column(Text)  # JSON: {"RSI": {"weight": 0.4, "period": 14, "oversold": 30, "overbought": 70}, ...}
    
    # Performance optimization settings
    skip_signals_on_low_balance = Column(Boolean, default=False)  # Skip signal processing when balance insufficient
    
    # Phase 1: Market Regime Intelligence - Trend Detection
    use_trend_detection = Column(Boolean, default=False)  # Enable/disable trend-based regime adaptation
    
    # Phase 2: Position Sizing Intelligence - Dynamic Position Sizing
    use_position_sizing = Column(Boolean, default=False)  # Enable/disable regime-adaptive position sizing
    
    # Current state
    current_position_size = Column(Float, default=0.0)
    current_position_entry_price = Column(Float)
    current_combined_score = Column(Float, default=0.0)
    signal_confirmation_start = Column(DateTime(timezone=True))  # When current signal confirmation started
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BotSignalHistory(Base):
    """Historical signal scores for confirmation tracking."""
    __tablename__ = "bot_signal_history"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    timestamp = Column(DateTime(timezone=True), index=True)
    combined_score = Column(Float)  # Weighted combined score of all signals
    action = Column(String(10))  # buy, sell, hold
    confidence = Column(Float)  # Overall confidence (0-1)
    signal_scores = Column(Text)  # JSON string of individual signal scores
    evaluation_metadata = Column(Text)  # JSON string of evaluation metadata
    price = Column(Float)  # Market price at evaluation time
    
    bot = relationship("Bot", back_populates="signal_history")


class MarketData(Base):
    """Candlestick market data."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(20), index=True)  # e.g., "BTC-USD"
    timestamp = Column(DateTime(timezone=True), index=True)
    timeframe = Column(String(10), index=True)  # e.g., "1h", "1d"
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)


class Trade(Base):
    """Trade execution records with enhanced position management."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))  # Which bot made this trade
    product_id = Column(String(20), index=True)
    side = Column(String(10))  # "buy" or "sell"
    size = Column(Float)
    price = Column(Float)
    fee = Column(Float)  # Legacy fee field (usually 0 from Coinbase)
    commission = Column(Float)  # Actual trading commission from Coinbase
    order_id = Column(String(100), unique=True)  # Coinbase order ID
    status = Column(String(20))  # "pending", "filled", "cancelled"
    combined_signal_score = Column(Float)  # Combined signal score that triggered this trade
    signal_scores = Column(Text)  # JSON string of individual signal scores at trade time
    
    # Phase 4.1.3: Enhanced Position Management
    position_tranches = Column(Text)  # JSON array of position tranches
    average_entry_price = Column(Numeric(precision=20, scale=8))  # Weighted average entry price
    tranche_number = Column(Integer, default=1)  # Sequential tranche tracking (1, 2, 3...)
    position_status = Column(String(20), default="CLOSED")  # CLOSED, BUILDING, OPEN, REDUCING
    size_usd = Column(Float)  # Trade size in USD
    size_in_quote = Column(Boolean, default=False)  # Coinbase flag: True if size is in USD, False if crypto units

    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True))
    
    bot = relationship("Bot", back_populates="trades")


class RawTrade(Base):
    """Raw trade data from Coinbase API - stored exactly as received."""
    __tablename__ = "raw_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Coinbase fill payload data (ACTUAL VALUES)
    fill_id = Column(String(100), unique=True, nullable=False, index=True)  # Coinbase fill ID
    order_id = Column(String(100), nullable=False, index=True)  # Coinbase order ID
    product_id = Column(String(20), nullable=False, index=True)  # e.g. "BTC-USD"
    side = Column(String(10), nullable=False)  # "BUY" or "SELL"
    
    # Actual numeric values from Coinbase
    size = Column(Float, nullable=False)  # Actual size number
    size_in_quote = Column(Boolean, nullable=False)  # Coinbase's boolean flag
    price = Column(Float, nullable=False)  # Actual price number
    
    # Actual fee value
    commission = Column(Float)  # Actual commission number
    
    # Timestamp
    created_at = Column(String(50), nullable=False)  # ISO timestamp from Coinbase
    
    # Metadata
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    """System notifications for market opportunities and alerts."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # 'market_opportunity', 'system_alert', 'trade_alert'
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")  # 'low', 'normal', 'high', 'critical'
    data = Column(Text)  # JSON data for additional context
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TradingPair(Base):
    """Track trading pairs and detect new listings."""
    __tablename__ = "trading_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "BTC-USD"
    base_currency_id = Column(String(10), nullable=False)  # e.g., "BTC"
    quote_currency_id = Column(String(10), nullable=False)  # e.g., "USD"
    base_name = Column(String(100))  # Full name like "Bitcoin"
    status = Column(String(20), default="online")  # online, offline, delisted
    trading_disabled = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    
    # Tracking fields
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_new_listing = Column(Boolean, default=True)  # Mark as new until processed
    
    # Market data snapshot at discovery
    initial_price = Column(Float)
    initial_volume_24h = Column(Float)
    
    def __repr__(self):
        return f"<TradingPair {self.product_id}>"


class SignalPredictionRecord(Base):
    """
    Phase 3A: Signal performance tracking - Individual signal predictions
    Store each signal prediction for later performance evaluation
    """
    __tablename__ = "signal_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Signal context
    pair = Column(String(20), index=True)
    regime = Column(String(20), index=True)  # TRENDING, RANGING, CHOPPY, etc.
    signal_type = Column(String(50), index=True)  # RSI, MA_Crossover, MACD
    
    # Prediction details
    signal_score = Column(Float)
    prediction = Column(String(10))  # buy, sell, hold
    confidence = Column(Float)
    
    # Outcome evaluation (filled later)
    actual_price_change_pct = Column(Float)  # Actual price change over evaluation period
    outcome = Column(String(20))  # true_positive, false_positive, true_negative, false_negative
    evaluation_timestamp = Column(DateTime(timezone=True))
    
    # Trade execution details (if applicable)
    trade_executed = Column(Boolean, default=False)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    trade_pnl_usd = Column(Float)  # P&L if trade was executed
    
    # Metadata
    evaluation_period_minutes = Column(Integer, default=60)  # How long after to evaluate outcome
    
    def __repr__(self):
        return f"<SignalPrediction {self.signal_type} {self.pair} {self.prediction}>"


class SignalPerformanceMetrics(Base):
    """
    Phase 3A: Aggregated signal performance metrics by pair, regime, and signal type
    Calculated periodically from SignalPredictionRecord data
    """
    __tablename__ = "signal_performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Performance context
    pair = Column(String(20), index=True)
    regime = Column(String(20), index=True)
    signal_type = Column(String(50), index=True)
    
    # Performance metrics
    total_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)  # % correct predictions
    precision = Column(Float, default=0.0)  # % positive predictions that were correct
    recall = Column(Float, default=0.0)  # % opportunities that were caught
    avg_confidence = Column(Float, default=0.0)
    avg_pnl_usd = Column(Float, default=0.0)  # Average P&L when trades executed
    
    # Time ranges
    calculation_period_days = Column(Integer, default=30)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Metadata
    min_samples_required = Column(Integer, default=20)
    is_reliable = Column(Boolean, default=False)  # True if enough samples for reliability
    
    def __repr__(self):
        return f"<SignalPerformanceMetrics {self.signal_type} {self.pair} {self.regime} {self.accuracy:.2f}>"


class AdaptiveSignalWeights(Base):
    """
    Phase 3B: Store adaptive signal weights calculated from performance metrics
    Used by bots to dynamically adjust signal importance
    """
    __tablename__ = "adaptive_signal_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), index=True)
    
    # Context
    pair = Column(String(20), index=True)
    regime = Column(String(20), index=True)
    
    # Adaptive weights (JSON format for flexibility)
    signal_weights = Column(JSON)  # {"RSI": 0.35, "MA_Crossover": 0.40, "MACD": 0.25}
    default_weights = Column(JSON)  # Original weights for comparison
    
    # Performance basis
    weight_calculation_method = Column(String(50), default="performance_weighted")
    performance_period_days = Column(Integer, default=30)
    confidence_score = Column(Float, default=0.0)  # How confident we are in these weights
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Relationships
    bot = relationship("Bot", back_populates="adaptive_weights")
    
    def __repr__(self):
        return f"<AdaptiveSignalWeights Bot{self.bot_id} {self.regime}>"


# Add back references
Bot.signal_history = relationship("BotSignalHistory", back_populates="bot")
Bot.trades = relationship("Trade", back_populates="bot")
Bot.adaptive_weights = relationship("AdaptiveSignalWeights", back_populates="bot")
