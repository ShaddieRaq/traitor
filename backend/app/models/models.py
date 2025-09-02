from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Signal(Base):
    """Signal configuration and metadata."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)  # Signal importance weight
    parameters = Column(Text)  # JSON string of signal parameters
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


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
    product_id = Column(String(20), index=True)
    side = Column(String(10))  # "buy" or "sell"
    size = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    order_id = Column(String(100), unique=True)  # Coinbase order ID
    status = Column(String(20))  # "pending", "filled", "cancelled"
    signal_scores = Column(Text)  # JSON string of signal scores at trade time
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True))


class SignalResult(Base):
    """Signal calculation results."""
    __tablename__ = "signal_results"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    product_id = Column(String(20), index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    score = Column(Float)  # Signal strength (-1 to 1, or 0 to 1)
    action = Column(String(10))  # "buy", "sell", "hold"
    confidence = Column(Float)  # 0.0 to 1.0
    signal_metadata = Column(Text)  # JSON string with additional signal data
    
    signal = relationship("Signal", back_populates="results")


# Add back reference
Signal.results = relationship("SignalResult", back_populates="signal")
