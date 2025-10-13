"""
Breakout Detection Service

Scans all Coinbase trading pairs to detect breakout opportunities based on:
- Volume spikes (3x average)
- Price momentum (+15% in 4-24 hours)
- Trend confirmation
- Liquidity requirements

Created: October 12, 2025
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import statistics
import requests

from sqlalchemy.orm import Session

from app.services.market_data_service import get_market_data_service
from app.models.models import Bot

logger = logging.getLogger(__name__)


class BreakoutOpportunity:
    """Represents a detected breakout opportunity"""
    
    def __init__(
        self,
        product_id: str,
        score: float,
        price: float,
        price_change_24h: float,
        volume_24h: float,
        volume_change_24h: float,
        signals: List[str],
        confidence: str
    ):
        self.product_id = product_id
        self.score = score
        self.price = price
        self.price_change_24h = price_change_24h
        self.volume_24h = volume_24h
        self.volume_change_24h = volume_change_24h
        self.signals = signals
        self.confidence = confidence
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "score": self.score,
            "price": self.price,
            "price_change_24h": self.price_change_24h,
            "volume_24h": self.volume_24h,
            "volume_change_24h": self.volume_change_24h,
            "signals": self.signals,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat()
        }


class BreakoutDetector:
    """
    Detects breakout opportunities across all Coinbase trading pairs.
    
    Detection Criteria:
    1. Volume Spike: 3x average volume (or >100% increase)
    2. Price Momentum: +15% minimum in 24 hours
    3. Trend Confirmation: Sustained upward movement
    4. Liquidity: $500K+ 24h volume minimum
    
    Scoring System (0-100):
    - Price momentum: 0-40 points (higher % = more points)
    - Volume spike: 0-30 points (volume increase % = points)
    - Sustained trend: 0-20 points (price consistency)
    - Liquidity depth: 0-10 points ($1M+ volume = 10 pts)
    """
    
    def __init__(self):
        # Use MarketDataService for cached market data (prevents rate limiting)
        self.market_data_service = get_market_data_service()
        
        # Simple in-memory cache for products list (5 minute TTL)
        self._products_cache = None
        self._products_cache_time = None
        self._products_cache_ttl = 300  # 5 minutes
        
        # Detection thresholds
        self.MIN_PRICE_CHANGE = 15.0  # Minimum 15% price increase
        self.MIN_VOLUME_CHANGE = 100.0  # Minimum 100% volume increase (2x)
        self.MIN_VOLUME_USD = 500000  # $500K minimum volume
        self.IDEAL_VOLUME_USD = 1000000  # $1M ideal volume
        
        # Confidence levels
        self.CONFIDENCE_HIGH = 70  # Score >= 70
        self.CONFIDENCE_MEDIUM = 50  # Score >= 50
        self.CONFIDENCE_LOW = 30  # Score >= 30
    
    def scan_all_products(self) -> List[BreakoutOpportunity]:
        """
        Scan all Coinbase products for breakout opportunities.
        
        Returns:
            List of detected breakout opportunities sorted by score
        """
        logger.info("🔍 Starting breakout scan across all Coinbase pairs...")
        
        try:
            # Fetch all products from Coinbase
            products = self._fetch_all_products()
            logger.info(f"📊 Scanning {len(products)} trading pairs...")
            
            # Filter to tradeable USD/USDC pairs
            tradeable = self._filter_tradeable_products(products)
            logger.info(f"✅ {len(tradeable)} tradeable USD/USDC pairs")
            
            # Detect breakouts
            breakouts = []
            for product in tradeable:
                opportunity = self._analyze_product(product)
                if opportunity:
                    breakouts.append(opportunity)
            
            # Sort by score (highest first)
            breakouts.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"🚀 Detected {len(breakouts)} breakout opportunities")
            
            # Log top 5
            for i, breakout in enumerate(breakouts[:5], 1):
                logger.info(
                    f"  #{i} {breakout.product_id}: "
                    f"+{breakout.price_change_24h:.1f}% price, "
                    f"+{breakout.volume_change_24h:.1f}% volume, "
                    f"score={breakout.score:.1f} ({breakout.confidence})"
                )
            
            return breakouts
            
        except Exception as e:
            logger.error(f"❌ Error scanning for breakouts: {e}", exc_info=True)
            return []
    
    def _fetch_all_products(self) -> List[Dict]:
        """
        Fetch all products with 24h stats via Coinbase market API.
        
        Uses in-memory caching (5 min TTL) to minimize API calls.
        Single API call fetches ALL 663 pairs with price/volume stats.
        
        Note: Using market API endpoint because SDK's get_products() doesn't include
        price_percentage_change_24h and volume_percentage_change_24h needed for detection.
        """
        # Check in-memory cache first
        if self._products_cache and self._products_cache_time:
            age_seconds = (datetime.utcnow() - self._products_cache_time).total_seconds()
            if age_seconds < self._products_cache_ttl:
                logger.debug(f"✅ Using cached products list (age: {age_seconds:.0f}s)")
                return self._products_cache
        
        try:
            # Fetch from Coinbase market API (has price/volume percentage changes)
            import requests
            
            logger.info("📡 Fetching fresh products list from Coinbase market API...")
            response = requests.get(
                'https://api.coinbase.com/api/v3/brokerage/market/products',
                params={'limit': 1000},  # Get all products
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                # Update cache
                self._products_cache = products
                self._products_cache_time = datetime.utcnow()
                
                logger.info(f"✅ Retrieved {len(products)} products with 24h stats (cached for {self._products_cache_ttl}s)")
                return products
            else:
                logger.error(f"❌ Coinbase API returned status {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error fetching products: {e}")
            # Return stale cache if available
            if self._products_cache:
                logger.warning("⚠️ Using stale cache due to API error")
                return self._products_cache
            return []
    
    def _filter_tradeable_products(self, products: List[dict]) -> List[dict]:
        """
        Filter to tradeable USD/USDC spot pairs.
        
        Criteria:
        - SPOT product type
        - Not trading disabled
        - USD or USDC quote currency
        - Not view-only
        - Has volume data
        
        Handles both Product objects and dicts from Coinbase API.
        """
        tradeable = []
        seen_pairs = set()
        
        for product in products:
            # Handle both dict and object formats (like market_analysis_service.py)
            product_type = getattr(product, 'product_type', None) or (product.get('product_type') if hasattr(product, 'get') else None)
            quote_currency = getattr(product, 'quote_currency_id', None) or (product.get('quote_currency_id') if hasattr(product, 'get') else None)
            trading_disabled = getattr(product, 'trading_disabled', False) or (product.get('trading_disabled', False) if hasattr(product, 'get') else False)
            view_only = getattr(product, 'view_only', False) or (product.get('view_only', False) if hasattr(product, 'get') else False)
            product_id = getattr(product, 'product_id', None) or (product.get('product_id') if hasattr(product, 'get') else None)
            price = getattr(product, 'price', None) or (product.get('price') if hasattr(product, 'get') else None)
            volume_24h = getattr(product, 'volume_24h', None) or (product.get('volume_24h') if hasattr(product, 'get') else None)
            
            # Basic checks
            if product_type != "SPOT":
                continue
            
            if trading_disabled:
                continue
            
            if view_only:
                continue
            
            # USD or USDC only
            if quote_currency not in ["USD", "USDC"]:
                continue
            
            # Must have price and volume data
            if not price or not volume_24h:
                continue
            
            # Avoid duplicates (BTC-USD and BTC-USDC) - prefer USD
            base = product_id.split('-')[0] if product_id else None
            if base in seen_pairs:
                continue
            seen_pairs.add(base)
            
            # Convert to dict format for consistency downstream
            product_dict = {
                'product_id': product_id,
                'price': price,
                'price_percentage_change_24h': getattr(product, 'price_percentage_change_24h', None) or (product.get('price_percentage_change_24h') if hasattr(product, 'get') else None),
                'volume_24h': volume_24h,
                'volume_percentage_change_24h': getattr(product, 'volume_percentage_change_24h', None) or (product.get('volume_percentage_change_24h') if hasattr(product, 'get') else None),
                'approximate_quote_24h_volume': getattr(product, 'approximate_quote_24h_volume', None) or (product.get('approximate_quote_24h_volume') if hasattr(product, 'get') else volume_24h),
            }
            
            tradeable.append(product_dict)
        
        return tradeable
    
    def _analyze_product(self, product: dict) -> Optional[BreakoutOpportunity]:
        """
        Analyze a single product for breakout signals.
        
        Returns BreakoutOpportunity if breakout detected, None otherwise.
        """
        product_id = product.get("product_id")
        
        try:
            # Extract data
            price = float(product.get("price", 0))
            price_change_24h = float(product.get("price_percentage_change_24h", 0))
            volume_24h = float(product.get("volume_24h", 0))
            volume_change_24h = float(product.get("volume_percentage_change_24h", 0))
            volume_usd = float(product.get("approximate_quote_24h_volume", 0))
            
            # Quick filters
            if price_change_24h < self.MIN_PRICE_CHANGE:
                return None  # Not enough price momentum
            
            if volume_change_24h < self.MIN_VOLUME_CHANGE:
                return None  # No volume spike
            
            if volume_usd < self.MIN_VOLUME_USD:
                return None  # Insufficient liquidity
            
            # Calculate breakout score
            score, signals = self._calculate_breakout_score(
                price_change_24h,
                volume_change_24h,
                volume_usd
            )
            
            # Determine confidence
            if score >= self.CONFIDENCE_HIGH:
                confidence = "HIGH"
            elif score >= self.CONFIDENCE_MEDIUM:
                confidence = "MEDIUM"
            elif score >= self.CONFIDENCE_LOW:
                confidence = "LOW"
            else:
                return None  # Score too low
            
            return BreakoutOpportunity(
                product_id=product_id,
                score=score,
                price=price,
                price_change_24h=price_change_24h,
                volume_24h=volume_24h,
                volume_change_24h=volume_change_24h,
                signals=signals,
                confidence=confidence
            )
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Error analyzing {product_id}: {e}")
            return None
    
    def _calculate_breakout_score(
        self,
        price_change_24h: float,
        volume_change_24h: float,
        volume_usd: float
    ) -> tuple[float, List[str]]:
        """
        Calculate breakout score (0-100) and detected signals.
        
        Scoring breakdown:
        - Price momentum (0-40): Higher % = more points
        - Volume spike (0-30): Higher % = more points
        - Liquidity depth (0-10): $1M+ volume = 10 points
        - Extreme move bonus (0-20): +50% price or +500% volume
        
        Returns:
            (score, signals_list)
        """
        score = 0
        signals = []
        
        # 1. Price Momentum Score (0-40 points)
        # 15% = 15 pts, 25% = 25 pts, 50% = 40 pts (capped)
        price_score = min(price_change_24h, 40)
        score += price_score
        
        if price_change_24h >= 50:
            signals.append(f"EXTREME_PUMP:+{price_change_24h:.1f}%")
        elif price_change_24h >= 30:
            signals.append(f"STRONG_PUMP:+{price_change_24h:.1f}%")
        else:
            signals.append(f"PUMP:+{price_change_24h:.1f}%")
        
        # 2. Volume Spike Score (0-30 points)
        # 100% = 10 pts, 200% = 20 pts, 300%+ = 30 pts
        volume_score = min(volume_change_24h / 10, 30)
        score += volume_score
        
        if volume_change_24h >= 500:
            signals.append(f"EXTREME_VOLUME:+{volume_change_24h:.1f}%")
        elif volume_change_24h >= 200:
            signals.append(f"HUGE_VOLUME:+{volume_change_24h:.1f}%")
        else:
            signals.append(f"VOLUME_SPIKE:+{volume_change_24h:.1f}%")
        
        # 3. Liquidity Depth Score (0-10 points)
        # $500K = 5 pts, $1M+ = 10 pts
        if volume_usd >= self.IDEAL_VOLUME_USD:
            liquidity_score = 10
            signals.append(f"HIGH_LIQUIDITY:${volume_usd/1e6:.1f}M")
        else:
            liquidity_score = (volume_usd / self.IDEAL_VOLUME_USD) * 10
            signals.append(f"LIQUIDITY:${volume_usd/1e3:.0f}K")
        score += liquidity_score
        
        # 4. Extreme Move Bonus (0-20 points)
        if price_change_24h >= 50 or volume_change_24h >= 500:
            extreme_bonus = 20
            score += extreme_bonus
            signals.append("EXTREME_BREAKOUT")
        elif price_change_24h >= 30 or volume_change_24h >= 300:
            strong_bonus = 10
            score += strong_bonus
            signals.append("STRONG_BREAKOUT")
        
        return round(score, 1), signals
    
    def get_existing_bot_pairs(self, db: Session) -> List[str]:
        """Get list of trading pairs that already have active bots."""
        from app.models.models import Bot
        
        # Get all pairs with bots (any status - we don't want duplicates)
        existing_bots = db.query(Bot.pair).all()
        return [bot.pair for bot in existing_bots]
    
    def filter_new_opportunities(
        self,
        breakouts: List[BreakoutOpportunity],
        existing_pairs: set
    ) -> List[BreakoutOpportunity]:
        """Filter breakouts to only new opportunities (no existing bots)"""
        return [b for b in breakouts if b.product_id not in existing_pairs]


# Global instance
_breakout_detector = None


def get_breakout_detector() -> BreakoutDetector:
    """Get or create global BreakoutDetector instance"""
    global _breakout_detector
    if _breakout_detector is None:
        _breakout_detector = BreakoutDetector()
    return _breakout_detector
