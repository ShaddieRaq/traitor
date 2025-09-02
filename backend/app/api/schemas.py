from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SignalCreate(BaseModel):
    name: str
    description: str
    weight: float = 1.0
    parameters: Dict[str, Any] = {}


class SignalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    weight: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None


class SignalResponse(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    weight: float
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    
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
    product_id: str
    side: str
    size: float
    price: float
    fee: float
    order_id: str
    status: str
    created_at: datetime
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SignalResultResponse(BaseModel):
    id: int
    signal_id: int
    product_id: str
    timestamp: datetime
    score: float
    action: str
    confidence: float
    metadata: Dict[str, Any]
    
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
