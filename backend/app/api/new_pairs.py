"""
API endpoints for new trading pair detection and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..services.new_pair_detector import get_new_pair_detector

router = APIRouter()


@router.get("/scan")
def scan_for_new_pairs(db: Session = Depends(get_db)):
    """
    Manually trigger a scan for new trading pairs.
    
    Returns results of the scan including any newly discovered pairs.
    """
    try:
        detector = get_new_pair_detector()
        results = detector.scan_for_new_pairs(db)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/recent")
def get_recent_new_pairs(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get recently discovered trading pairs within the specified timeframe.
    
    Args:
        days: Number of days to look back (1-30)
    
    Returns:
        List of recently discovered USD trading pairs
    """
    try:
        detector = get_new_pair_detector()
        recent_pairs = detector.get_recent_new_pairs(db, days)
        
        return {
            "success": True,
            "timeframe_days": days,
            "pairs_found": len(recent_pairs),
            "pairs": recent_pairs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent pairs: {str(e)}")


@router.post("/mark-processed")
def mark_pairs_as_processed(
    product_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    Mark trading pairs as processed (no longer 'new').
    
    Args:
        product_ids: List of product IDs to mark as processed
    
    Returns:
        Confirmation of processing
    """
    try:
        if not product_ids:
            raise HTTPException(status_code=400, detail="No product IDs provided")
        
        detector = get_new_pair_detector()
        detector.mark_pairs_as_processed(db, product_ids)
        
        return {
            "success": True,
            "message": f"Marked {len(product_ids)} pairs as processed",
            "processed_pairs": product_ids
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark pairs as processed: {str(e)}")


@router.get("/stats")
def get_new_pair_stats(db: Session = Depends(get_db)):
    """
    Get statistics about new pair detection system.
    
    Returns:
        Statistics and system status
    """
    try:
        from ..models.models import TradingPair
        from datetime import datetime, timedelta
        
        # Get basic stats
        total_pairs = db.query(TradingPair).count()
        usd_pairs = db.query(TradingPair).filter(TradingPair.quote_currency_id == 'USD').count()
        new_pairs = db.query(TradingPair).filter(TradingPair.is_new_listing == True).count()
        
        # Recent activity
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_pairs = db.query(TradingPair).filter(
            TradingPair.first_seen >= recent_cutoff
        ).count()
        
        # Latest discovery
        latest_pair = db.query(TradingPair).filter(
            TradingPair.quote_currency_id == 'USD'
        ).order_by(TradingPair.first_seen.desc()).first()
        
        return {
            "success": True,
            "stats": {
                "total_pairs_tracked": total_pairs,
                "usd_pairs_tracked": usd_pairs,
                "unprocessed_new_pairs": new_pairs,
                "pairs_discovered_last_7_days": recent_pairs,
                "latest_discovery": {
                    "product_id": latest_pair.product_id if latest_pair else None,
                    "base_name": latest_pair.base_name if latest_pair else None,
                    "discovered_at": latest_pair.first_seen.isoformat() if latest_pair else None
                } if latest_pair else None
            },
            "system_info": {
                "detection_enabled": True,
                "scan_frequency": "Every 2 hours",
                "alert_threshold": "USD pairs only",
                "retention_period": "Indefinite"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/analyze/{product_id}")
def analyze_new_pair(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis of a specific new trading pair.
    
    Args:
        product_id: Trading pair ID (e.g., "NEW-USD")
    
    Returns:
        Detailed analysis including market data and recommendations
    """
    try:
        from ..models.models import TradingPair
        from ..services.market_analysis_service import MarketAnalysisService
        
        # Get pair info from our database
        pair = db.query(TradingPair).filter(TradingPair.product_id == product_id).first()
        if not pair:
            raise HTTPException(status_code=404, detail=f"Pair {product_id} not found in tracking database")
        
        # Get current market analysis
        analysis_service = MarketAnalysisService()
        
        # Try to get current product data from Coinbase
        products = analysis_service.coinbase_service.get_products()
        current_product = None
        for product in products:
            if getattr(product, 'product_id', '') == product_id:
                current_product = product
                break
        
        if not current_product:
            return {
                "success": False,
                "error": f"Pair {product_id} not found on Coinbase (may be delisted)",
                "pair_info": {
                    "product_id": pair.product_id,
                    "base_name": pair.base_name,
                    "status": pair.status,
                    "first_seen": pair.first_seen.isoformat(),
                    "initial_price": pair.initial_price,
                    "initial_volume_24h": pair.initial_volume_24h
                }
            }
        
        # Analyze the current state
        analysis = analysis_service._analyze_single_pair(current_product)
        
        return {
            "success": True,
            "pair_info": {
                "product_id": pair.product_id,
                "base_name": pair.base_name,
                "status": pair.status,
                "first_seen": pair.first_seen.isoformat(),
                "days_since_listing": (datetime.utcnow() - pair.first_seen).days,
                "is_new_listing": pair.is_new_listing
            },
            "initial_data": {
                "price": pair.initial_price,
                "volume_24h": pair.initial_volume_24h
            },
            "current_analysis": analysis,
            "performance_since_listing": {
                "price_change": ((analysis['price'] - pair.initial_price) / pair.initial_price * 100) if pair.initial_price else None,
                "volume_change": ((analysis['volume_24h_million'] * 1000000 - pair.initial_volume_24h) / pair.initial_volume_24h * 100) if pair.initial_volume_24h else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
