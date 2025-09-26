"""
Trend Analysis API Endpoints - Phase 1B Implementation
Market Regime Intelligence Framework
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
from ..services.trend_detection_engine import get_trend_engine
from ..api.schemas import TrendAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{product_id}", response_model=TrendAnalysisResponse)
def get_trend_analysis(product_id: str) -> TrendAnalysisResponse:
    """
    Get comprehensive trend analysis for a trading pair.
    
    Args:
        product_id: Trading pair (e.g., "BTC-USD")
        
    Returns:
        Trend analysis with regime classification and confidence
    """
    try:
        trend_engine = get_trend_engine()
        result = trend_engine.analyze_trend(product_id)
        
        if 'error' in result:
            raise HTTPException(
                status_code=400, 
                detail=f"Trend analysis failed: {result['error']}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting trend analysis for {product_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze trend for {product_id}: {str(e)}"
        )


@router.get("/")
def get_multiple_trend_analysis(
    pairs: str = Query(..., description="Comma-separated trading pairs (e.g., 'BTC-USD,ETH-USD,SOL-USD')")
) -> Dict[str, Any]:
    """
    Get trend analysis for multiple trading pairs.
    
    Args:
        pairs: Comma-separated list of trading pairs
        
    Returns:
        Dict with trend analysis for each pair
    """
    try:
        # Parse pairs
        pair_list = [pair.strip().upper() for pair in pairs.split(',')]
        
        # Limit to prevent abuse
        if len(pair_list) > 12:
            raise HTTPException(
                status_code=400,
                detail="Maximum 12 pairs allowed per request"
            )
        
        trend_engine = get_trend_engine()
        results = {}
        
        for pair in pair_list:
            try:
                result = trend_engine.analyze_trend(pair)
                results[pair] = result
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                results[pair] = {
                    'product_id': pair,
                    'error': str(e),
                    'trend_strength': 0.0,
                    'confidence': 0.0,
                    'regime': 'NEUTRAL'
                }
        
        return {
            'pairs_analyzed': len(results),
            'results': results,
            'engine_stats': trend_engine.get_stats()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multiple trend analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze trends: {str(e)}"
        )


@router.get("/stats/engine")
def get_trend_engine_stats() -> Dict[str, Any]:
    """
    Get trend detection engine performance statistics.
    
    Returns:
        Engine performance metrics and cache statistics
    """
    try:
        trend_engine = get_trend_engine()
        stats = trend_engine.get_stats()
        
        return {
            'engine_performance': stats,
            'status': 'operational',
            'cache_ttl_minutes': stats['cache_ttl_seconds'] / 60
        }
        
    except Exception as e:
        logger.error(f"Error getting trend engine stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get engine stats: {str(e)}"
        )


@router.post("/cache/clear")
def clear_trend_cache() -> Dict[str, Any]:
    """
    Clear the trend detection cache (admin endpoint).
    
    Returns:
        Number of cached items cleared
    """
    try:
        trend_engine = get_trend_engine()
        cleared_count = trend_engine.clear_cache()
        
        logger.info(f"Trend detection cache cleared: {cleared_count} items")
        
        return {
            'message': 'Trend detection cache cleared',
            'cleared_items': cleared_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing trend cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/regime/summary")
def get_regime_summary() -> Dict[str, Any]:
    """
    Get regime classification summary for all active bot pairs.
    
    Returns:
        Summary of current market regimes across trading pairs
    """
    try:
        # Get active trading pairs from common bot pairs
        active_pairs = [
            "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
            "AVNT-USD", "AERO-USD", "SUI-USD", "AVAX-USD", "TOSHI-USD",
            "PENGU-USD", "ADA-USD"
        ]
        
        trend_engine = get_trend_engine()
        regime_counts = {
            'STRONG_TRENDING': 0,
            'TRENDING': 0, 
            'RANGING': 0,
            'CHOPPY': 0
        }
        
        pair_results = {}
        
        for pair in active_pairs:
            try:
                result = trend_engine.analyze_trend(pair)
                regime = result.get('regime', 'NEUTRAL')
                
                if regime in regime_counts:
                    regime_counts[regime] += 1
                
                pair_results[pair] = {
                    'regime': regime,
                    'trend_strength': result.get('trend_strength', 0.0),
                    'confidence': result.get('confidence', 0.0)
                }
                
            except Exception as e:
                logger.error(f"Error analyzing {pair} for regime summary: {e}")
                pair_results[pair] = {
                    'regime': 'ERROR',
                    'trend_strength': 0.0,
                    'confidence': 0.0,
                    'error': str(e)
                }
        
        # Calculate market sentiment
        total_pairs = len([p for p in pair_results.values() if p['regime'] != 'ERROR'])
        trending_pairs = regime_counts['STRONG_TRENDING'] + regime_counts['TRENDING']
        
        if total_pairs > 0:
            trending_percentage = (trending_pairs / total_pairs) * 100
        else:
            trending_percentage = 0
        
        return {
            'regime_distribution': regime_counts,
            'market_sentiment': {
                'trending_pairs': trending_pairs,
                'total_analyzed': total_pairs,
                'trending_percentage': round(trending_percentage, 1)
            },
            'individual_pairs': pair_results,
            'analysis_timestamp': trend_engine.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Error generating regime summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate regime summary: {str(e)}"
        )