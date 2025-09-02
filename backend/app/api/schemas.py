from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Signal Configuration Schemas
class RSISignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.33, ge=0.0, le=1.0, description="Signal weight (0-1)")
    period: int = Field(default=14, ge=2, le=100, description="RSI calculation period")
    buy_threshold: float = Field(default=30, ge=0, le=100, description="Buy when RSI below this")
    sell_threshold: float = Field(default=70, ge=0, le=100, description="Sell when RSI above this")

    @validator('sell_threshold')
    def sell_must_be_greater_than_buy(cls, v, values):
        if 'buy_threshold' in values and v <= values['buy_threshold']:
            raise ValueError('sell_threshold must be greater than buy_threshold')
        return v


class MovingAverageSignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.33, ge=0.0, le=1.0, description="Signal weight (0-1)")
    fast_period: int = Field(default=10, ge=2, le=200, description="Fast MA period")
    slow_period: int = Field(default=20, ge=2, le=200, description="Slow MA period")
    
    @validator('slow_period')
    def slow_must_be_greater_than_fast(cls, v, values):
        if 'fast_period' in values and v <= values['fast_period']:
            raise ValueError('slow_period must be greater than fast_period')
        return v


class MACDSignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.34, ge=0.0, le=1.0, description="Signal weight (0-1)")
    fast_period: int = Field(default=12, ge=2, le=50, description="MACD fast period")
    slow_period: int = Field(default=26, ge=2, le=100, description="MACD slow period")
    signal_period: int = Field(default=9, ge=2, le=50, description="MACD signal period")
    
    @validator('slow_period')
    def slow_must_be_greater_than_fast(cls, v, values):
        if 'fast_period' in values and v <= values['fast_period']:
            raise ValueError('slow_period must be greater than fast_period')
        return v


class SignalConfigurationSchema(BaseModel):
    rsi: RSISignalConfig = RSISignalConfig()
    moving_average: MovingAverageSignalConfig = MovingAverageSignalConfig()
    macd: MACDSignalConfig = MACDSignalConfig()
    
    @validator('macd')
    def validate_total_weight(cls, v, values):
        """Ensure total weights don't exceed 1.0"""
        total_weight = 0.0
        
        # Add RSI weight if enabled
        if 'rsi' in values and values['rsi'].enabled:
            total_weight += values['rsi'].weight
            
        # Add MA weight if enabled  
        if 'moving_average' in values and values['moving_average'].enabled:
            total_weight += values['moving_average'].weight
            
        # Add MACD weight if enabled
        if v.enabled:
            total_weight += v.weight
            
        if total_weight > 1.0:
            raise ValueError(f'Total enabled signal weights ({total_weight:.2f}) cannot exceed 1.0')
        
        return v


class BotCreate(BaseModel):
    name: str
    description: str
    pair: str  # e.g., "BTC-USD"
    position_size_usd: float = 100.0
    max_positions: int = 1
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    confirmation_minutes: int = 5
    trade_step_pct: float = 2.0
    cooldown_minutes: int = 15
    signal_config: Optional[SignalConfigurationSchema] = SignalConfigurationSchema()

    @validator('signal_config', pre=True)
    def validate_signal_config(cls, v):
        """Convert dict to SignalConfigurationSchema if needed"""
        if isinstance(v, dict):
            return SignalConfigurationSchema(**v)
        return v


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # RUNNING, STOPPED, ERROR
    position_size_usd: Optional[float] = None
    max_positions: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    confirmation_minutes: Optional[int] = None
    trade_step_pct: Optional[float] = None
    cooldown_minutes: Optional[int] = None
    signal_config: Optional[SignalConfigurationSchema] = None

    @validator('signal_config', pre=True)
    def validate_signal_config(cls, v):
        """Convert dict to SignalConfigurationSchema if needed"""
        if isinstance(v, dict):
            return SignalConfigurationSchema(**v)
        return v


class BotResponse(BaseModel):
    id: int
    name: str
    description: str
    pair: str
    status: str
    position_size_usd: float
    max_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    confirmation_minutes: int
    trade_step_pct: float
    cooldown_minutes: int
    signal_config: Dict[str, Any]
    current_position_size: float
    current_position_entry_price: Optional[float]
    current_combined_score: float
    signal_confirmation_start: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BotStatusResponse(BaseModel):
    """Lightweight bot status for dashboard."""
    id: int
    name: str
    pair: str
    status: str
    current_combined_score: float
    current_position_size: float
    temperature: str  # HOT, WARM, COLD, FROZEN
    distance_to_signal: float  # How close to buy/sell threshold
    
    class Config:
        from_attributes = True


class MarketDataResponse(BaseModel):
    product_id: str
    timestamp: datetime
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    
    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: int
    bot_id: int
    product_id: str
    side: str
    size: float
    price: float
    fee: float
    order_id: str
    status: str
    combined_signal_score: float
    created_at: datetime
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BotSignalHistoryResponse(BaseModel):
    id: int
    bot_id: int
    timestamp: datetime
    combined_score: float
    signal_scores: Dict[str, Any]
    price: float
    
    class Config:
        from_attributes = True


class ProductTickerResponse(BaseModel):
    product_id: str
    price: float
    volume_24h: float


class AccountResponse(BaseModel):
    currency: str
    available_balance: float
    hold: float
