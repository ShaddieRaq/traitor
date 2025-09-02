from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import bots, market, trades
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
app.include_router(bots.router, prefix=f"{settings.api_v1_prefix}/bots", tags=["bots"])
app.include_router(market.router, prefix=f"{settings.api_v1_prefix}/market", tags=["market"])
app.include_router(trades.router, prefix=f"{settings.api_v1_prefix}/trades", tags=["trades"])


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
