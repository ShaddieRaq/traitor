"""
Market Analysis Service for evaluating potential trading pairs.
Analyzes volume, volatility, momentum, and risk factors to recommend new bots.
"""

from typing import Dict, List, Any, Optional
import logging
from ..services.coinbase_service import CoinbaseService

logger = logging.getLogger(__name__)


class MarketAnalysisService:
    """Service for analyzing market conditions and recommending trading pairs."""
    
    def __init__(self):
        self.coinbase_service = CoinbaseService()
    
    def analyze_potential_pairs(self, 
                              exclude_pairs: Optional[List[str]] = None,
                              limit: int = 100,
                              include_gems: bool = True) -> Dict[str, Any]:
        """
        Analyze potential trading pairs and rank them by suitability.
        
        Args:
            exclude_pairs: List of pairs to exclude (existing bots)
            limit: Number of top candidates to analyze
            include_gems: If True, includes a gem-hunting pass for high-scoring low-volume pairs
            
        Returns:
            Dict containing analysis results and recommendations
        """
        try:
            # Get all available products
            products = self.coinbase_service.get_products()
            if not products:
                return {"error": "Unable to fetch products from Coinbase"}
            
            # Filter USD pairs that are tradeable
            usd_pairs = []
            for product in products:
                # Handle both dict and object formats
                quote_currency = getattr(product, 'quote_currency_id', None) or product.get('quote_currency_id', None) if hasattr(product, 'get') else getattr(product, 'quote_currency_id', None)
                status = getattr(product, 'status', None) or product.get('status', None) if hasattr(product, 'get') else getattr(product, 'status', None)
                trading_disabled = getattr(product, 'trading_disabled', False) or product.get('trading_disabled', False) if hasattr(product, 'get') else getattr(product, 'trading_disabled', False)
                is_disabled = getattr(product, 'is_disabled', False) or product.get('is_disabled', False) if hasattr(product, 'get') else getattr(product, 'is_disabled', False)
                product_id = getattr(product, 'product_id', None) or product.get('product_id', None) if hasattr(product, 'get') else getattr(product, 'product_id', None)
                
                if (quote_currency == 'USD' and 
                    status == 'online' and 
                    not trading_disabled and
                    not is_disabled):
                    
                    # Skip excluded pairs (existing bots)
                    if exclude_pairs and product_id in exclude_pairs:
                        continue
                    
                    usd_pairs.append(product)
            
            logger.info(f"STEP 1: Found {len(usd_pairs)} tradeable USD pairs (excluding {len(exclude_pairs or [])} existing bots)")
            
            if include_gems and limit < len(usd_pairs):
                # Hybrid approach: Volume leaders + Gem hunting
                logger.info(f"STEP 2A: Using hybrid approach - analyzing top volume + potential gems")
                
                # Take top volume leaders (75% of limit)
                volume_limit = int(limit * 0.75)
                usd_pairs.sort(key=self._get_volume_safe, reverse=True)
                volume_leaders = usd_pairs[:volume_limit]
                logger.info(f"STEP 2B: Selected top {len(volume_leaders)} pairs by volume")
                
                # Quick score remaining pairs to find gems (25% of limit)
                gem_limit = limit - volume_limit
                remaining_pairs = usd_pairs[volume_limit:]
                
                # Quick scoring of remaining pairs
                gem_candidates = []
                for product in remaining_pairs:
                    quick_analysis = self._analyze_single_pair(product)
                    if quick_analysis and quick_analysis['total_score'] >= 15:  # High score threshold
                        gem_candidates.append((product, quick_analysis['total_score']))
                
                # Sort gems by score and take top ones
                gem_candidates.sort(key=lambda x: x[1], reverse=True)
                gem_pairs = [pair[0] for pair in gem_candidates[:gem_limit]]
                
                logger.info(f"STEP 2C: Found {len(gem_pairs)} potential gems (score ≥15) from {len(remaining_pairs)} lower-volume pairs")
                
                # Combine volume leaders + gems
                candidates = volume_leaders + gem_pairs
                
            else:
                # Original volume-only approach
                usd_pairs.sort(key=self._get_volume_safe, reverse=True)
                logger.info(f"STEP 2: Sorted {len(usd_pairs)} pairs by volume (highest first)")
                candidates = usd_pairs[:limit]
            
            logger.info(f"STEP 3: Selected {len(candidates)} pairs for detailed analysis")
            
            # Debug logging for pool size
            logger.info(f"Total USD pairs available: {len(usd_pairs)}, Analyzing top: {len(candidates)}")
            
            # Analyze each candidate
            analysis_results = []
            for i, product in enumerate(candidates, 1):
                analysis = self._analyze_single_pair(product)
                if analysis:
                    analysis_results.append(analysis)
                    if i <= 5:  # Log first 5 for debugging
                        logger.info(f"  #{i}: {analysis['product_id']} - Volume: ${analysis['volume_24h_million']:.1f}M, Score: {analysis['total_score']:.1f}")
            
            logger.info(f"STEP 4: Completed analysis of {len(analysis_results)} pairs")
            
            # Sort by total score
            analysis_results.sort(key=lambda x: x['total_score'], reverse=True)
            if analysis_results:
                top_3 = analysis_results[:3]
                logger.info(f"STEP 5: Sorted by score - Top pair: {top_3[0]['product_id']} ({top_3[0]['total_score']:.1f})")
            
            # Generate summary and recommendations
            summary = self._generate_analysis_summary(analysis_results)
            
            return {
                "candidates": analysis_results,
                "summary": summary,
                "timestamp": "2025-09-10T23:30:00Z",  # Current timestamp
                "total_analyzed": len(analysis_results)
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {"error": f"Market analysis failed: {str(e)}"}
    
    def _get_volume_safe(self, product) -> float:
        """Safely get volume from product data."""
        try:
            # Handle both dict and object formats
            vol = getattr(product, 'approximate_quote_24h_volume', None) or product.get('approximate_quote_24h_volume', '0') if hasattr(product, 'get') else getattr(product, 'approximate_quote_24h_volume', '0')
            if vol is None or vol == '':
                return 0
            return float(vol)
        except (ValueError, TypeError):
            return 0
    
    def _analyze_single_pair(self, product) -> Optional[Dict[str, Any]]:
        """Analyze a single trading pair."""
        try:
            # Handle both dict and object formats
            product_id = getattr(product, 'product_id', None) or product.get('product_id', '') if hasattr(product, 'get') else getattr(product, 'product_id', '')
            price = float(getattr(product, 'price', 0) or product.get('price', 0) if hasattr(product, 'get') else getattr(product, 'price', 0))
            volume_24h = self._get_volume_safe(product)
            volume_24h_million = volume_24h / 1_000_000
            
            # Get percentage changes
            price_change_24h = float(getattr(product, 'price_percentage_change_24h', 0) or product.get('price_percentage_change_24h', 0) if hasattr(product, 'get') else getattr(product, 'price_percentage_change_24h', 0))
            volume_change_24h = float(getattr(product, 'volume_percentage_change_24h', 0) or product.get('volume_percentage_change_24h', 0) if hasattr(product, 'get') else getattr(product, 'volume_percentage_change_24h', 0))
            
            # Calculate scoring factors
            liquidity_score = min(volume_24h_million / 50, 10)  # Max 10 points
            volatility_score = min(abs(price_change_24h) * 2, 10)  # Max 10 points  
            momentum_score = min(max(volume_change_24h, 0) / 10, 5)  # Max 5 points
            
            # Position sizing analysis
            position_tokens = 25 / price if price > 0 else 0
            
            # Risk assessment
            if volume_24h_million > 200:
                risk_level = "LOW"
                risk_color = "green"
                risk_score = 5
            elif volume_24h_million > 50:
                risk_level = "MEDIUM" 
                risk_color = "yellow"
                risk_score = 3
            else:
                risk_level = "HIGH"
                risk_color = "red"
                risk_score = 1
            
            total_score = liquidity_score + volatility_score + momentum_score + risk_score
            
            # Determine recommendation level
            if total_score >= 20:
                recommendation = "HIGHLY_RECOMMENDED"
                recommendation_color = "green"
            elif total_score >= 12:
                recommendation = "GOOD_CANDIDATE"
                recommendation_color = "yellow"
            else:
                recommendation = "CONSIDER_LATER"
                recommendation_color = "gray"
            
            return {
                "product_id": product_id,
                "base_name": getattr(product, 'base_name', '') or product.get('base_name', '') if hasattr(product, 'get') else getattr(product, 'base_name', ''),
                "price": price,
                "volume_24h_million": volume_24h_million,
                "price_change_24h": price_change_24h,
                "volume_change_24h": volume_change_24h,
                "position_tokens": position_tokens,
                "liquidity_score": liquidity_score,
                "volatility_score": volatility_score,
                "momentum_score": momentum_score,
                "risk_score": risk_score,
                "total_score": total_score,
                "risk_level": risk_level,
                "risk_color": risk_color,
                "recommendation": recommendation,
                "recommendation_color": recommendation_color,
                "analysis": {
                    "liquidity_analysis": self._get_liquidity_analysis(volume_24h_million),
                    "volatility_analysis": self._get_volatility_analysis(price_change_24h),
                    "momentum_analysis": self._get_momentum_analysis(volume_change_24h),
                    "position_analysis": self._get_position_analysis(price, position_tokens)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {product.get('product_id', 'unknown')}: {e}")
            return None
    
    def _get_liquidity_analysis(self, volume_million: float) -> str:
        """Generate liquidity analysis text."""
        if volume_million > 200:
            return f"Excellent liquidity (${volume_million:.1f}M) ensures minimal slippage"
        elif volume_million > 50:
            return f"Good liquidity (${volume_million:.1f}M) suitable for automated trading"
        else:
            return f"Lower liquidity (${volume_million:.1f}M) may cause higher slippage"
    
    def _get_volatility_analysis(self, price_change: float) -> str:
        """Generate volatility analysis text."""
        abs_change = abs(price_change)
        if abs_change > 10:
            return f"High volatility ({price_change:+.1f}%) offers many trading opportunities"
        elif abs_change > 3:
            return f"Moderate volatility ({price_change:+.1f}%) provides good trading potential"
        else:
            return f"Low volatility ({price_change:+.1f}%) may limit trading opportunities"
    
    def _get_momentum_analysis(self, volume_change: float) -> str:
        """Generate momentum analysis text."""
        if volume_change > 50:
            return f"Strong momentum (+{volume_change:.1f}%) indicates growing interest"
        elif volume_change > 0:
            return f"Positive momentum (+{volume_change:.1f}%) shows increasing activity"
        else:
            return f"Declining momentum ({volume_change:+.1f}%) suggests less interest"
    
    def _get_position_analysis(self, price: float, tokens: float) -> str:
        """Generate position sizing analysis text."""
        if price > 1000:
            return f"High-value asset: {tokens:.3f} tokens per $25 trade"
        elif price > 10:
            return f"Mid-value asset: {tokens:.2f} tokens per $25 trade" 
        else:
            return f"Low-value asset: {tokens:.1f} tokens per $25 trade"
    
    def auto_create_bot_for_opportunity(self, product_id: str, db_session) -> Dict[str, Any]:
        """
        Automatically create a bot for a high-scoring market opportunity.
        
        Args:
            product_id: Trading pair to create bot for
            db_session: Database session for bot creation
            
        Returns:
            Dict with creation results
        """
        try:
            from ..models.models import Bot
            import json
            
            # First, analyze this specific pair to get its score
            products = self.coinbase_service.get_products()
            target_product = None
            
            for product in products:
                pid = getattr(product, 'product_id', None) or product.get('product_id', '') if hasattr(product, 'get') else getattr(product, 'product_id', '')
                if pid == product_id:
                    target_product = product
                    break
            
            if not target_product:
                return {"success": False, "error": f"Product {product_id} not found"}
            
            # Analyze the opportunity
            analysis = self._analyze_single_pair(target_product)
            if not analysis:
                return {"success": False, "error": f"Failed to analyze {product_id}"}
            
            # Only create bot if it meets criteria
            if analysis['total_score'] < 15:  # Minimum score threshold
                return {
                    "success": False, 
                    "error": f"Score too low: {analysis['total_score']:.1f} (minimum 15.0)",
                    "analysis": analysis
                }
            
            # Check if bot already exists
            existing_bot = db_session.query(Bot).filter(Bot.pair == product_id).first()
            if existing_bot:
                return {"success": False, "error": f"Bot already exists for {product_id}"}
            
            # Create standard signal configuration
            signal_config = {
                "RSI": {
                    "enabled": True,
                    "weight": 0.4,
                    "period": 14,
                    "buy_threshold": 35,
                    "sell_threshold": 65
                },
                "moving_average": {
                    "enabled": True,
                    "weight": 0.4,
                    "fast_period": 12,
                    "slow_period": 26
                },
                "macd": {
                    "enabled": True,
                    "weight": 0.2,
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                }
            }
            
            # Create the bot
            new_bot = Bot(
                name=f"Auto-{analysis['base_name']}-USD Bot",
                description=f"Auto-created bot for {product_id} (Score: {analysis['total_score']:.1f})",
                pair=product_id,
                status="STOPPED",  # Start stopped for safety
                position_size_usd=25.0,  # Conservative $25 per trade instead of $100
                max_positions=5,
                stop_loss_pct=5.0,
                take_profit_pct=10.0,
                confirmation_minutes=5,
                trade_step_pct=2.0,
                cooldown_minutes=15,
                signal_config=json.dumps(signal_config)
            )
            
            db_session.add(new_bot)
            db_session.commit()
            db_session.refresh(new_bot)
            
            logger.info(f"🤖 Auto-created bot {new_bot.id} for {product_id} (Score: {analysis['total_score']:.1f})")
            
            return {
                "success": True,
                "bot_id": new_bot.id,
                "bot_name": new_bot.name,
                "analysis": analysis,
                "message": f"Successfully created bot for {product_id}"
            }
            
        except Exception as e:
            logger.error(f"Error auto-creating bot for {product_id}: {e}")
            return {"success": False, "error": str(e)}

    def scan_and_auto_create_bots(self, db_session, max_new_bots: int = 2, min_score: float = 18.0) -> Dict[str, Any]:
        """
        Scan market for opportunities and auto-create bots for top candidates.
        
        Args:
            db_session: Database session
            max_new_bots: Maximum number of new bots to create
            min_score: Minimum score threshold for bot creation
            
        Returns:
            Dict with scan and creation results
        """
        try:
            from ..models.models import Bot
            
            # Get existing bot pairs to exclude
            existing_bots = db_session.query(Bot).all()
            exclude_pairs = [bot.pair for bot in existing_bots]
            
            # Perform market analysis
            analysis_results = self.analyze_potential_pairs(
                exclude_pairs=exclude_pairs,
                limit=20  # Analyze more candidates for auto-creation
            )
            
            if "error" in analysis_results:
                return {"success": False, "error": analysis_results["error"]}
            
            # Filter candidates that meet criteria
            candidates = analysis_results.get("candidates", [])
            qualified_candidates = [
                c for c in candidates 
                if c["total_score"] >= min_score and c["recommendation"] in ["HIGHLY_RECOMMENDED", "GOOD_CANDIDATE"]
            ]
            
            # Sort by score and take top candidates
            qualified_candidates.sort(key=lambda x: x["total_score"], reverse=True)
            top_candidates = qualified_candidates[:max_new_bots]
            
            created_bots = []
            for candidate in top_candidates:
                result = self.auto_create_bot_for_opportunity(candidate["product_id"], db_session)
                if result["success"]:
                    created_bots.append(result)
            
            return {
                "success": True,
                "total_candidates_analyzed": len(candidates),
                "qualified_candidates": len(qualified_candidates),
                "bots_created": len(created_bots),
                "new_bots": created_bots,
                "threshold_used": min_score
            }
            
        except Exception as e:
            logger.error(f"Error in scan and auto-create: {e}")
            return {"success": False, "error": str(e)}
        """Generate analysis summary and top recommendations."""
        if not results:
            return {"message": "No candidates found"}
        
        # Get top 3 recommendations
        top_3 = results[:3]
        
    def _generate_analysis_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate analysis summary and top recommendations."""
        if not results:
            return {"message": "No candidates found"}
        
        # Get top 3 recommendations
        top_3 = results[:3]
        
        # Count recommendation levels
        highly_recommended = len([r for r in results if r['recommendation'] == 'HIGHLY_RECOMMENDED'])
        good_candidates = len([r for r in results if r['recommendation'] == 'GOOD_CANDIDATE'])
        
        # Find best by category
        best_liquidity = max(results, key=lambda x: x['liquidity_score'])
        best_volatility = max(results, key=lambda x: x['volatility_score'])
        best_momentum = max(results, key=lambda x: x['momentum_score'])
        
        return {
            "top_recommendation": top_3[0] if top_3 else None,
            "runner_ups": top_3[1:3] if len(top_3) > 1 else [],
            "counts": {
                "highly_recommended": highly_recommended,
                "good_candidates": good_candidates,
                "total_analyzed": len(results)
            },
            "best_by_category": {
                "liquidity": {
                    "product_id": best_liquidity['product_id'],
                    "volume": best_liquidity['volume_24h_million']
                },
                "volatility": {
                    "product_id": best_volatility['product_id'],
                    "change": best_volatility['price_change_24h']
                },
                "momentum": {
                    "product_id": best_momentum['product_id'],
                    "growth": best_momentum['volume_change_24h']
                }
            }
        }
