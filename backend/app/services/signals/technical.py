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
        
        # Generate signal with proper -1 to +1 scoring
        # Option B: Soft Neutral approach with gradual scaling
        
        if current_rsi <= oversold:
            # Strong buy signal: RSI 0-30 maps to scores -0.5 to -1.0
            score = -0.5 - (oversold - current_rsi) / oversold * 0.5
            action = "buy"
            confidence = abs(score)
        elif current_rsi >= overbought:
            # Strong sell signal: RSI 70-100 maps to scores 0.5 to 1.0
            score = 0.5 + (current_rsi - overbought) / (100 - overbought) * 0.5
            action = "sell"
            confidence = abs(score)
        else:
            # Neutral zone: RSI 30-70 maps to scores -0.5 to +0.5 (soft neutral)
            neutral_range = overbought - oversold
            neutral_position = (current_rsi - oversold) / neutral_range
            score = (neutral_position - 0.5) * 1.0  # Scale to -0.5 to +0.5
            
            if score > 0.2:
                action = "sell"  # Fixed: positive score = sell signal
            elif score < -0.2:
                action = "buy"   # Fixed: negative score = buy signal
            else:
                action = "hold"
            confidence = abs(score) * 0.5  # Lower confidence in neutral zone
        
        # Ensure score is within bounds
        score = max(-1.0, min(1.0, score))
        
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
        
        # Handle NaN values
        if pd.isna(current_fast) or pd.isna(current_slow) or pd.isna(prev_fast) or pd.isna(prev_slow):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {"error": "MA calculation failed"}}
        
        # Calculate percentage separation for scoring
        separation_pct = (current_fast - current_slow) / current_slow * 100
        
        # Check for crossover events (strong signals)
        bullish_crossover = (prev_fast <= prev_slow) and (current_fast > current_slow)
        bearish_crossover = (prev_fast >= prev_slow) and (current_fast < current_slow)
        
        if bullish_crossover:
            # Strong buy signal on bullish crossover
            score = -0.8  # Negative score indicates buy signal
            action = "buy"
            confidence = 0.9
        elif bearish_crossover:
            # Strong sell signal on bearish crossover
            score = 0.8  # Positive score indicates sell signal
            action = "sell" 
            confidence = 0.9
        else:
            # Score based on MA separation (distance-based scoring)
            # Larger separation = stronger signal
            # Use tanh to compress to -1 to +1 range with smooth scaling
            raw_score = np.tanh(separation_pct * 0.1)  # 0.1 is sensitivity factor
            
            # Invert score: negative separation (fast < slow) = buy signal (negative score)
            score = -raw_score
            
            # Determine action based on score magnitude and direction
            if score <= -0.2:
                action = "buy"
                confidence = min(abs(score), 0.7)
            elif score >= 0.2:
                action = "sell"
                confidence = min(abs(score), 0.7)
            else:
                action = "hold"
                confidence = abs(score) * 0.3  # Lower confidence near neutral
        
        # Ensure score is within bounds
        score = max(-1.0, min(1.0, score))
        
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


class MACDSignal(BaseSignal):
    """MACD (Moving Average Convergence Divergence) signal."""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs):
        super().__init__(
            name="MACD",
            description="Moving Average Convergence Divergence signal",
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            **kwargs
        )
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MACD signal."""
        if not self.is_valid_data(data):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {}}
        
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        signal_period = self.parameters["signal_period"]
        
        # Calculate exponential moving averages
        ema_fast = data['close'].ewm(span=fast_period).mean()
        ema_slow = data['close'].ewm(span=slow_period).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD line)
        signal_line = macd_line.ewm(span=signal_period).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
        
        # Handle NaN values
        if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(current_histogram):
            return {"score": 0, "action": "hold", "confidence": 0, "metadata": {"error": "MACD calculation failed"}}
        
        # Scoring based on multiple MACD signals
        score = 0
        confidence_factors = []
        
        # 1. MACD line vs Signal line (primary signal)
        macd_above_signal = current_macd > current_signal
        macd_separation = abs(current_macd - current_signal)
        
        if macd_above_signal:
            score -= 0.4  # Bullish (buy signal gets negative score)
            confidence_factors.append(min(macd_separation * 100, 0.3))
        else:
            score += 0.4  # Bearish (sell signal gets positive score)
            confidence_factors.append(min(macd_separation * 100, 0.3))
        
        # 2. Zero line crossover
        if current_macd > 0:
            score -= 0.3  # Above zero = bullish
        else:
            score += 0.3  # Below zero = bearish
        
        # 3. Histogram momentum (rate of change)
        histogram_momentum = current_histogram - prev_histogram
        normalized_momentum = np.tanh(histogram_momentum * 1000)  # Scale and normalize
        score -= normalized_momentum * 0.3  # Negative momentum = buy signal
        
        # Ensure score is within bounds
        score = max(-1.0, min(1.0, score))
        
        # Calculate overall confidence
        base_confidence = np.mean(confidence_factors) if confidence_factors else 0.1
        momentum_confidence = min(abs(histogram_momentum) * 1000, 0.3)
        confidence = min(base_confidence + momentum_confidence, 0.8)
        
        # Determine action
        if score <= -0.2:
            action = "buy"
        elif score >= 0.2:
            action = "sell"
        else:
            action = "hold"
            confidence *= 0.5  # Lower confidence in neutral zone
        
        return {
            "score": score,
            "action": action,
            "confidence": confidence,
            "metadata": {
                "macd_line": current_macd,
                "signal_line": current_signal,
                "histogram": current_histogram,
                "histogram_momentum": histogram_momentum,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period
            }
        }
    
    def get_required_periods(self) -> int:
        return self.parameters["slow_period"] + self.parameters["signal_period"] + 5  # Buffer for EMA calculations
