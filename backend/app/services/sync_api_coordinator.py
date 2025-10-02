"""
Synchronous API Coordinator - Phase 6.4 Implementation
Rate-limited request coordination without async/sync deadlock issues.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque
import json

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Request priority levels for API call coordination."""
    CRITICAL = 1     # Trading operations
    HIGH = 2         # Bot evaluations  
    MEDIUM = 3       # Market data
    LOW = 4          # Background analytics


@dataclass
class APIRequest:
    """Synchronous API request object."""
    id: str
    method: str  # 'get_ticker', 'get_historical', 'get_accounts', etc.
    args: tuple
    kwargs: dict
    priority: RequestPriority
    timestamp: datetime
    retries: int = 0
    max_retries: int = 3


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    calls_per_minute: int = 8  # Conservative limit under Coinbase's 10/min
    burst_allowance: int = 3   # Allow small bursts
    cooldown_seconds: int = 8  # Wait time after rate limit hit


class SyncAPICoordinator:
    """
    Synchronous API coordinator that prevents rate limiting through
    request queuing and intelligent batching.
    """
    
    def __init__(self, coinbase_service, rate_config: RateLimitConfig = None):
        self.coinbase_service = coinbase_service
        self.rate_config = rate_config or RateLimitConfig()
        
        # Request queue with priority ordering
        self.request_queue: deque = deque()
        self.processing_lock = threading.Lock()
        
        # Rate limiting tracking
        self.call_timestamps: deque = deque()
        self.last_rate_limit_hit = None
        
        # Cache for avoiding duplicate calls
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 90  # seconds
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'rate_limits_avoided': 0,
            'queued_requests': 0
        }
        
        logger.info("🔧 SyncAPICoordinator initialized with synchronous rate limiting")
    
    def _generate_cache_key(self, method: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for request deduplication."""
        # Create deterministic key from method and arguments
        key_parts = [method]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    def _is_cached_valid(self, cache_entry: Dict) -> bool:
        """Check if cached response is still valid."""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_ttl
    
    def _should_rate_limit(self) -> bool:
        """Check if we should apply rate limiting."""
        now = time.time()
        
        # Clean old timestamps
        while self.call_timestamps and (now - self.call_timestamps[0]) > 60:
            self.call_timestamps.popleft()
        
        # Check if we're at rate limit
        if len(self.call_timestamps) >= self.rate_config.calls_per_minute:
            return True
        
        # Check if we recently hit rate limit
        if (self.last_rate_limit_hit and 
            (now - self.last_rate_limit_hit) < self.rate_config.cooldown_seconds):
            return True
        
        return False
    
    def _execute_request(self, request: APIRequest) -> Any:
        """Execute a single API request with error handling."""
        try:
            # Get the method from coinbase_service
            method = getattr(self.coinbase_service, request.method)
            
            # Record the API call timestamp
            self.call_timestamps.append(time.time())
            
            # Execute the call
            result = method(*request.args, **request.kwargs)
            
            # Cache the result
            cache_key = self._generate_cache_key(request.method, request.args, request.kwargs)
            self.response_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"✅ API call successful: {request.method}({request.args})")
            return result
            
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                self.last_rate_limit_hit = time.time()
                logger.warning(f"⚠️ Rate limit hit for {request.method}: {e}")
                self.stats['rate_limits_avoided'] += 1
                
                # Requeue with exponential backoff
                if request.retries < request.max_retries:
                    request.retries += 1
                    time.sleep(2 ** request.retries)  # Exponential backoff
                    return self._execute_request(request)
                
            logger.error(f"❌ API call failed: {request.method}: {e}")
            raise
    
    def _process_queue(self):
        """Process requests from the queue with rate limiting."""
        with self.processing_lock:
            if not self.request_queue:
                return None
            
            # Check if we should rate limit
            if self._should_rate_limit():
                logger.debug("⏳ Rate limiting active, deferring request")
                return None
            
            # Get highest priority request (sort by priority)
            if not self.request_queue:
                return None
                
            # Sort queue by priority (CRITICAL=1 first)
            sorted_queue = sorted(self.request_queue, key=lambda r: r.priority.value)
            request = sorted_queue[0]
            self.request_queue.remove(request)
            
            try:
                result = self._execute_request(request)
                self.stats['total_requests'] += 1
                return result
            except Exception as e:
                logger.error(f"❌ Request processing failed: {e}")
                raise
    
    def coordinated_call(self, method: str, *args, priority: RequestPriority = RequestPriority.MEDIUM, **kwargs) -> Any:
        """
        Make a coordinated API call with rate limiting and caching.
        
        Args:
            method: Name of the coinbase_service method to call
            *args: Positional arguments for the method
            priority: Request priority level
            **kwargs: Keyword arguments for the method
            
        Returns:
            Result from the API call
        """
        # Check cache first
        cache_key = self._generate_cache_key(method, args, kwargs)
        cached_entry = self.response_cache.get(cache_key)
        
        if cached_entry and self._is_cached_valid(cached_entry):
            self.stats['cache_hits'] += 1
            logger.debug(f"💾 Cache hit for {method}({args})")
            return cached_entry['result']
        
        # Create request
        request = APIRequest(
            id=f"{method}_{int(time.time() * 1000)}",
            method=method,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timestamp=datetime.now()
        )
        
        # For high priority requests, try immediate execution
        if priority in [RequestPriority.CRITICAL, RequestPriority.HIGH]:
            if not self._should_rate_limit():
                try:
                    result = self._execute_request(request)
                    self.stats['total_requests'] += 1
                    return result
                except Exception:
                    # Fall back to queueing
                    pass
        
        # Queue the request
        self.request_queue.append(request)
        self.stats['queued_requests'] += 1
        
        # Process queue with retry logic for trading requests
        max_attempts = 10 if priority == RequestPriority.CRITICAL else 3
        attempt = 0
        
        while attempt < max_attempts:
            result = self._process_queue()
            if result is not None:
                return result
            
            # Wait before retry (shorter wait for critical requests)
            wait_time = 0.5 if priority == RequestPriority.CRITICAL else 1.0
            time.sleep(wait_time)
            attempt += 1
        
        # Last resort: try direct execution for critical requests
        if priority == RequestPriority.CRITICAL:
            logger.warning(f"⚠️ Critical request {method} failed queue processing, attempting direct execution")
            try:
                result = self._execute_request(request)
                self.stats['total_requests'] += 1
                return result
            except Exception as e:
                logger.error(f"❌ Direct execution failed for critical request: {e}")
                raise
        
        raise Exception(f"Request {method} failed: queue processing timeout after {max_attempts} attempts")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordination statistics."""
        cache_hit_rate = 0
        if self.stats['total_requests'] > 0:
            cache_hit_rate = (self.stats['cache_hits'] / 
                            (self.stats['cache_hits'] + self.stats['total_requests'])) * 100
        
        return {
            'total_requests': self.stats['total_requests'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'rate_limits_avoided': self.stats['rate_limits_avoided'],
            'queued_requests': self.stats['queued_requests'],
            'queue_length': len(self.request_queue),
            'cache_entries': len(self.response_cache),
            'recent_api_calls': len(self.call_timestamps),
            'rate_limit_cooldown': (
                self.rate_config.cooldown_seconds - (time.time() - self.last_rate_limit_hit)
                if self.last_rate_limit_hit else 0
            )
        }
    
    def clear_cache(self):
        """Clear the response cache."""
        self.response_cache.clear()
        logger.info("🧹 Response cache cleared")


# Global coordinator instance
_coordinator_instance = None
_coordinator_lock = threading.Lock()


def get_sync_coordinator(coinbase_service=None):
    """Get or create the global synchronous coordinator instance."""
    global _coordinator_instance
    
    with _coordinator_lock:
        if _coordinator_instance is None and coinbase_service:
            _coordinator_instance = SyncAPICoordinator(coinbase_service)
            logger.info("🚀 Global SyncAPICoordinator created")
        
        return _coordinator_instance


def reset_coordinator():
    """Reset the global coordinator (for testing)."""
    global _coordinator_instance
    with _coordinator_lock:
        _coordinator_instance = None