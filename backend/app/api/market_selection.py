"""
Phase 8.2: Market Selection Learning API Endpoints
API for analyzing market performance and auto-pausing losers/scaling winners
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.market_selection_learner import get_market_selection_learner

router = APIRouter(prefix="/api/v1/market-selection", tags=["Market Selection Learning"])


class MarketAnalysisResponse(BaseModel):
    """Response model for market performance analysis"""
    timestamp: str
    winners: list = Field(..., description="Profitable bots that should be scaled up")
    losers: list = Field(..., description="Losing bots that should be paused") 
    neutral: list = Field(..., description="Neutral performance bots")
    recommendations: dict = Field(..., description="Action recommendations per pair")
    total_bots_analyzed: int = Field(..., description="Total bots included in analysis")


class AutoPauseResponse(BaseModel):
    """Response model for auto-pause loser bots"""
    dry_run: bool
    timestamp: str
    bots_paused: list = Field(..., description="Bots that were (or would be) paused")
    bots_skipped: list = Field(..., description="Losing bots that were skipped")
    total_loss_prevented: float = Field(..., description="Total losses that were prevented")


class AutoScaleResponse(BaseModel):
    """Response model for auto-scale winner bots"""  
    dry_run: bool
    timestamp: str
    bots_scaled: list = Field(..., description="Bots that were (or would be) scaled up")
    total_profit_potential: float = Field(..., description="Total profit potential identified")
    message: str = Field(..., description="Status message about scaling implementation")


@router.get("/analyze", response_model=MarketAnalysisResponse)
def analyze_market_performance(
    db: Session = Depends(get_db)
):
    """
    Analyze performance of all active bots to classify markets as winners/losers.
    
    This is the core market selection learning analysis that identifies:
    - Winner bots that should be scaled up (alt-coins like AVNT, XAN)
    - Loser bots that should be paused (major coins like BTC, ETH)
    - Neutral bots that should be monitored
    
    Based on Phase 8 discovery:
    - Alt-coins average +$2.89 profit  
    - Major coins average -$4.49 loss
    """
    try:
        learner = get_market_selection_learner()
        analysis = learner.analyze_market_performance(db)
        
        if 'error' in analysis:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis['error']}")
        
        return MarketAnalysisResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market analysis failed: {str(e)}")


@router.post("/auto-pause-losers", response_model=AutoPauseResponse)
def auto_pause_losing_bots(
    dry_run: bool = Query(True, description="If true, simulate without actually pausing bots"),
    min_loss_threshold: float = Query(-10.0, description="Minimum loss to trigger auto-pause"),
    db: Session = Depends(get_db)
):
    """
    Automatically pause bots that are consistently losing money.
    
    This implements the core market selection learning principle:
    Stop doing what doesn't work (major coins losing money).
    
    Safety features:
    - Dry run mode by default
    - Configurable loss threshold  
    - Only pauses bots with significant losses
    - Logs all actions for audit trail
    
    Known losers from Phase 8 analysis:
    - SQD-USD: -$25.44
    - ZORA-USD: -$19.28  
    - IP-USD: -$9.38
    """
    try:
        learner = get_market_selection_learner()
        learner.min_loss_threshold = min_loss_threshold  # Apply custom threshold
        
        result = learner.auto_pause_losers(db, dry_run=dry_run)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=f"Auto-pause failed: {result['error']}")
        
        return AutoPauseResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-pause failed: {str(e)}")


@router.post("/auto-scale-winners", response_model=AutoScaleResponse) 
def auto_scale_winning_bots(
    dry_run: bool = Query(True, description="If true, simulate without actually scaling bots"),
    min_profit_threshold: float = Query(5.0, description="Minimum profit to trigger auto-scaling"),
    db: Session = Depends(get_db)
):
    """
    Automatically scale up bots that are consistently profitable.
    
    This implements the market selection learning principle:
    Do more of what works (alt-coins making money).
    
    Current implementation identifies profitable bots for scaling.
    Future integration with position sizing engine will implement actual scaling.
    
    Known winners from Phase 8 analysis:
    - AVNT-USD: +$60.31 (TOP PERFORMER)
    - XAN-USD: +$8.11
    - USELESS-USD: +$3.02
    """
    try:
        learner = get_market_selection_learner()
        learner.min_profit_threshold = min_profit_threshold  # Apply custom threshold
        
        result = learner.auto_scale_winners(db, dry_run=dry_run)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=f"Auto-scale failed: {result['error']}")
        
        return AutoScaleResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-scale failed: {str(e)}")


@router.get("/market-insights")
def get_market_insights(
    db: Session = Depends(get_db)
):
    """
    Get high-level insights about market performance patterns.
    
    This provides strategic insights for manual decision making:
    - Which market types (major vs alt-coins) are performing better
    - Overall system profitability trends
    - Recommendations for portfolio allocation
    """
    try:
        learner = get_market_selection_learner()
        analysis = learner.analyze_market_performance(db)
        
        if 'error' in analysis:
            return {"error": analysis['error']}
        
        # Calculate insights
        total_winner_profit = sum(bot['total_pnl'] for bot in analysis['winners'])
        total_loser_loss = sum(bot['total_pnl'] for bot in analysis['losers'])
        net_portfolio_pnl = total_winner_profit + total_loser_loss
        
        # Classify pairs by type
        major_coins = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SUI-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD']
        alt_coins = []
        major_performance = 0.0
        alt_performance = 0.0
        
        for bot in analysis['winners'] + analysis['losers'] + analysis['neutral']:
            if bot['pair'] in major_coins:
                major_performance += bot['total_pnl']
            else:
                alt_coins.append(bot['pair'])
                alt_performance += bot['total_pnl']
        
        insights = {
            'timestamp': datetime.utcnow().isoformat(),
            'portfolio_performance': {
                'net_pnl': net_portfolio_pnl,
                'total_winner_profit': total_winner_profit,
                'total_loser_loss': total_loser_loss,
                'winner_count': len(analysis['winners']),
                'loser_count': len(analysis['losers'])
            },
            'market_type_analysis': {
                'major_coins': {
                    'pairs': major_coins,
                    'total_pnl': major_performance,
                    'average_pnl': major_performance / len(major_coins) if major_coins else 0
                },
                'alt_coins': {
                    'pairs': list(set(alt_coins)),
                    'total_pnl': alt_performance,
                    'average_pnl': alt_performance / len(set(alt_coins)) if alt_coins else 0
                }
            },
            'strategic_insights': {
                'primary_insight': 'Alt-coins outperforming major coins' if alt_performance > major_performance else 'Major coins outperforming alt-coins',
                'recommended_action': 'Focus on alt-coin opportunities' if alt_performance > major_performance else 'Reassess alt-coin strategy',
                'risk_assessment': 'High' if total_loser_loss < -50 else 'Medium' if total_loser_loss < -20 else 'Low'
            },
            'phase_8_validation': {
                'hypothesis': 'Alt-coins average +$2.89, Major coins average -$4.49',
                'current_data_confirms': alt_performance > major_performance,
                'learning_system_working': len(analysis['winners']) > 0 and len(analysis['losers']) > 0
            }
        }
        
        return insights
        
    except Exception as e:
        return {"error": f"Market insights failed: {str(e)}"}