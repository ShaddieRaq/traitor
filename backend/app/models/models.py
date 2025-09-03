from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
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
    max_positions = Column(Integer, default=1)  # Maximum concurrent positions
    
    # Risk management
    stop_loss_pct = Column(Float, default=5.0)  # Stop loss percentage
    take_profit_pct = Column(Float, default=10.0)  # Take profit percentage
    confirmation_minutes = Column(Integer, default=5)  # Signal confirmation time
    trade_step_pct = Column(Float, default=2.0)  # Minimum price change % between trades
    cooldown_minutes = Column(Integer, default=15)  # Time to wait between trades
    
    # Signal configuration (JSON string)
    signal_config = Column(Text)  # JSON: {"RSI": {"weight": 0.4, "period": 14, "oversold": 30, "overbought": 70}, ...}
    
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
    """Trade execution records."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))  # Which bot made this trade
    product_id = Column(String(20), index=True)
    side = Column(String(10))  # "buy" or "sell"
    size = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    order_id = Column(String(100), unique=True)  # Coinbase order ID
    status = Column(String(20))  # "pending", "filled", "cancelled"
    combined_signal_score = Column(Float)  # Combined signal score that triggered this trade
    signal_scores = Column(Text)  # JSON string of individual signal scores at trade time
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True))
    
    bot = relationship("Bot", back_populates="trades")


# Add back references
Bot.signal_history = relationship("BotSignalHistory", back_populates="bot")
Bot.trades = relationship("Trade", back_populates="bot")
