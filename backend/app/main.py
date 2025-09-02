from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import signals, market, trades
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
    description="Signal-based cryptocurrency trading bot",
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

# Include API routers
app.include_router(signals.router, prefix=f"{settings.api_v1_prefix}/signals", tags=["signals"])
app.include_router(market.router, prefix=f"{settings.api_v1_prefix}/market", tags=["market"])
app.include_router(trades.router, prefix=f"{settings.api_v1_prefix}/trades", tags=["trades"])


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Trading Bot API", "version": "1.0.0", "docs": "/api/docs"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Trading Bot API starting up...")
    
    # Initialize default signals if none exist
    await initialize_default_signals()


async def initialize_default_signals():
    """Initialize default signals in the database."""
    from .core.database import SessionLocal
    from .models.models import Signal
    import json
    
    db = SessionLocal()
    try:
        # Check if signals already exist
        existing_signals = db.query(Signal).count()
        if existing_signals > 0:
            logger.info(f"Found {existing_signals} existing signals")
            return
        
        # Create default RSI signal
        rsi_signal = Signal(
            name="RSI",
            description="Relative Strength Index momentum oscillator",
            enabled=True,
            weight=1.0,
            parameters=json.dumps({
                "period": 14,
                "oversold": 30,
                "overbought": 70
            })
        )
        
        # Create default Moving Average signal
        ma_signal = Signal(
            name="MA_Crossover",
            description="Moving Average crossover signal",
            enabled=True,
            weight=1.0,
            parameters=json.dumps({
                "fast_period": 10,
                "slow_period": 20
            })
        )
        
        db.add(rsi_signal)
        db.add(ma_signal)
        db.commit()
        
        logger.info("Default signals created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing default signals: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
