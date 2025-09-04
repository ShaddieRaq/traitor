from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import bots, market, trades, bot_evaluation, websocket, bot_temperatures
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

# Include API routers
# API Routes
app.include_router(bots.router, prefix="/api/v1/bots", tags=["bots"])
app.include_router(bot_temperatures.router, prefix="/api/v1/bot-temperatures", tags=["bot-temperatures"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(bot_evaluation.router, prefix="/api/v1/bot-evaluation", tags=["bot-evaluation"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["websocket"])


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
