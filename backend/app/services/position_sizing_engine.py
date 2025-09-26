"""
Position Sizing Intelligence Engine - Phase 2B Implementation
Adaptive Position Sizing based on Market Regime Intelligence

Calculates dynamic position sizes using:
- Market regime (TRENDING vs RANGING vs CHOPPY)
- Volatility analysis
- Signal confidence levels
- Risk management constraints
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from .trend_detection_engine import get_trend_engine

logger = logging.getLogger(__name__)


class PositionSizingEngine:
    """
    Intelligent position sizing based on market regime and risk factors.
    
    Core Formula:
    Final Size = Base Size × Regime Multiplier × Volatility Adjustment × Confidence Factor
    
    With risk controls:
    - Max multiplier: 2.0x base size
    - Min multiplier: 0.3x base size
    """
    
    def __init__(self):
        """Initialize the position sizing engine."""
        self.max_position_multiplier = 2.0  # Maximum 2x base position
        self.min_position_multiplier = 0.3  # Minimum 30% base position
        
        # Regime-based multipliers
        self.regime_multipliers = {
            'STRONG_TRENDING': 1.5,  # High confidence in direction
            'TRENDING': 1.2,         # Good confidence
            'RANGING': 0.8,          # Lower confidence, choppy
            'CHOPPY': 0.5,           # Very uncertain, minimal exposure
            'UNKNOWN': 1.0           # Fallback to normal sizing
        }
        
        logger.info("Position Sizing Engine initialized with regime-adaptive multipliers")
    
    def calculate_position_size(
        self, 
        base_position_size: float,
        product_id: str,
        signal_confidence: Optional[float] = None,
        override_regime: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate dynamic position size based on market regime intelligence.
        
        Args:
            base_position_size: Base position size in USD
            product_id: Trading pair (e.g., "BTC-USD")
            signal_confidence: Optional signal confidence (0-1)
            override_regime: Optional regime data to avoid API call
            
        Returns:
            Dictionary containing position sizing analysis and final size
        """
        try:
            # Get regime analysis
            if override_regime:
                regime_data = override_regime
                logger.info(f"Using provided regime data for {product_id}")
            else:
                trend_engine = get_trend_engine()
                regime_data = trend_engine.analyze_trend(product_id)
                logger.info(f"Retrieved regime data for {product_id}: {regime_data['regime']}")
            
            # Extract key metrics
            regime = regime_data.get('regime', 'UNKNOWN')
            trend_strength = abs(regime_data.get('trend_strength', 0.0))
            confidence = regime_data.get('confidence', 0.7)
            
            # Get volatility from timeframe analysis
            volatility = self._calculate_volatility(regime_data)
            
            # Calculate multipliers
            regime_multiplier = self.regime_multipliers.get(regime, 1.0)
            volatility_multiplier = self._get_volatility_multiplier(volatility)
            confidence_multiplier = self._get_confidence_multiplier(
                signal_confidence if signal_confidence is not None else confidence
            )
            
            # Calculate raw position size
            raw_multiplier = regime_multiplier * volatility_multiplier * confidence_multiplier
            
            # Apply risk controls
            final_multiplier = max(
                self.min_position_multiplier,
                min(self.max_position_multiplier, raw_multiplier)
            )
            
            final_position_size = base_position_size * final_multiplier
            
            # Prepare analysis results
            analysis = {
                'base_position_size': base_position_size,
                'final_position_size': round(final_position_size, 2),
                'total_multiplier': round(final_multiplier, 3),
                'regime_analysis': {
                    'regime': regime,
                    'trend_strength': round(trend_strength, 4),
                    'confidence': round(confidence, 3),
                    'volatility': round(volatility, 4)
                },
                'multiplier_breakdown': {
                    'regime_multiplier': regime_multiplier,
                    'volatility_multiplier': round(volatility_multiplier, 3),
                    'confidence_multiplier': round(confidence_multiplier, 3),
                    'raw_multiplier': round(raw_multiplier, 3),
                    'applied_risk_controls': final_multiplier != raw_multiplier
                },
                'sizing_rationale': self._generate_rationale(
                    regime, volatility, confidence, final_multiplier, base_position_size
                ),
                'calculation_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"💰 Position sizing for {product_id}: {regime} regime → "
                f"${base_position_size:.2f} × {final_multiplier:.2f} = ${final_position_size:.2f}"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Position sizing calculation failed for {product_id}: {e}")
            # Fallback to base position size
            return {
                'base_position_size': base_position_size,
                'final_position_size': base_position_size,
                'total_multiplier': 1.0,
                'error': str(e),
                'sizing_rationale': f"Error in calculation, using base size: {e}",
                'calculation_timestamp': datetime.utcnow().isoformat()
            }
    
    def _calculate_volatility(self, regime_data: Dict[str, Any]) -> float:
        """Calculate average volatility across timeframes."""
        try:
            timeframe_analysis = regime_data.get('timeframe_analysis', {})
            volatilities = []
            
            for timeframe, data in timeframe_analysis.items():
                vol = data.get('volatility', 0.0)
                if vol > 0:
                    volatilities.append(vol)
            
            if volatilities:
                # Weighted average (give more weight to medium-term)
                if len(volatilities) >= 3:
                    # short, medium, long term
                    return (volatilities[0] * 0.3 + volatilities[1] * 0.5 + volatilities[2] * 0.2)
                else:
                    return sum(volatilities) / len(volatilities)
            else:
                return 1.0  # Default volatility assumption
                
        except Exception as e:
            logger.warning(f"Volatility calculation error: {e}")
            return 1.0
    
    def _get_volatility_multiplier(self, volatility: float) -> float:
        """Calculate position size multiplier based on volatility."""
        if volatility < 0.01:  # Very low volatility (<1%)
            return 1.2  # Size up - safe to take larger positions
        elif volatility < 0.03:  # Medium volatility (1-3%)
            return 1.0  # Normal sizing
        elif volatility < 0.05:  # High volatility (3-5%)
            return 0.8  # Size down
        else:  # Very high volatility (>5%)
            return 0.6  # Significant size reduction for risk management
    
    def _get_confidence_multiplier(self, confidence: float) -> float:
        """Calculate position size multiplier based on signal/regime confidence."""
        if confidence >= 0.8:    # High confidence
            return 1.1
        elif confidence >= 0.6:  # Medium confidence
            return 1.0
        elif confidence >= 0.4:  # Low confidence
            return 0.8
        else:                    # Very low confidence
            return 0.6
    
    def _generate_rationale(
        self, 
        regime: str, 
        volatility: float, 
        confidence: float, 
        final_multiplier: float,
        base_size: float
    ) -> str:
        """Generate human-readable rationale for position sizing decision."""
        vol_desc = "low" if volatility < 0.01 else "medium" if volatility < 0.03 else "high"
        conf_desc = "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low"
        
        size_change = ""
        if final_multiplier > 1.1:
            size_change = f"Increased position to ${base_size * final_multiplier:.2f} "
        elif final_multiplier < 0.9:
            size_change = f"Reduced position to ${base_size * final_multiplier:.2f} "
        else:
            size_change = f"Standard position of ${base_size * final_multiplier:.2f} "
        
        return (
            f"{size_change}due to {regime.lower()} market regime with {conf_desc} confidence "
            f"({confidence:.1%}) and {vol_desc} volatility ({volatility:.1%})"
        )


# Global instance
_global_position_sizing_engine = None


def get_position_sizing_engine() -> PositionSizingEngine:
    """Get the global position sizing engine instance."""
    global _global_position_sizing_engine
    if _global_position_sizing_engine is None:
        _global_position_sizing_engine = PositionSizingEngine()
    return _global_position_sizing_engine