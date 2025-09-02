from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime


def create_signal_instance(signal_type: str, parameters: Dict[str, Any]) -> Optional['BaseSignal']:
    """
    Factory function to create signal instances.
    
    Args:
        signal_type: Type of signal to create ('RSI', 'MA_Crossover')
        parameters: Signal parameters
        
    Returns:
        Signal instance or None if type not found
    """
    from .technical import RSISignal, MovingAverageSignal
    
    signal_map = {
        'RSI': RSISignal,
        'MA_Crossover': MovingAverageSignal,
    }
    
    signal_class = signal_map.get(signal_type)
    if signal_class:
        return signal_class(**parameters)
    return None


class BaseSignal(ABC):
    """Base class for all trading signals."""
    
    def __init__(self, name: str, description: str, weight: float = 1.0, **parameters):
        self.name = name
        self.description = description
        self.weight = weight
        self.parameters = parameters
        self.enabled = True
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate signal based on market data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dict containing:
            - score: float (-1 to 1, negative = sell, positive = buy)
            - action: str ("buy", "sell", "hold")
            - confidence: float (0 to 1)
            - metadata: Dict with additional signal information
        """
        pass
    
    @abstractmethod
    def get_required_periods(self) -> int:
        """Return minimum number of data periods required for calculation."""
        pass
    
    def is_valid_data(self, data: pd.DataFrame) -> bool:
        """Check if data is sufficient for signal calculation."""
        return len(data) >= self.get_required_periods()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "enabled": self.enabled,
            "parameters": self.parameters
        }
