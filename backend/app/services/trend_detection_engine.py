"""
Trend Detection Engine - Phase 1A Implementation
Market Regime Intelligence Framework

Provides multi-timeframe trend analysis for regime-adaptive trading bots.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from collections import OrderedDict
import threading
from .coinbase_service import coinbase_service

logger = logging.getLogger(__name__)


class TrendDetectionEngine:
    """
    Multi-timeframe trend analysis engine for regime detection.
    
    Features:
    - Multi-timeframe momentum analysis (5min, 1hour, daily)
    - Moving average trend confirmation  
    - Volume-confirmed trend validation
    - Regime classification with crypto-optimized thresholds
    - Intelligent caching (5-minute TTL)
    """
    
    # Regime classification thresholds (crypto-optimized)
    REGIME_THRESHOLDS = {
        "STRONG_TRENDING": 0.4,    # Very clear trend
        "TRENDING": 0.15,          # Moderate trend  
        "RANGING": -0.15,          # Sideways movement
        "CHOPPY": -0.4             # Volatile/unclear
    }
    
    def __init__(self, cache_ttl_seconds: int = 300):  # 5-minute cache
        """
        Initialize trend detection engine.
        
        Args:
            cache_ttl_seconds: Cache TTL for trend analysis (default 5 minutes)
        """
        self._cache = OrderedDict()
        self._cache_ttl = cache_ttl_seconds
        self._lock = threading.Lock()
        self._stats = {
            'requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'calculations': 0
        }
        
    def analyze_trend(self, product_id: str) -> Dict[str, Any]:
        """
        Analyze trend strength and regime for a trading pair.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            
        Returns:
            Dict containing:
            - trend_strength: float (-1.0 to +1.0, negative = downtrend, positive = uptrend)
            - confidence: float (0 to 1, higher = more reliable)
            - regime: str (STRONG_TRENDING, TRENDING, RANGING, CHOPPY)
            - timeframe_analysis: Dict with individual timeframe results
            - volume_confirmation: bool (whether volume confirms trend)
            - moving_average_alignment: str (BULLISH, BEARISH, NEUTRAL)
        """
        self._stats['requests'] += 1
        
        # Check cache first
        cache_key = f"trend_{product_id}"
        cached_result = self._get_cached_analysis(cache_key)
        if cached_result:
            self._stats['cache_hits'] += 1
            logger.debug(f"Cache HIT for trend analysis: {product_id}")
            return cached_result
            
        self._stats['cache_misses'] += 1
        logger.info(f"🔍 Calculating trend analysis for {product_id}")
        
        try:
            # Calculate fresh trend analysis
            result = self._calculate_trend_analysis(product_id)
            
            # Cache the result
            self._cache_analysis(cache_key, result)
            self._stats['calculations'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {product_id}: {e}")
            return self._get_default_trend_result(product_id, str(e))
    
    def _calculate_trend_analysis(self, product_id: str) -> Dict[str, Any]:
        """Calculate comprehensive trend analysis."""
        
        # 1. Multi-timeframe momentum analysis
        timeframe_analysis = self._analyze_multi_timeframe_momentum(product_id)
        
        # 2. Calculate composite trend strength
        trend_strength = self._calculate_composite_trend_strength(timeframe_analysis)
        
        # 3. Moving average confirmation
        ma_alignment = self._analyze_moving_average_alignment(product_id)
        
        # 4. Volume confirmation
        volume_confirmation = self._analyze_volume_confirmation(product_id, trend_strength)
        
        # 5. Calculate confidence based on alignment
        confidence = self._calculate_trend_confidence(
            timeframe_analysis, ma_alignment, volume_confirmation
        )
        
        # 6. Classify regime
        regime = self._classify_regime(trend_strength, confidence)
        
        result = {
            'product_id': product_id,
            'trend_strength': round(trend_strength, 4),
            'confidence': round(confidence, 4),
            'regime': regime,
            'timeframe_analysis': timeframe_analysis,
            'volume_confirmation': volume_confirmation,
            'moving_average_alignment': ma_alignment,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'cache_ttl_seconds': self._cache_ttl
        }
        
        logger.info(f"✅ Trend analysis complete for {product_id}: "
                   f"strength={trend_strength:.3f}, regime={regime}, confidence={confidence:.3f}")
        
        return result
    
    def _analyze_multi_timeframe_momentum(self, product_id: str) -> Dict[str, Any]:
        """Analyze momentum across multiple timeframes."""
        
        timeframes = {
            'short_term': {'granularity': 300, 'periods': 12, 'name': '5min'},    # 1 hour of 5min candles
            'medium_term': {'granularity': 3600, 'periods': 24, 'name': '1hour'}, # 1 day of hourly candles  
            'long_term': {'granularity': 86400, 'periods': 7, 'name': 'daily'}    # 1 week of daily candles
        }
        
        analysis = {}
        
        for timeframe, config in timeframes.items():
            try:
                # Get market data for this timeframe
                data = coinbase_service.get_historical_data(
                    product_id=product_id,
                    granularity=config['granularity'],
                    limit=config['periods']
                )
                
                if data.empty or len(data) < 3:
                    logger.warning(f"Insufficient data for {product_id} {timeframe}")
                    analysis[timeframe] = {
                        'momentum': 0.0,
                        'data_points': 0,
                        'error': 'insufficient_data'
                    }
                    continue
                
                # Calculate momentum for this timeframe
                momentum = self._calculate_momentum(data)
                
                analysis[timeframe] = {
                    'momentum': round(momentum, 4),
                    'data_points': len(data),
                    'timeframe_name': config['name'],
                    'price_change_pct': round(self._calculate_price_change_pct(data), 4),
                    'volatility': round(data['close'].pct_change().std() * 100, 4) if len(data) > 1 else 0.0
                }
                
            except Exception as e:
                logger.error(f"Error analyzing {timeframe} for {product_id}: {e}")
                analysis[timeframe] = {
                    'momentum': 0.0,
                    'data_points': 0,
                    'error': str(e)
                }
        
        return analysis
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """
        Calculate momentum score for given price data.
        
        Returns:
            float: Momentum score (-1.0 to +1.0)
        """
        if len(data) < 3:
            return 0.0
            
        try:
            # Calculate rate of change (ROC) momentum
            close_prices = data['close']
            
            # Simple momentum: (current - start) / start
            start_price = close_prices.iloc[0] 
            current_price = close_prices.iloc[-1]
            
            if start_price <= 0:
                return 0.0
                
            momentum = (current_price - start_price) / start_price
            
            # Normalize to -1 to +1 range using tanh for smooth bounds
            normalized_momentum = np.tanh(momentum * 10)  # Scale factor for crypto volatility
            
            return float(normalized_momentum)
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _calculate_price_change_pct(self, data: pd.DataFrame) -> float:
        """Calculate percentage price change from start to end of period."""
        if len(data) < 2:
            return 0.0
            
        try:
            start_price = data['close'].iloc[0]
            end_price = data['close'].iloc[-1]
            
            if start_price <= 0:
                return 0.0
                
            return ((end_price - start_price) / start_price) * 100
            
        except Exception:
            return 0.0
    
    def _calculate_composite_trend_strength(self, timeframe_analysis: Dict[str, Any]) -> float:
        """Calculate weighted composite trend strength from multiple timeframes."""
        
        # Timeframe weights (based on crypto market characteristics)
        weights = {
            'short_term': 0.3,   # 5min data - immediate price action
            'medium_term': 0.4,  # 1hour data - most important for trading decisions
            'long_term': 0.3     # Daily data - overall trend context
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for timeframe, weight in weights.items():
            if timeframe in timeframe_analysis:
                momentum = timeframe_analysis[timeframe].get('momentum', 0.0)
                
                # Only include if we have valid data
                if 'error' not in timeframe_analysis[timeframe]:
                    weighted_sum += momentum * weight
                    total_weight += weight
        
        if total_weight == 0:
            return 0.0
            
        composite_strength = weighted_sum / total_weight
        
        # Ensure result is in expected range
        return max(-1.0, min(1.0, composite_strength))
    
    def _analyze_moving_average_alignment(self, product_id: str) -> str:
        """Analyze moving average alignment for trend confirmation."""
        
        try:
            # Get hourly data for MA analysis
            data = coinbase_service.get_historical_data(
                product_id=product_id,
                granularity=3600,  # 1 hour
                limit=50           # Need enough data for 50-period MA
            )
            
            if data.empty or len(data) < 50:
                return "NEUTRAL"  # Not enough data
                
            # Calculate moving averages
            data = data.sort_index()  # Ensure chronological order
            data['MA5'] = data['close'].rolling(window=5).mean()
            data['MA20'] = data['close'].rolling(window=20).mean() 
            data['MA50'] = data['close'].rolling(window=50).mean()
            
            # Get latest values
            latest = data.iloc[-1]
            current_price = latest['close']
            ma5 = latest['MA5']
            ma20 = latest['MA20'] 
            ma50 = latest['MA50']
            
            # Check for NaN values
            if pd.isna(ma5) or pd.isna(ma20) or pd.isna(ma50):
                return "NEUTRAL"
            
            # Analyze alignment
            if (current_price > ma5 > ma20 > ma50):
                return "BULLISH"  # Perfect bullish alignment
            elif (current_price < ma5 < ma20 < ma50):
                return "BEARISH"  # Perfect bearish alignment
            elif current_price > ma20 and ma5 > ma20:
                return "BULLISH"  # Generally bullish
            elif current_price < ma20 and ma5 < ma20:
                return "BEARISH"  # Generally bearish
            else:
                return "NEUTRAL"  # Mixed signals
                
        except Exception as e:
            logger.error(f"Error analyzing MA alignment for {product_id}: {e}")
            return "NEUTRAL"
    
    def _analyze_volume_confirmation(self, product_id: str, trend_strength: float) -> bool:
        """Analyze if volume confirms the trend."""
        
        try:
            # Get recent hourly data with volume
            data = coinbase_service.get_historical_data(
                product_id=product_id,
                granularity=3600,  # 1 hour
                limit=24           # 24 hours
            )
            
            if data.empty or len(data) < 12:
                return False  # Not enough data
                
            # Calculate volume trend
            recent_volume = data['volume'].tail(6).mean()  # Last 6 hours
            older_volume = data['volume'].head(6).mean()   # First 6 hours
            
            if older_volume <= 0:
                return False
                
            volume_change = (recent_volume - older_volume) / older_volume
            
            # Volume should increase with strong trends
            if abs(trend_strength) > 0.3:  # Strong trend
                return volume_change > 0.1  # Volume increased by >10%
            elif abs(trend_strength) > 0.1:  # Moderate trend  
                return volume_change > -0.2  # Volume didn't decrease significantly
            else:
                return True  # Weak trends, volume less important
                
        except Exception as e:
            logger.error(f"Error analyzing volume confirmation for {product_id}: {e}")
            return False
    
    def _calculate_trend_confidence(self, timeframe_analysis: Dict[str, Any], 
                                  ma_alignment: str, volume_confirmation: bool) -> float:
        """Calculate confidence score for trend analysis."""
        
        confidence = 0.5  # Base confidence
        
        # 1. Timeframe alignment (up to +0.3)
        momentums = []
        valid_timeframes = 0
        
        for timeframe in ['short_term', 'medium_term', 'long_term']:
            if timeframe in timeframe_analysis and 'error' not in timeframe_analysis[timeframe]:
                momentum = timeframe_analysis[timeframe].get('momentum', 0.0)
                momentums.append(momentum)
                valid_timeframes += 1
        
        if valid_timeframes >= 2:
            # Check if timeframes agree on direction
            positive_count = sum(1 for m in momentums if m > 0.1)
            negative_count = sum(1 for m in momentums if m < -0.1)
            
            if positive_count >= 2 or negative_count >= 2:
                confidence += 0.3  # Timeframes agree
            elif positive_count + negative_count < valid_timeframes:
                confidence += 0.1  # Some agreement
        
        # 2. Moving average confirmation (up to +0.15)
        if ma_alignment in ["BULLISH", "BEARISH"]:
            confidence += 0.15
        elif ma_alignment == "NEUTRAL":
            confidence += 0.05
        
        # 3. Volume confirmation (up to +0.05)
        if volume_confirmation:
            confidence += 0.05
        
        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))
    
    def _classify_regime(self, trend_strength: float, confidence: float) -> str:
        """Classify market regime based on trend strength and confidence."""
        
        # Apply confidence weighting to trend strength
        weighted_strength = abs(trend_strength) * confidence
        
        if weighted_strength >= self.REGIME_THRESHOLDS["STRONG_TRENDING"]:
            return "STRONG_TRENDING"
        elif weighted_strength >= self.REGIME_THRESHOLDS["TRENDING"]:
            return "TRENDING"  
        elif weighted_strength >= abs(self.REGIME_THRESHOLDS["RANGING"]):
            return "RANGING"
        else:
            return "CHOPPY"
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached trend analysis if still valid."""
        with self._lock:
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                age_seconds = (datetime.utcnow() - timestamp).total_seconds()
                
                if age_seconds < self._cache_ttl:
                    # Move to end for LRU
                    self._cache.move_to_end(cache_key)
                    return cached_data
                else:
                    # Expired, remove from cache
                    del self._cache[cache_key]
        
        return None
    
    def _cache_analysis(self, cache_key: str, result: Dict[str, Any]):
        """Cache trend analysis result."""
        with self._lock:
            self._cache[cache_key] = (result, datetime.utcnow())
            
            # LRU eviction (keep cache size reasonable)
            max_cache_size = 50  # Cache up to 50 products
            while len(self._cache) > max_cache_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
    
    def _get_default_trend_result(self, product_id: str, error_msg: str) -> Dict[str, Any]:
        """Return default result when analysis fails."""
        return {
            'product_id': product_id,
            'trend_strength': 0.0,
            'confidence': 0.0,
            'regime': 'NEUTRAL',
            'timeframe_analysis': {},
            'volume_confirmation': False,
            'moving_average_alignment': 'NEUTRAL',
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'error': error_msg
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trend detection engine statistics."""
        with self._lock:
            cache_hit_rate = (self._stats['cache_hits'] / max(self._stats['requests'], 1)) * 100
            
            return {
                'requests': self._stats['requests'],
                'cache_hits': self._stats['cache_hits'],
                'cache_misses': self._stats['cache_misses'],
                'cache_hit_rate': round(cache_hit_rate, 1),
                'calculations': self._stats['calculations'],
                'cached_products': len(self._cache),
                'cache_ttl_seconds': self._cache_ttl
            }
    
    def clear_cache(self) -> int:
        """Clear trend detection cache."""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            return cleared_count


# Global trend detection engine instance
_global_trend_engine = TrendDetectionEngine(cache_ttl_seconds=300)  # 5-minute cache


def get_trend_engine() -> TrendDetectionEngine:
    """Get the global trend detection engine instance."""
    return _global_trend_engine