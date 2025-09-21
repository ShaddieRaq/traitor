"""
Market Analysis API endpoints.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..core.database import get_db
from ..models.models import Bot
from ..services.market_analysis_service import MarketAnalysisService
from ..tasks.market_analysis_tasks import periodic_market_scan, market_opportunity_alert

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analysis")
def get_market_analysis(
    limit: int = Query(50, ge=5, le=500, description="Number of candidates to analyze (max 500, ~313 USD pairs available)"),
    include_gems: bool = Query(True, description="Include gem hunting for high-scoring low-volume pairs"),
    db: Session = Depends(get_db)
):
    """
    Analyze potential trading pairs and recommend new bots.
    
    Automatically excludes pairs that already have active bots.
    Returns analysis with scoring, risk assessment, and recommendations.
    """
    try:
        # Get existing bot pairs to exclude
        existing_bots = db.query(Bot).all()
        exclude_pairs = [bot.pair for bot in existing_bots]
        
        # Initialize market analysis service
        analysis_service = MarketAnalysisService()
        
        # Perform analysis
        results = analysis_service.analyze_potential_pairs(
            exclude_pairs=exclude_pairs,
            limit=limit,
            include_gems=include_gems
        )
        
        # Add context about excluded pairs
        results["excluded_pairs"] = exclude_pairs
        results["active_bots_count"] = len(existing_bots)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in market analysis endpoint: {e}")
        return {
            "error": f"Market analysis failed: {str(e)}",
            "candidates": [],
            "summary": {"message": "Analysis unavailable"}
        }


@router.get("/analysis/{product_id}")
def get_single_pair_analysis(product_id: str):
    """
    Get detailed analysis for a specific trading pair.
    """
    try:
        analysis_service = MarketAnalysisService()
        
        # Get all products and find the specific one
        products = analysis_service.coinbase_service.get_products()
        if not products:
            return {"error": "Unable to fetch products from Coinbase"}
        
        # Find the specific product
        target_product = None
        for product in products:
            pid = getattr(product, 'product_id', None) or product.get('product_id', None) if hasattr(product, 'get') else getattr(product, 'product_id', None)
            if pid == product_id:
                target_product = product
                break
        
        if not target_product:
            return {"error": f"Product {product_id} not found"}
        
        # Analyze the single pair
        analysis = analysis_service._analyze_single_pair(target_product)
        
        if not analysis:
            return {"error": f"Unable to analyze {product_id}"}
        
        return {
            "product_id": product_id,
            "analysis": analysis,
            "timestamp": "2025-09-10T23:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing {product_id}: {e}")
        return {"error": f"Analysis failed for {product_id}: {str(e)}"}


@router.get("/comparison")
def compare_pairs(
    pairs: str = Query(..., description="Comma-separated list of pairs to compare"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple trading pairs side by side.
    
    Example: /api/v1/market-analysis/comparison?pairs=SOL-USD,AVAX-USD,ADA-USD
    """
    try:
        # Parse pairs
        pair_list = [pair.strip() for pair in pairs.split(',')]
        
        if len(pair_list) > 10:
            return {"error": "Maximum 10 pairs allowed for comparison"}
        
        analysis_service = MarketAnalysisService()
        products = analysis_service.coinbase_service.get_products()
        
        if not products:
            return {"error": "Unable to fetch products from Coinbase"}
        
        # Create product lookup
        product_lookup = {}
        for p in products:
            pid = getattr(p, 'product_id', None) or p.get('product_id', None) if hasattr(p, 'get') else getattr(p, 'product_id', None)
            if pid:
                product_lookup[pid] = p
        
        # Analyze each requested pair
        comparisons = []
        for pair in pair_list:
            if pair in product_lookup:
                analysis = analysis_service._analyze_single_pair(product_lookup[pair])
                if analysis:
                    comparisons.append(analysis)
            else:
                comparisons.append({
                    "product_id": pair,
                    "error": "Product not found or not tradeable"
                })
        
        # Sort by total score
        valid_comparisons = [c for c in comparisons if 'total_score' in c]
        valid_comparisons.sort(key=lambda x: x['total_score'], reverse=True)
        
        return {
            "comparisons": comparisons,
            "ranked_results": valid_comparisons,
            "total_compared": len(pair_list),
            "valid_analyses": len(valid_comparisons),
            "timestamp": "2025-09-10T23:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error in pair comparison: {e}")
        return {"error": f"Comparison failed: {str(e)}"}


@router.post("/auto-create-bot/{product_id}")
def auto_create_bot_for_pair(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Automatically create a trading bot for a specific product pair.
    
    Analyzes the pair first and only creates bot if it meets quality criteria.
    """
    try:
        analysis_service = MarketAnalysisService()
        result = analysis_service.auto_create_bot_for_opportunity(product_id, db)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error in auto bot creation for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Auto bot creation failed: {str(e)}")


@router.post("/scan-and-create")
def scan_market_and_auto_create_bots(
    max_bots: int = Query(2, ge=1, le=5, description="Maximum number of bots to create"),
    min_score: float = Query(18.0, ge=10.0, le=25.0, description="Minimum score threshold"),
    db: Session = Depends(get_db)
):
    """
    Scan the entire market for opportunities and automatically create bots for top candidates.
    
    This is the main auto bot creation endpoint that:
    1. Scans all available trading pairs
    2. Filters by score and quality criteria  
    3. Creates bots for the best opportunities
    """
    try:
        analysis_service = MarketAnalysisService()
        result = analysis_service.scan_and_auto_create_bots(
            db_session=db,
            max_new_bots=max_bots,
            min_score=min_score
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in scan and auto-create: {e}")
        raise HTTPException(status_code=500, detail=f"Scan and auto-create failed: {str(e)}")


@router.post("/trigger-scan")
def trigger_manual_market_scan():
    """
    Manually trigger a market scan task.
    Useful for testing or immediate analysis outside the scheduled intervals.
    """
    try:
        # Trigger the background task
        task_result = periodic_market_scan.delay()
        
        return {
            "success": True,
            "message": "Market scan task triggered",
            "task_id": task_result.id
        }
        
    except Exception as e:
        logger.error(f"Error triggering market scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


@router.post("/trigger-opportunity-alert")
def trigger_opportunity_alert(min_score: float = Query(12.0, ge=8.0, le=25.0)):
    """
    Manually trigger an opportunity alert check.
    """
    try:
        # Trigger the background task
        task_result = market_opportunity_alert.delay(min_score=min_score)
        
        return {
            "success": True,
            "message": f"Opportunity alert triggered for scores >= {min_score}",
            "task_id": task_result.id
        }
        
    except Exception as e:
        logger.error(f"Error triggering opportunity alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger alert: {str(e)}")


@router.get("/automation-status")
def get_market_analysis_automation_status():
    """
    Get the status of automated market analysis tasks.
    """
    try:
        return {
            "automated_scanning": {
                "enabled": True,
                "frequency": "Every 60 minutes",
                "task_name": "periodic-market-scan",
                "description": "Comprehensive analysis of top 25 trading pairs"
            },
            "opportunity_alerts": {
                "enabled": True,
                "frequency": "Every 30 minutes", 
                "task_name": "market-opportunity-alert",
                "description": "Alerts for exceptional opportunities (score >= 12.0)"
            },
            "manual_triggers": {
                "scan_endpoint": "/api/v1/market-analysis/trigger-scan",
                "alert_endpoint": "/api/v1/market-analysis/trigger-opportunity-alert"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

