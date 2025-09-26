#!/usr/bin/env python3
"""
Phase 3A Integration Test
Test that signal performance tracking is working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.models import Bot
from app.services.bot_evaluator import BotSignalEvaluator
from app.services.signal_performance_tracker import get_signal_performance_tracker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_phase3a_integration():
    """Test Phase 3A signal performance tracking integration"""
    logger.info("🧪 Testing Phase 3A Signal Performance Tracking")
    
    # Get database session
    db = SessionLocal()
    try:
        # Find BTC-USD bot for testing
        btc_bot = db.query(Bot).filter(Bot.pair == "BTC-USD").first()
        if not btc_bot:
            logger.error("❌ BTC-USD bot not found")
            return False
            
        logger.info(f"📊 Testing bot: {btc_bot.name} (ID: {btc_bot.id})")
        
        # Initialize bot evaluator with Phase 3A tracking
        evaluator = BotSignalEvaluator(db=db)
        
        # Get signal performance tracker
        performance_tracker = get_signal_performance_tracker(db)
        
        # Check initial state
        initial_predictions = sum(len(predictions) for predictions in performance_tracker.predictions.values())
        logger.info(f"📈 Initial predictions count: {initial_predictions}")
        
        # Evaluate bot signals (this should trigger tracking)
        try:
            from app.services.coinbase_service import CoinbaseService
            coinbase_service = CoinbaseService()
            
            # Get market data
            market_data = coinbase_service.get_historical_data(btc_bot.pair, granularity=3600, limit=100)
            if market_data is None or len(market_data) < 10:
                logger.warning(f"⚠️  Insufficient market data for {btc_bot.pair}")
                return False
            
            logger.info(f"📊 Market data: {len(market_data)} data points")
            
            # Evaluate signals
            evaluation_result = evaluator.evaluate_bot(btc_bot, market_data)
            
            logger.info(f"🎯 Evaluation result:")
            logger.info(f"   Overall score: {evaluation_result.get('overall_score', 0):.4f}")
            logger.info(f"   Action: {evaluation_result.get('action', 'unknown')}")
            logger.info(f"   Confidence: {evaluation_result.get('confidence', 0):.4f}")
            
            # Check if signal results were recorded
            signal_results = evaluation_result.get('signal_results', {})
            logger.info(f"   Signals evaluated: {list(signal_results.keys())}")
            
            # Check if predictions were recorded
            final_predictions = sum(len(predictions) for predictions in performance_tracker.predictions.values())
            new_predictions = final_predictions - initial_predictions
            
            logger.info(f"📊 Predictions after evaluation: {final_predictions} (+{new_predictions})")
            
            if new_predictions > 0:
                logger.info("✅ Phase 3A signal tracking is working!")
                
                # Show some prediction details
                for key, predictions in performance_tracker.predictions.items():
                    if predictions:
                        latest = predictions[-1]
                        logger.info(f"   Latest {key}: {latest.prediction} (score: {latest.signal_score:.3f})")
                
                return True
            else:
                logger.warning("⚠️  No new predictions recorded - tracking may not be working")
                return False
                
        except Exception as eval_error:
            logger.error(f"❌ Evaluation failed: {eval_error}")
            return False
            
    finally:
        db.close()
    
    return False

if __name__ == "__main__":
    success = test_phase3a_integration()
    if success:
        logger.info("🎉 Phase 3A Integration Test: PASSED")
    else:
        logger.error("💥 Phase 3A Integration Test: FAILED")
        sys.exit(1)