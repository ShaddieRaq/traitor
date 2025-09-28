from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# Signal Configuration Schemas
class RSISignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.33, ge=0.0, le=1.0, description="Signal weight (0-1)")
    period: int = Field(default=14, ge=2, le=100, description="RSI calculation period")
    buy_threshold: float = Field(default=30, ge=0, le=100, description="Buy when RSI below this")
    sell_threshold: float = Field(default=70, ge=0, le=100, description="Sell when RSI above this")

    @field_validator('sell_threshold')
    @classmethod
    def sell_must_be_greater_than_buy(cls, v, info):
        buy_threshold = info.data.get('buy_threshold')
        if buy_threshold is not None and v <= buy_threshold:
            raise ValueError('sell_threshold must be greater than buy_threshold')
        return v


class MovingAverageSignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.33, ge=0.0, le=1.0, description="Signal weight (0-1)")
    fast_period: int = Field(default=10, ge=2, le=200, description="Fast MA period")
    slow_period: int = Field(default=20, ge=2, le=200, description="Slow MA period")
    
    @field_validator('slow_period')
    @classmethod
    def slow_must_be_greater_than_fast(cls, v, info):
        fast_period = info.data.get('fast_period')
        if fast_period is not None and v <= fast_period:
            raise ValueError('slow_period must be greater than fast_period')
        return v


class MACDSignalConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(default=0.34, ge=0.0, le=1.0, description="Signal weight (0-1)")
    fast_period: int = Field(default=12, ge=2, le=50, description="MACD fast period")
    slow_period: int = Field(default=26, ge=2, le=100, description="MACD slow period")
    signal_period: int = Field(default=9, ge=2, le=50, description="MACD signal period")
    
    @field_validator('slow_period')
    @classmethod
    def slow_must_be_greater_than_fast(cls, v, info):
        fast_period = info.data.get('fast_period')
        if fast_period is not None and v <= fast_period:
            raise ValueError('slow_period must be greater than fast_period')
        return v


class SignalConfigurationSchema(BaseModel):
    rsi: Optional[RSISignalConfig] = None
    moving_average: Optional[MovingAverageSignalConfig] = None
    macd: Optional[MACDSignalConfig] = None
    
    @model_validator(mode='after')
    def validate_total_weight(self):
        """Ensure total weights don't exceed 1.0"""
        total_weight = 0.0
        
        # Add RSI weight if enabled
        if self.rsi and self.rsi.enabled:
            total_weight += self.rsi.weight
            
        # Add MA weight if enabled  
        if self.moving_average and self.moving_average.enabled:
            total_weight += self.moving_average.weight
            
        # Add MACD weight if enabled
        if self.macd and self.macd.enabled:
            total_weight += self.macd.weight
            
        if total_weight > 1.0:
            raise ValueError(f'Total enabled signal weights ({total_weight:.2f}) cannot exceed 1.0')
        
        return self


class BotCreate(BaseModel):
    name: str
    description: str
    pair: str  # e.g., "BTC-USD"
    position_size_usd: float = 100.0
    max_positions: int = 5
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    confirmation_minutes: int = 5
    trade_step_pct: float = 2.0
    cooldown_minutes: int = 15
    signal_config: Optional[SignalConfigurationSchema] = None

    @field_validator('signal_config', mode='before')
    @classmethod
    def validate_signal_config(cls, v):
        """Convert dict to SignalConfigurationSchema if needed"""
        if v is None:
            # Provide default balanced configuration
            return SignalConfigurationSchema(
                rsi=RSISignalConfig(enabled=True, weight=0.33),
                moving_average=MovingAverageSignalConfig(enabled=True, weight=0.33),
                macd=MACDSignalConfig(enabled=True, weight=0.34)
            )
        elif isinstance(v, dict):
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
    use_trend_detection: Optional[bool] = None  # Phase 1: Market Regime Intelligence
    use_position_sizing: Optional[bool] = None  # Phase 2: Position Sizing Intelligence

    @field_validator('signal_config', mode='before')
    @classmethod
    def validate_signal_config(cls, v):
        """Convert dict to SignalConfigurationSchema if needed"""
        if isinstance(v, dict):
            return SignalConfigurationSchema(**v)
        return v


class TradingThresholds(BaseModel):
    """Trading thresholds extracted from signal_config"""
    buy_threshold: float
    sell_threshold: float
    optimization_applied: Optional[bool] = None
    applied_date: Optional[str] = None


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
    trading_thresholds: Optional[TradingThresholds]  # Extracted thresholds for UI
    current_position_size: float
    current_position_entry_price: Optional[float]
    current_combined_score: float
    signal_confirmation_start: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    use_trend_detection: Optional[bool] = None  # Phase 1: Market Regime Intelligence
    use_position_sizing: Optional[bool] = None  # Phase 2: Position Sizing Intelligence
    
    model_config = ConfigDict(from_attributes=True)


class ConfirmationStatus(BaseModel):
    """Signal confirmation timer status."""
    is_active: bool
    action: Optional[str] = None  # "buy", "sell", or None
    progress: float = 0.0  # 0-1 completion percentage
    time_remaining_seconds: int = 0
    started_at: Optional[datetime] = None
    required_duration_minutes: int = 5


class TradingIntent(BaseModel):
    """Current trading intent and signal strength."""
    next_action: str  # "buy", "sell", "hold"
    signal_strength: float  # 0-1 how close to threshold
    confidence: float  # 0-1 signal reliability
    distance_to_threshold: float  # How much more signal needed


class TradeReadiness(BaseModel):
    """Current trade readiness status."""
    status: str  # "confirming", "ready", "cooling_down", "no_signal"
    can_trade: bool
    blocking_reason: Optional[str] = None  # "cooldown", "no_signal", "safety_limit"
    cooldown_remaining_minutes: int = 0


class LastTradeInfo(BaseModel):
    """Information about the last trade."""
    side: Optional[str] = None  # "BUY", "SELL"
    price: Optional[float] = None
    size: Optional[float] = None
    status: Optional[str] = None  # "filled", "pending"
    executed_at: Optional[datetime] = None
    minutes_ago: Optional[int] = None


class BalanceStatusResponse(BaseModel):
    """Balance validation status for trading."""
    valid: bool
    message: str


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
    balance_status: BalanceStatusResponse  # Balance validation info
    
    model_config = ConfigDict(from_attributes=True)


# Phase 1: Market Regime Intelligence - Trend Detection Schema
class TimeframeAnalysis(BaseModel):
    """Individual timeframe analysis data."""
    momentum: float
    data_points: int
    timeframe_name: str
    price_change_pct: float
    volatility: float
    
    model_config = ConfigDict(from_attributes=True)


class PositionSizingAnalysis(BaseModel):
    """Position sizing analysis data."""
    base_position_size: float
    final_position_size: float
    total_multiplier: float
    sizing_rationale: str
    regime_analysis: Optional[Dict[str, Any]] = None
    multiplier_breakdown: Optional[Dict[str, Any]] = None
    calculation_timestamp: Optional[str] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TrendAnalysisResponse(BaseModel):
    """Trend analysis data for regime-aware trading."""
    product_id: str = Field(description="Trading pair analyzed")
    trend_strength: float = Field(description="Trend strength (-1.0 to +1.0)")
    confidence: float = Field(description="Analysis confidence (0 to 1.0)")
    regime: str = Field(description="Market regime (STRONG_TRENDING, TRENDING, RANGING, CHOPPY)")
    moving_average_alignment: str = Field(description="MA alignment (BULLISH, BEARISH, NEUTRAL)")
    volume_confirmation: bool = Field(description="Whether volume confirms the trend")
    analysis_timestamp: str = Field(description="When analysis was performed")
    cache_ttl_seconds: int = Field(description="Cache TTL in seconds")
    timeframe_analysis: Dict[str, TimeframeAnalysis] = Field(description="Multi-timeframe analysis")
    
    model_config = ConfigDict(from_attributes=True)


class EnhancedBotStatusResponse(BaseModel):
    """Enhanced bot status with trading visibility."""
    id: int
    name: str
    pair: str
    status: str
    current_combined_score: float
    current_position_size: float
    position_size_usd: Optional[float] = None  # Alias for current_position_size for frontend compatibility
    temperature: str
    distance_to_signal: float
    
    # Enhanced trading visibility fields
    trading_intent: TradingIntent
    confirmation: ConfirmationStatus
    trade_readiness: TradeReadiness
    last_trade: Optional[LastTradeInfo] = None
    
    # Phase 1: Market Regime Intelligence - Trend Detection
    trend_analysis: Optional[TrendAnalysisResponse] = None
    use_trend_detection: bool = False
    
    # Phase 2: Position Sizing Intelligence - Dynamic Position Sizing
    position_sizing: Optional[PositionSizingAnalysis] = None
    use_position_sizing: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class MarketDataResponse(BaseModel):
    product_id: str
    timestamp: datetime
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    
    model_config = ConfigDict(from_attributes=True)


class TradeResponse(BaseModel):
    id: int
    bot_id: Optional[int] = None  # Optional to handle synced Coinbase trades
    product_id: str
    side: str
    size: float
    price: float
    fee: Optional[float] = None
    order_id: Optional[str] = None  # Optional to handle real Coinbase trades
    status: str
    combined_signal_score: Optional[float] = None
    created_at: datetime
    filled_at: Optional[datetime] = None
    
    # Enhanced fields for information feedback
    action: Optional[str] = None  # Computed from side (BUY/SELL)
    amount: Optional[float] = None  # Computed as size * price (USD value)
    
    model_config = ConfigDict(from_attributes=True)


class BotSignalHistoryResponse(BaseModel):
    id: int
    bot_id: int
    timestamp: datetime
    combined_score: float
    signal_scores: Dict[str, Any]
    price: float
    
    model_config = ConfigDict(from_attributes=True)


class ProductTickerResponse(BaseModel):
    product_id: str
    price: float
    volume_24h: float


class AccountResponse(BaseModel):
    currency: str
    available_balance: float
    hold: float


# Phase 4.1.1: Trading Safety Schemas

class TradeValidationRequest(BaseModel):
    bot_id: int = Field(description="Bot ID requesting trade")
    side: str = Field(description="Trade side: 'buy' or 'sell'")
    size_usd: float = Field(gt=0, description="Trade size in USD")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError("side must be 'buy' or 'sell'")
        return v


class SafetyCheckResult(BaseModel):
    position_size_valid: bool
    daily_trade_limit: bool
    daily_loss_limit: bool
    temperature_check: bool
    active_position_limit: bool
    consecutive_loss_check: bool
    emergency_circuit_breaker: bool


class TradeValidationResponse(BaseModel):
    allowed: bool
    reason: str
    safety_checks: SafetyCheckResult
    validated_at: datetime
    limits_applied: Dict[str, float]


class SafetyLimitsStatus(BaseModel):
    max_daily_loss_usd: float
    max_daily_trades: int
    max_position_size_usd: float
    min_position_size_usd: float
    max_active_positions: int
    min_temperature: str


class SafetyCurrentStatus(BaseModel):
    trades_today: int
    trades_remaining: int
    active_positions: int
    positions_available: int


class SafetyStatusResponse(BaseModel):
    limits: SafetyLimitsStatus
    current_status: SafetyCurrentStatus
    safety_enabled: bool
    last_updated: datetime


# Phase 4.1.2: Trade Execution Schemas

class TradeExecutionRequest(BaseModel):
    """Request schema for trade execution."""
    bot_id: int = Field(..., gt=0, description="ID of the bot executing the trade")
    side: str = Field(..., description="Trade side: 'buy' or 'sell'")
    size_usd: float = Field(..., gt=0, description="Trade size in USD")
    current_temperature: Optional[str] = Field(None, description="Current bot temperature (optional)")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")
        return v.lower()


class TradeExecutionResponse(BaseModel):
    """Response schema for successful trade execution."""
    success: bool
    trade_id: int
    order_id: str
    bot: Dict[str, Any]
    execution: Dict[str, Any]
    safety_validation: Dict[str, Any]
    order_details: Dict[str, Any]
    executed_at: str


class TradeExecutionError(BaseModel):
    """Response schema for failed trade execution."""
    success: bool = False
    error: str
    error_type: str
    bot_id: int
    request: Dict[str, Any]
    failed_at: str


class TradeStatusResponse(BaseModel):
    """Response schema for trade status queries."""
    trade_id: int
    bot_id: int
    order_id: str
    product_id: str
    side: str
    size: float
    price: float
    status: str
    created_at: Optional[str]
    filled_at: Optional[str]
    combined_signal_score: Optional[float]
