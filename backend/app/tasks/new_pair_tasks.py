"""
Celery tasks for new trading pair detection.
"""

import logging
from ..core.database import get_db
from ..services.new_pair_detector import get_new_pair_detector
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="scan_for_new_pairs_task")
def scan_for_new_pairs_task():
    """
    Background task to scan for newly listed trading pairs on Coinbase.
    Runs periodically to detect new opportunities early.
    """
    try:
        logger.info("🔍 Starting automated new pair detection scan...")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Initialize new pair detector
            detector = get_new_pair_detector()
            
            # Perform the scan
            results = detector.scan_for_new_pairs(db)
            
            if "error" in results:
                logger.error(f"New pair scan failed: {results['error']}")
                return {"success": False, "error": results["error"]}
            
            # Log results
            new_pairs_count = results.get("new_pairs_found", 0)
            usd_pairs_count = results.get("usd_pairs_found", 0)
            
            if new_pairs_count > 0:
                logger.info(f"🆕 Found {new_pairs_count} new trading pairs ({usd_pairs_count} USD pairs)")
                
                # Log details of new USD pairs
                new_pairs = results.get("new_pairs", [])
                for pair in new_pairs:
                    logger.info(f"   • {pair['product_id']}: {pair['base_name']} - ${pair['initial_price']:.4f}")
                
                if usd_pairs_count > 0:
                    logger.info(f"📢 Created notifications for {usd_pairs_count} new USD pairs")
            else:
                logger.info("✅ New pair scan complete: No new pairs found")
            
            return {
                "success": True,
                "timestamp": results.get("timestamp"),
                "total_products_scanned": results.get("total_products_scanned", 0),
                "new_pairs_found": new_pairs_count,
                "usd_pairs_found": usd_pairs_count,
                "notifications_created": usd_pairs_count
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in new pair detection task: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="analyze_new_pair_task")
def analyze_new_pair_task(product_id: str):
    """
    Background task to analyze a specific new trading pair.
    
    Args:
        product_id: Trading pair to analyze (e.g., "NEW-USD")
    """
    try:
        logger.info(f"🔍 Analyzing new pair: {product_id}")
        
        db = next(get_db())
        
        try:
            from ..services.market_analysis_service import MarketAnalysisService
            from ..models.models import TradingPair
            
            # Get pair info
            pair = db.query(TradingPair).filter(TradingPair.product_id == product_id).first()
            if not pair:
                logger.error(f"Pair {product_id} not found in database")
                return {"success": False, "error": "Pair not found"}
            
            # Perform analysis
            analysis_service = MarketAnalysisService()
            products = analysis_service.coinbase_service.get_products()
            
            # Find the specific product
            target_product = None
            for product in products:
                if getattr(product, 'product_id', '') == product_id:
                    target_product = product
                    break
            
            if not target_product:
                logger.warning(f"Pair {product_id} not found on Coinbase (may be delisted)")
                return {"success": False, "error": "Pair not available on Coinbase"}
            
            # Analyze the pair
            analysis = analysis_service._analyze_single_pair(target_product)
            
            if analysis and analysis.get('total_score', 0) >= 12:
                logger.info(f"🎯 New pair {product_id} shows promise: Score {analysis['total_score']:.1f}")
                
                # Create a high-priority notification for promising new pairs
                from ..services.notification_service import get_notification_service
                notification_service = get_notification_service()
                
                notification_service.create_notification(
                    type="promising_new_pair",
                    title=f"🚀 Promising New Pair: {product_id}",
                    message=f"New pair {product_id} ({pair.base_name}) scored {analysis['total_score']:.1f}/25 in analysis!\n\n"
                           f"💰 Price: ${analysis['price']:.4f}\n"
                           f"📊 Volume: ${analysis['volume_24h_million']:.1f}M\n"
                           f"📈 Score breakdown: L:{analysis['liquidity_score']:.1f} V:{analysis['volatility_score']:.1f} M:{analysis['momentum_score']:.1f}\n"
                           f"⚠️ Risk: {analysis['risk_level']}\n"
                           f"💡 Recommendation: {analysis['recommendation']}\n\n"
                           f"🔍 Consider creating a bot for this opportunity!",
                    priority="high",
                    data={
                        "product_id": product_id,
                        "analysis": analysis,
                        "days_since_listing": (db.query(TradingPair).filter(TradingPair.product_id == product_id).first().first_seen).days if pair else 0
                    }
                )
                
                return {
                    "success": True,
                    "product_id": product_id,
                    "analysis": analysis,
                    "promising": True,
                    "notification_created": True
                }
            else:
                logger.info(f"📊 New pair {product_id} analyzed: Score {analysis.get('total_score', 0):.1f} (below threshold)")
                return {
                    "success": True,
                    "product_id": product_id,
                    "analysis": analysis,
                    "promising": False
                }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error analyzing new pair {product_id}: {e}")
        return {"success": False, "error": str(e)}
