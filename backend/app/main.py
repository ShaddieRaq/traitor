from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import bots, market, trades, bot_evaluation, websocket, bot_temperatures, coinbase_sync, trading_diagnosis, validation, market_analysis, raw_trades, positions, system_errors, websocket_prices, health_monitoring, market_data_cache, notifications, new_pairs, trends, intelligence_analytics, cache_monitoring, market_data, market_selection
from .core.config import settings
from .core.database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Bot-based cryptocurrency trading system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Using sync_api_coordinator for production (Phase 6.4)
# Centralized coordination handled by sync_coordinated_coinbase_service
logger.info("🚀 Phase 6.4: Using sync API coordination for production deployment")

# Include API routers
# API Routes
app.include_router(bots.router, prefix="/api/v1/bots", tags=["bots"])
app.include_router(bot_temperatures.router, prefix="/api/v1/bot-temperatures", tags=["bot-temperatures"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(raw_trades.router, prefix="/api/v1/raw-trades", tags=["raw-trades"])
app.include_router(bot_evaluation.router, prefix="/api/v1/bot-evaluation", tags=["bot-evaluation"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["websocket"])
app.include_router(websocket_prices.router, prefix="/api/v1/websocket-prices", tags=["websocket-prices"])
app.include_router(coinbase_sync.router, prefix="/api/v1/coinbase-sync", tags=["coinbase-sync"])
app.include_router(trading_diagnosis.router, prefix="/api/v1/diagnosis", tags=["diagnosis"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(market_analysis.router, prefix="/api/v1/market-analysis", tags=["market-analysis"])
app.include_router(new_pairs.router, prefix="/api/v1/new-pairs", tags=["new-pairs"])

# Phase 1: Market Regime Intelligence - Trend Detection API
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])

app.include_router(positions.router, prefix="/api/v1/positions", tags=["positions"])

# System Errors API
app.include_router(system_errors.router, prefix="/api/v1/system-errors", tags=["system-errors"])

# Market Data Cache API
app.include_router(market_data_cache.router, prefix="/api/v1/cache", tags=["market-data-cache"])

# Phase 7: Market Data Service API
app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["market-data"])

# Phase 6.2: Centralized Cache Monitoring API
app.include_router(cache_monitoring.router, prefix="/api/v1/cache-monitoring", tags=["cache-monitoring"])

# Health Monitoring API  
app.include_router(health_monitoring.router, prefix="/api/v1/health", tags=["health-monitoring"])

# Notifications API
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])

# New Pairs Detection API
app.include_router(new_pairs.router, prefix="/api/v1/new-pairs", tags=["new-pairs"])

# Position Reconciliation API
from .api import position_reconciliation
app.include_router(position_reconciliation.router, prefix="/api/v1/position-reconciliation", tags=["position-reconciliation"])

# Market Selection Learning API (Phase 8.2)
app.include_router(market_selection.router, tags=["market-selection"])

# Phase 3A: Signal Performance Analytics API
from .api import signal_performance
app.include_router(signal_performance.router, prefix="/api/v1/signal-performance", tags=["signal-performance"])

# Phase 5D: Intelligence Framework Analytics API
app.include_router(intelligence_analytics.router, prefix="/api/v1/intelligence", tags=["intelligence-analytics"])


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Bot-based Trading API", "version": "1.0.0", "docs": "/api/docs"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
