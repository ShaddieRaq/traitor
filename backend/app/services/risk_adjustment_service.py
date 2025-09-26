# Risk Adjustment Service for Dynamic Position Sizing
# Implementation Phase 1: Rolling Performance Calculation

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import requests
import logging

logger = logging.getLogger(__name__)

class RiskAdjustmentService:
    """
    Dynamic Risk Adjustment Service
    
    Calculates risk multipliers based on:
    1. Signal strength (heavily weighted)
    2. Confidence level (lightly weighted)  
    3. Recent performance (last 50 trades)
    """
    
    def __init__(self, db_session: Session, api_base_url: str = "http://localhost:8000"):
        self.db = db_session
        self.api_base_url = api_base_url
        
        # Risk calculation parameters
        self.signal_weight = 2.0        # Signal strength heavily weighted
        self.confidence_weight = 0.5    # Confidence lightly weighted
        self.performance_scale = 10.0   # $0.10 profit = 2x multiplier
        self.min_risk_multiplier = 0.2  # Minimum risk (defensive mode)
        self.max_risk_multiplier = 3.0  # Maximum risk (aggressive mode)
        self.rolling_window = 50        # Number of trades for performance calculation
    
    def get_recent_trades(self, product_id: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a product from the API."""
        try:
            url = f"{self.api_base_url}/api/v1/raw-trades/"
            params = {"product_id": product_id, "limit": limit}
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get recent trades for {product_id}: {e}")
            return []
    
    def calculate_rolling_pnl(self, product_id: str, window: int = 50) -> Dict:
        """
        Calculate rolling P&L for the last N trades.
        
        Returns:
        {
            'total_pnl': float,
            'avg_pnl_per_trade': float,
            'trade_count': int,
            'win_count': int,
            'loss_count': int,
            'win_rate': float
        }
        """
        trades = self.get_recent_trades(product_id, window)
        
        if not trades:
            logger.warning(f"No trades found for {product_id}")
            return {
                'total_pnl': 0.0,
                'avg_pnl_per_trade': 0.0,
                'trade_count': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0
            }
        
        # Calculate P&L using a simplified approach
        # Note: This is a basic implementation - we can enhance with proper position tracking
        total_buy_value = sum(float(t['usd_value']) for t in trades if t['side'] == 'BUY')
        total_sell_value = sum(float(t['usd_value']) for t in trades if t['side'] == 'SELL')
        
        # For now, calculate net flow (this will be enhanced with proper position tracking)
        net_pnl = total_sell_value - total_buy_value
        avg_pnl = net_pnl / len(trades) if trades else 0.0
        
        # Simple win/loss calculation (enhancement needed)
        buy_trades = [t for t in trades if t['side'] == 'BUY']
        sell_trades = [t for t in trades if t['side'] == 'SELL']
        
        # For now, assume equal buy/sell pairs (will enhance this)
        win_count = min(len(buy_trades), len(sell_trades))
        loss_count = abs(len(buy_trades) - len(sell_trades))
        win_rate = win_count / (win_count + loss_count) if (win_count + loss_count) > 0 else 0.0
        
        return {
            'total_pnl': net_pnl,
            'avg_pnl_per_trade': avg_pnl,
            'trade_count': len(trades),
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate
        }
    
    def calculate_risk_multiplier(self, signal_strength: float, confidence: float, 
                                performance_data: Dict) -> float:
        """
        Calculate risk multiplier using the framework formula.
        
        risk_multiplier = (signal_component + confidence_component) * performance_multiplier
        Bounded between min_risk_multiplier and max_risk_multiplier
        """
        # Signal component (heavily weighted)
        signal_component = min(signal_strength * self.signal_weight, 2.0)
        
        # Confidence component (lightly weighted)
        confidence_component = confidence * self.confidence_weight
        
        # Performance multiplier (recent P&L impact)
        avg_pnl = performance_data.get('avg_pnl_per_trade', 0.0)
        performance_multiplier = 1.0 + (avg_pnl * self.performance_scale)
        
        # Final calculation
        risk_multiplier = (signal_component + confidence_component) * performance_multiplier
        
        # Apply bounds
        risk_multiplier = max(self.min_risk_multiplier, min(self.max_risk_multiplier, risk_multiplier))
        
        logger.info(f"Risk calculation: signal={signal_strength:.3f}, confidence={confidence:.3f}, "
                   f"avg_pnl={avg_pnl:.4f}, multiplier={risk_multiplier:.2f}")
        
        return risk_multiplier
    
    def get_bot_risk_multiplier(self, bot_id: int, product_id: str, 
                               signal_strength: float, confidence: float) -> Dict:
        """
        Get complete risk assessment for a bot.
        
        Returns:
        {
            'risk_multiplier': float,
            'performance_data': dict,
            'calculation_reason': str,
            'calculated_at': datetime
        }
        """
        # Get recent performance
        performance_data = self.calculate_rolling_pnl(product_id, self.rolling_window)
        
        # Calculate risk multiplier
        risk_multiplier = self.calculate_risk_multiplier(signal_strength, confidence, performance_data)
        
        # Generate explanation
        reason = self._generate_calculation_reason(signal_strength, confidence, 
                                                 performance_data, risk_multiplier)
        
        return {
            'risk_multiplier': risk_multiplier,
            'performance_data': performance_data,
            'calculation_reason': reason,
            'calculated_at': datetime.utcnow()
        }
    
    def _generate_calculation_reason(self, signal_strength: float, confidence: float,
                                   performance_data: Dict, risk_multiplier: float) -> str:
        """Generate human-readable explanation for the risk calculation."""
        signal_desc = "HIGH" if signal_strength > 0.8 else "MEDIUM" if signal_strength > 0.5 else "LOW"
        confidence_desc = "HIGH" if confidence > 0.5 else "MEDIUM" if confidence > 0.3 else "LOW"
        
        avg_pnl = performance_data.get('avg_pnl_per_trade', 0.0)
        pnl_desc = "PROFITABLE" if avg_pnl > 0.05 else "NEUTRAL" if avg_pnl > -0.05 else "LOSING"
        
        reason = f"{signal_desc} signal ({signal_strength:.2f}) + {confidence_desc} confidence ({confidence:.2f}) + {pnl_desc} performance (${avg_pnl:.4f}/trade) → {risk_multiplier:.2f}x risk"
        
        if risk_multiplier >= 2.5:
            reason += " (AGGRESSIVE)"
        elif risk_multiplier <= 0.5:
            reason += " (DEFENSIVE)"
        else:
            reason += " (NORMAL)"
        
        return reason

# Test function to validate the implementation
def test_risk_adjustment_service():
    """Test the risk adjustment service with real data."""
    service = RiskAdjustmentService(None)  # No DB session needed for testing
    
    print("🧪 TESTING RISK ADJUSTMENT SERVICE")
    print("=" * 50)
    
    # Test with AVNT data (known winner)
    avnt_result = service.get_bot_risk_multiplier(
        bot_id=9,
        product_id="AVNT-USD", 
        signal_strength=0.92,
        confidence=0.32
    )
    
    print(f"📈 AVNT-USD Test:")
    print(f"   Risk Multiplier: {avnt_result['risk_multiplier']:.2f}x")
    print(f"   Reason: {avnt_result['calculation_reason']}")
    print(f"   Recent Performance: ${avnt_result['performance_data']['avg_pnl_per_trade']:.4f}/trade")
    print()
    
    # Test with ETH data (known underperformer)  
    eth_result = service.get_bot_risk_multiplier(
        bot_id=4,
        product_id="ETH-USD",
        signal_strength=0.43,
        confidence=0.21
    )
    
    print(f"📉 ETH-USD Test:")
    print(f"   Risk Multiplier: {eth_result['risk_multiplier']:.2f}x")
    print(f"   Reason: {eth_result['calculation_reason']}")
    print(f"   Recent Performance: ${eth_result['performance_data']['avg_pnl_per_trade']:.4f}/trade")
    print()
    
    print("✅ Risk Adjustment Service Testing Complete!")

if __name__ == "__main__":
    test_risk_adjustment_service()