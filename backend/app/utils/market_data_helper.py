"""
Centralized market data cache utilities.
Replaces 12+ duplicate implementations across the codebase.

This module consolidates the market data caching pattern that was duplicated in:
- bot_temperatures.py (2 instances)
- websocket.py (4 instances)  
- bots.py (3 instances)
- bot_evaluator.py (1 instance)

Usage:
    from app.utils.market_data_helper import create_market_data_cache
    
    # Replace 15+ lines of duplicate code with single call
    market_data_cache = create_market_data_cache(unique_pairs)
"""

from typing import Dict, List, Optional
import pandas as pd
import logging
from ..services.market_data_service import get_market_data_service

logger = logging.getLogger(__name__)


def create_fallback_dataframe() -> pd.DataFrame:
    """
    Standard fallback data structure used throughout system.
    
    Provides consistent OHLCV data when market data fetch fails.
    This replaces the duplicate fallback DataFrame creation pattern
    found in 12+ files across the codebase.
    
    Returns:
        DataFrame with standard fallback OHLCV data
    """
    return pd.DataFrame({
        'close': [100.0],
        'high': [101.0],
        'low': [99.0], 
        'open': [100.5],
        'volume': [1000]
    })


def create_market_data_cache(pairs: List[str], 
                           granularity: int = 3600, 
                           limit: int = 100) -> Dict[str, pd.DataFrame]:
    """
    Create market data cache for multiple trading pairs.
    
    This function replaces the duplicated pattern found in:
    - backend/app/api/bot_temperatures.py (lines 26-42, 66-82)
    - backend/app/api/websocket.py (lines 298-315, 347-364, 389-406)  
    - backend/app/api/bots.py (lines 257-273, 388-420)
    - backend/app/services/bot_evaluator.py (lines 866-877)
    
    Args:
        pairs: List of trading pairs (e.g., ["BTC-USD", "ETH-USD"])
        granularity: Candlestick granularity in seconds (default: 3600 = 1 hour)
        limit: Number of candles to fetch (default: 100)
        
    Returns:
        Dict mapping pair -> DataFrame with OHLCV data
    """
    market_data_cache = {}
    market_service = get_market_data_service()
    
    for pair in pairs:
        try:
            # Use MarketDataService for Redis caching benefits
            market_data_cache[pair] = market_service.get_historical_data(
                pair, granularity=granularity, limit=limit
            )
            logger.debug(f"✅ Market data loaded for {pair} ({len(market_data_cache[pair])} candles)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to get market data for {pair}: {e}")
            # Use consistent fallback data
            market_data_cache[pair] = create_fallback_dataframe()
            
    return market_data_cache


def create_single_market_data(pair: str, 
                            granularity: int = 3600, 
                            limit: int = 100) -> pd.DataFrame:
    """
    Get market data for single trading pair with fallback.
    
    Provides consistent error handling and fallback behavior
    for single pair market data requests.
    
    Args:
        pair: Trading pair (e.g., "BTC-USD")
        granularity: Candlestick granularity in seconds
        limit: Number of candles to fetch
        
    Returns:
        DataFrame with OHLCV data or fallback data
    """
    try:
        market_service = get_market_data_service()
        data = market_service.get_historical_data(pair, granularity=granularity, limit=limit)
        
        if data.empty:
            logger.warning(f"⚠️ Empty data returned for {pair}, using fallback")
            return create_fallback_dataframe()
            
        logger.debug(f"✅ Market data loaded for {pair} ({len(data)} candles)")
        return data
    except Exception as e:
        logger.warning(f"⚠️ Failed to get market data for {pair}: {e}")
        return create_fallback_dataframe()


def create_market_data_cache_with_legacy_fallback(pairs: List[str], 
                                                 coinbase_service, 
                                                 granularity: int = 3600, 
                                                 limit: int = 100) -> Dict[str, pd.DataFrame]:
    """
    Create market data cache with fallback to legacy CoinbaseService.
    
    This is a transitional helper for files that still use the old
    coinbase_service.get_historical_data() pattern. Gradually migrate
    these to use create_market_data_cache() instead.
    
    Args:
        pairs: List of trading pairs
        coinbase_service: Legacy coinbase service instance  
        granularity: Candlestick granularity in seconds
        limit: Number of candles to fetch
        
    Returns:
        Dict mapping pair -> DataFrame with OHLCV data
    """
    market_data_cache = {}
    
    for pair in pairs:
        try:
            # Try MarketDataService first (preferred, cached)
            market_service = get_market_data_service()
            market_data_cache[pair] = market_service.get_historical_data(
                pair, granularity=granularity, limit=limit
            )
            logger.debug(f"✅ Market data loaded for {pair} via MarketDataService")
        except Exception as e:
            try:
                # Fallback to legacy CoinbaseService
                logger.warning(f"⚠️ MarketDataService failed for {pair}, trying legacy: {e}")
                market_data_cache[pair] = coinbase_service.get_historical_data(
                    pair, granularity=granularity, limit=limit
                )
                logger.debug(f"✅ Market data loaded for {pair} via legacy CoinbaseService")
            except Exception as e2:
                logger.warning(f"⚠️ All market data sources failed for {pair}: {e2}")
                # Use consistent fallback data
                market_data_cache[pair] = create_fallback_dataframe()
            
    return market_data_cache