#!/usr/bin/env python3
"""
Phase 3A Database Migration: Add Signal Performance Tracking Tables

Creates the following tables:
- signal_predictions: Individual signal predictions for performance evaluation
- signal_performance_metrics: Aggregated performance metrics
- adaptive_signal_weights: Dynamic signal weights based on performance
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_signal_performance_tables():
    """Create the Phase 3A signal performance tracking tables"""
    
    # SQL statements for table creation
    tables = {
        "signal_predictions": """
            CREATE TABLE IF NOT EXISTS signal_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pair VARCHAR(20) NOT NULL,
                regime VARCHAR(20) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                signal_score FLOAT,
                prediction VARCHAR(10),
                confidence FLOAT,
                actual_price_change_pct FLOAT,
                outcome VARCHAR(20),
                evaluation_timestamp DATETIME,
                trade_executed BOOLEAN DEFAULT FALSE,
                trade_id INTEGER,
                trade_pnl_usd FLOAT,
                evaluation_period_minutes INTEGER DEFAULT 60,
                FOREIGN KEY (trade_id) REFERENCES trades (id)
            )
        """,
        
        "signal_performance_metrics": """
            CREATE TABLE IF NOT EXISTS signal_performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair VARCHAR(20) NOT NULL,
                regime VARCHAR(20) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                accuracy FLOAT DEFAULT 0.0,
                precision_val FLOAT DEFAULT 0.0,  -- 'precision' is SQL keyword
                recall_val FLOAT DEFAULT 0.0,     -- 'recall' is SQL keyword
                avg_confidence FLOAT DEFAULT 0.0,
                avg_pnl_usd FLOAT DEFAULT 0.0,
                calculation_period_days INTEGER DEFAULT 30,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                min_samples_required INTEGER DEFAULT 20,
                is_reliable BOOLEAN DEFAULT FALSE
            )
        """,
        
        "adaptive_signal_weights": """
            CREATE TABLE IF NOT EXISTS adaptive_signal_weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                pair VARCHAR(20) NOT NULL,
                regime VARCHAR(20) NOT NULL,
                signal_weights TEXT,  -- JSON format
                default_weights TEXT, -- JSON format
                weight_calculation_method VARCHAR(50) DEFAULT 'performance_weighted',
                performance_period_days INTEGER DEFAULT 30,
                confidence_score FLOAT DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (bot_id) REFERENCES bots (id)
            )
        """
    }
    
    # Create indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_signal_predictions_pair_regime ON signal_predictions(pair, regime)",
        "CREATE INDEX IF NOT EXISTS idx_signal_predictions_signal_type ON signal_predictions(signal_type)",
        "CREATE INDEX IF NOT EXISTS idx_signal_predictions_timestamp ON signal_predictions(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_signal_performance_metrics_pair ON signal_performance_metrics(pair)",
        "CREATE INDEX IF NOT EXISTS idx_signal_performance_metrics_regime ON signal_performance_metrics(regime)",
        "CREATE INDEX IF NOT EXISTS idx_adaptive_weights_bot_id ON adaptive_signal_weights(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_adaptive_weights_pair_regime ON adaptive_signal_weights(pair, regime)"
    ]
    
    try:
        with engine.connect() as connection:
            # Create tables
            for table_name, create_sql in tables.items():
                logger.info(f"Creating table: {table_name}")
                connection.execute(text(create_sql))
                logger.info(f"✅ Table {table_name} created successfully")
            
            # Create indexes
            for index_sql in indexes:
                logger.info(f"Creating index...")
                connection.execute(text(index_sql))
            
            logger.info("✅ All indexes created successfully")
            
            # Commit the transaction
            connection.commit()
            
        logger.info("🎉 Phase 3A database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def verify_tables():
    """Verify that the tables were created correctly"""
    try:
        with engine.connect() as connection:
            # Check if tables exist
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('signal_predictions', 'signal_performance_metrics', 'adaptive_signal_weights')
                ORDER BY name
            """))
            
            tables = [row[0] for row in result]
            
            logger.info(f"📊 Found tables: {tables}")
            
            # Check table structures
            for table in tables:
                result = connection.execute(text(f"PRAGMA table_info({table})"))
                columns = [f"{row[1]}({row[2]})" for row in result]
                logger.info(f"   {table}: {len(columns)} columns")
            
            return len(tables) == 3
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Phase 3A Database Migration")
    
    # Create tables
    if create_signal_performance_tables():
        # Verify creation
        if verify_tables():
            logger.info("✅ Phase 3A Migration: SUCCESSFUL")
            sys.exit(0)
        else:
            logger.error("❌ Phase 3A Migration: VERIFICATION FAILED")
            sys.exit(1)
    else:
        logger.error("❌ Phase 3A Migration: CREATION FAILED")
        sys.exit(1)