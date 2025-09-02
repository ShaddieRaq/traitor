from typing import Dict, Any
import pandas as pd
import numpy as np
from .base import BaseSignal


class RSISignal(BaseSignal):
    """Relative Strength Index signal."""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs):
        super().__init__(
            name="RSI",
            description="Relative Strength Index momentum oscillator",
            period=period,
            oversold=oversold,
            overbought=overbought,
            **kwargs
        )
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate RSI signal using pure pandas/numpy."""
        if not self.is_valid_data(data):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {}}
        
        # Calculate RSI using pandas
        period = self.parameters["period"]
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        
        # Calculate price changes
        delta = data['close'].diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Calculate RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        # Handle NaN values
        if pd.isna(current_rsi):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {"error": "RSI calculation failed"}}
        
        # Generate signal
        if current_rsi <= oversold:
            score = (oversold - current_rsi) / oversold  # 0 to 1
            action = "buy"
            confidence = min(score, 1.0)
        elif current_rsi >= overbought:
            score = -(current_rsi - overbought) / (100 - overbought)  # -1 to 0
            action = "sell"
            confidence = min(abs(score), 1.0)
        else:
            score = 0
            action = "hold"
            confidence = 0.1
        
        return {
            "score": score,
            "action": action,
            "confidence": confidence,
            "metadata": {
                "rsi_value": current_rsi,
                "period": period,
                "oversold_threshold": oversold,
                "overbought_threshold": overbought
            }
        }
    
    def get_required_periods(self) -> int:
        return self.parameters["period"] + 1


class MovingAverageSignal(BaseSignal):
    """Simple Moving Average crossover signal."""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 20, **kwargs):
        super().__init__(
            name="MA_Crossover",
            description="Moving Average crossover signal",
            fast_period=fast_period,
            slow_period=slow_period,
            **kwargs
        )
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MA crossover signal."""
        if not self.is_valid_data(data):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {}}
        
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        
        fast_ma = data['close'].rolling(window=fast_period).mean()
        slow_ma = data['close'].rolling(window=slow_period).mean()
        
        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]
        
        # Check for crossover
        bullish_crossover = (prev_fast <= prev_slow) and (current_fast > current_slow)
        bearish_crossover = (prev_fast >= prev_slow) and (current_fast < current_slow)
        
        if bullish_crossover:
            score = 0.8
            action = "buy"
            confidence = 0.8
        elif bearish_crossover:
            score = -0.8
            action = "sell"
            confidence = 0.8
        else:
            # Signal strength based on MA separation
            separation = (current_fast - current_slow) / current_slow
            score = np.tanh(separation * 10)  # Normalize to -1 to 1
            action = "buy" if score > 0.1 else "sell" if score < -0.1 else "hold"
            confidence = abs(score) * 0.5
        
        return {
            "score": score,
            "action": action,
            "confidence": confidence,
            "metadata": {
                "fast_ma": current_fast,
                "slow_ma": current_slow,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "separation_pct": (current_fast - current_slow) / current_slow * 100
            }
        }
    
    def get_required_periods(self) -> int:
        return max(self.parameters["fast_period"], self.parameters["slow_period"]) + 1
