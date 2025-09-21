"""
Market Analysis Background Tasks.
Automated scanning for new trading opportunities and bot recommendations.
"""

import logging
from typing import Dict, Any, List
from ..tasks.celery_app import celery_app
from ..services.market_analysis_service import MarketAnalysisService
from ..services.notification_service import get_notification_service
from ..models.models import Bot
from ..core.database import get_db

logger = logging.getLogger(__name__)


@celery_app.task(name="periodic_market_scan")
def periodic_market_scan():
    """
    Periodic market analysis to identify new trading opportunities.
    Runs automatically to scan for high-scoring potential bot pairs.
    """
    try:
        logger.info("🔍 Starting periodic market scan...")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get existing bot pairs to exclude
            existing_bots = db.query(Bot).all()
            exclude_pairs = [bot.pair for bot in existing_bots]
            
            # Initialize market analysis service
            analysis_service = MarketAnalysisService()
            
            # Perform comprehensive analysis (top 100 pairs with gem hunting)
            results = analysis_service.analyze_potential_pairs(
                exclude_pairs=exclude_pairs,
                limit=100,
                include_gems=True
            )
            
            if "error" in results:
                logger.error(f"Market analysis failed: {results['error']}")
                return {"success": False, "error": results["error"]}
            
            # Analyze results for noteworthy opportunities
            opportunities = _analyze_scan_results(results)
            
            # Create notifications for significant opportunities
            notification_service = get_notification_service()
            if opportunities["new_high_scorers"]:
                notification_service.create_market_opportunity_notification(
                    opportunities["new_high_scorers"],
                    results.get("summary", {})
                )
            
            # Log summary
            total_candidates = len(results.get("candidates", []))
            good_candidates = results.get("summary", {}).get("counts", {}).get("good_candidates", 0)
            
            logger.info(f"✅ Market scan complete: {total_candidates} analyzed, {good_candidates} good candidates")
            
            # Log top opportunities
            if opportunities["new_high_scorers"]:
                logger.info(f"🎯 High-scoring opportunities found: {len(opportunities['new_high_scorers'])}")
                for opp in opportunities["new_high_scorers"][:3]:  # Top 3
                    logger.info(f"   • {opp['product_id']}: {opp['total_score']:.1f}/25 ({opp['recommendation']})")
            
            if opportunities["momentum_surges"]:
                logger.info(f"🚀 Momentum surges detected: {len(opportunities['momentum_surges'])}")
                for surge in opportunities["momentum_surges"][:3]:
                    logger.info(f"   • {surge['product_id']}: +{surge['volume_change_24h']:.1f}% volume surge")
            
            return {
                "success": True,
                "timestamp": results.get("timestamp"),
                "total_analyzed": total_candidates,
                "good_candidates": good_candidates,
                "opportunities": opportunities
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in periodic market scan: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="market_opportunity_alert")
def market_opportunity_alert(min_score: float = 12.0):
    """
    Check for exceptional market opportunities and alert if found.
    
    Args:
        min_score: Minimum total score to trigger an alert
    """
    try:
        logger.info(f"🚨 Checking for market opportunities above {min_score} score...")
        
        db = next(get_db())
        
        try:
            existing_bots = db.query(Bot).all()
            exclude_pairs = [bot.pair for bot in existing_bots]
            
            analysis_service = MarketAnalysisService()
            results = analysis_service.analyze_potential_pairs(
                exclude_pairs=exclude_pairs,
                limit=15  # Focus on top candidates
            )
            
            if "error" in results:
                return {"success": False, "error": results["error"]}
            
            # Find exceptional opportunities
            exceptional_opportunities = []
            for candidate in results.get("candidates", []):
                if candidate.get("total_score", 0) >= min_score:
                    exceptional_opportunities.append(candidate)
            
            if exceptional_opportunities:
                # Create notification for exceptional opportunities
                notification_service = get_notification_service()
                notification_service.create_market_opportunity_notification(
                    exceptional_opportunities,
                    {"alert_threshold": min_score}
                )
                
                logger.warning(f"🎯 EXCEPTIONAL OPPORTUNITIES FOUND: {len(exceptional_opportunities)} pairs above {min_score}")
                for opp in exceptional_opportunities:
                    logger.warning(f"   💎 {opp['product_id']}: {opp['total_score']:.1f}/25 - {opp['recommendation']}")
                    logger.warning(f"      Price: ${opp['price']:.4f}, Volume: ${opp['volume_24h_million']:.1f}M")
                    logger.warning(f"      Change: {opp['price_change_24h']:+.1f}%, Momentum: {opp['volume_change_24h']:+.1f}%")
            
            return {
                "success": True,
                "exceptional_count": len(exceptional_opportunities),
                "opportunities": exceptional_opportunities
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in market opportunity alert: {e}")
        return {"success": False, "error": str(e)}


def _analyze_scan_results(results: Dict[str, Any]) -> Dict[str, List]:
    """
    Analyze market scan results to identify noteworthy patterns.
    
    Returns:
        Dict with categorized opportunities
    """
    candidates = results.get("candidates", [])
    
    # High scoring opportunities (>12/25)
    new_high_scorers = [
        c for c in candidates 
        if c.get("total_score", 0) >= 12.0 and c.get("recommendation") == "GOOD_CANDIDATE"
    ]
    
    # Momentum surges (>100% volume growth)
    momentum_surges = [
        c for c in candidates 
        if c.get("volume_change_24h", 0) >= 100.0
    ]
    
    # High volatility opportunities (>15% price change)
    volatility_plays = [
        c for c in candidates 
        if abs(c.get("price_change_24h", 0)) >= 15.0
    ]
    
    # Large volume pairs (>20M)
    large_volume = [
        c for c in candidates 
        if c.get("volume_24h_million", 0) >= 20.0
    ]
    
    return {
        "new_high_scorers": new_high_scorers,
        "momentum_surges": momentum_surges,
        "volatility_plays": volatility_plays,
        "large_volume": large_volume
    }
