"""
Centralized API Call Coordinator - Phase 6.2 Implementation
Global rate limiter with priority queuing to prevent rate limiting errors.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from queue import PriorityQueue
from enum import Enum
import threading
from datetime import datetime, timedelta

# Import types but avoid circular imports by importing lazily where needed
from .shared_cache_service import APIRequest, Priority, DataType

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Status of API requests in the coordinator."""
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


@dataclass
class RateLimitStats:
    """Statistics for rate limiting monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_errors: int = 0
    last_request_time: float = 0
    circuit_breaker_open: bool = False
    circuit_breaker_open_until: float = 0


class CentralizedAPICoordinator:
    """
    Global API call coordinator that ensures ZERO rate limiting.
    All Coinbase API calls must go through this coordinator.
    """
    
    # Conservative rate limiting - guarantee under Coinbase limits
    MAX_CALLS_PER_MINUTE = 8  # Well under Coinbase's 10/minute limit
    MIN_INTERVAL_BETWEEN_CALLS = 8  # 8 seconds between calls (7.5 calls/minute)
    
    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
    CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes
    
    def __init__(self):
        """Initialize the centralized API coordinator."""
        self.request_queue = PriorityQueue()
        self.stats = RateLimitStats()
        self.active_requests: Dict[str, APIRequest] = {}
        self.completed_requests: Dict[str, Dict[str, Any]] = {}
        
        # Rate limiting state
        self.last_api_call_time = 0
        self.call_history: List[float] = []
        
        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        
        # Background processing
        self.is_running = False
        self.processor_thread = None
        
        logger.info("🚦 CentralizedAPICoordinator initialized")
    
    def start(self):
        """Start the background API request processor."""
        if not self.is_running:
            self.is_running = True
            self.processor_thread = threading.Thread(target=self._process_requests, daemon=True)
            self.processor_thread.start()
            logger.info("🚀 API request processor started")
    
    def stop(self):
        """Stop the background API request processor."""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("🛑 API request processor stopped")
    
    async def submit_request(self, request: APIRequest) -> str:
        """
        Submit an API request for coordinated execution.
        
        Args:
            request: API request to execute
            
        Returns:
            Request ID for tracking
        """
        request_id = f"{request.data_type.value}_{request.product_id}_{int(time.time() * 1000)}"
        
        # Check if we already have fresh cached data
        cached_data = await self._check_cache_first(request)
        if cached_data:
            logger.info(f"✅ Cache hit for {request.data_type.value}:{request.product_id} - skipping API call")
            self.completed_requests[request_id] = {
                "status": RequestStatus.COMPLETED,
                "data": cached_data,
                "source": "cache",
                "timestamp": time.time()
            }
            return request_id
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning(f"🔐 Circuit breaker open - rejecting request {request_id}")
            self.completed_requests[request_id] = {
                "status": RequestStatus.RATE_LIMITED,
                "error": "Circuit breaker open due to rate limiting",
                "timestamp": time.time()
            }
            return request_id
        
        # Add to queue with priority
        self.request_queue.put((request.priority.value, time.time(), request_id, request))
        self.active_requests[request_id] = request
        
        logger.info(f"📝 Queued request {request_id} with priority {request.priority.value}")
        return request_id
    
    async def get_request_result(self, request_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Get the result of a submitted request.
        
        Args:
            request_id: ID of the request
            timeout: Maximum time to wait for result
            
        Returns:
            Request result or None if timeout/not found
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self.completed_requests:
                result = self.completed_requests[request_id]
                
                # Clean up old completed requests
                if time.time() - result.get('timestamp', 0) > 300:  # 5 minutes
                    del self.completed_requests[request_id]
                
                return result
            
            await asyncio.sleep(0.1)  # Check every 100ms
        
        logger.warning(f"⏰ Request {request_id} timed out after {timeout}s")
        return None
    
    def _process_requests(self):
        """Background thread to process API requests with rate limiting."""
        logger.info("🔄 Starting API request processing loop")
        
        while self.is_running:
            try:
                # Get next request from priority queue (blocks if empty)
                if not self.request_queue.empty():
                    priority, timestamp, request_id, request = self.request_queue.get(timeout=1.0)
                    
                    # Enforce rate limiting
                    self._enforce_rate_limit()
                    
                    # Process the request
                    self._execute_api_request(request_id, request)
                else:
                    time.sleep(0.1)  # Small sleep if queue is empty
                    
            except Exception as e:
                logger.error(f"Error in API request processor: {e}")
                time.sleep(1.0)  # Prevent tight error loops
        
        logger.info("🏁 API request processing loop ended")
    
    def _enforce_rate_limit(self):
        """Enforce conservative rate limiting between API calls."""
        current_time = time.time()
        
        # Ensure minimum interval between calls
        time_since_last_call = current_time - self.last_api_call_time
        if time_since_last_call < self.MIN_INTERVAL_BETWEEN_CALLS:
            sleep_time = self.MIN_INTERVAL_BETWEEN_CALLS - time_since_last_call
            logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        # Update call history (for monitoring)
        self.call_history.append(current_time)
        # Keep only last hour of history
        one_hour_ago = current_time - 3600
        self.call_history = [t for t in self.call_history if t > one_hour_ago]
        
        self.last_api_call_time = time.time()
    
    def _execute_api_request(self, request_id: str, request: APIRequest):
        """Execute a single API request with error handling."""
        try:
            logger.info(f"🔄 Executing API request {request_id}: {request.data_type.value} for {request.product_id}")
            
            # Import services here to avoid circular imports
            from ..services.coinbase_service import coinbase_service
            
            # Execute the appropriate API call
            result = None
            if request.data_type == DataType.TICKER:
                result = coinbase_service.get_product_ticker(request.product_id)
            elif request.data_type == DataType.HISTORICAL:
                granularity = request.params.get('granularity', 3600)
                limit = request.params.get('limit', 100)
                df = coinbase_service.get_historical_data(request.product_id, granularity, limit)
                # Convert DataFrame to dict for JSON serialization
                result = df.to_dict('records') if not df.empty else []
            elif request.data_type == DataType.ACCOUNTS:
                result = coinbase_service.get_accounts()
            elif request.data_type == DataType.PRODUCTS:
                result = coinbase_service.get_products()
            elif request.data_type == DataType.BALANCE:
                currency = request.params.get('currency', 'USD')
                result = coinbase_service.get_available_balance(currency)
            
            if result is not None:
                # Success - store in completed requests and cache
                self.completed_requests[request_id] = {
                    "status": RequestStatus.COMPLETED,
                    "data": result,
                    "source": "api",
                    "timestamp": time.time()
                }
                
                # Warm the cache for future requests
                asyncio.run(self._warm_cache(request, result))
                
                # Update success stats
                self.stats.successful_requests += 1
                self.circuit_breaker_failures = 0  # Reset on success
                
                logger.info(f"✅ Successfully executed API request {request_id}")
                
            else:
                # API returned None - treat as failure
                self._handle_api_failure(request_id, "API returned None")
                
        except Exception as e:
            self._handle_api_failure(request_id, str(e))
        finally:
            # Clean up active request
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            # Update total stats
            self.stats.total_requests += 1
            self.stats.last_request_time = time.time()
    
    def _handle_api_failure(self, request_id: str, error_message: str):
        """Handle API request failures and update circuit breaker."""
        logger.error(f"❌ API request {request_id} failed: {error_message}")
        
        # Update failure stats
        self.stats.failed_requests += 1
        
        # Check for rate limiting
        if "429" in error_message or "rate limit" in error_message.lower():
            self.stats.rate_limit_errors += 1
            self.circuit_breaker_failures += 1
            self.circuit_breaker_last_failure = time.time()
            
            logger.error(f"🚨 RATE LIMITING DETECTED - failure count: {self.circuit_breaker_failures}")
            
            # Open circuit breaker if too many failures
            if self.circuit_breaker_failures >= self.CIRCUIT_BREAKER_FAILURE_THRESHOLD:
                self.stats.circuit_breaker_open = True
                self.stats.circuit_breaker_open_until = time.time() + self.CIRCUIT_BREAKER_TIMEOUT
                logger.error(f"🔐 CIRCUIT BREAKER OPENED for {self.CIRCUIT_BREAKER_TIMEOUT}s")
        
        # Store failure result
        self.completed_requests[request_id] = {
            "status": RequestStatus.FAILED,
            "error": error_message,
            "timestamp": time.time()
        }
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is currently open."""
        if self.stats.circuit_breaker_open:
            if time.time() < self.stats.circuit_breaker_open_until:
                return True
            else:
                # Circuit breaker timeout expired - reset
                self.stats.circuit_breaker_open = False
                self.stats.circuit_breaker_open_until = 0
                self.circuit_breaker_failures = 0
                logger.info("🔓 Circuit breaker reset")
                return False
        return False
    
    async def _check_cache_first(self, request: APIRequest) -> Optional[Dict[str, Any]]:
        """Check if we have fresh cached data for this request."""
        try:
            # Import here to avoid circular imports
            from .shared_cache_service import data_distribution_service
            
            if request.data_type == DataType.TICKER:
                return await data_distribution_service.get_ticker_cached(request.product_id)
            elif request.data_type == DataType.HISTORICAL:
                granularity = request.params.get('granularity', 3600)
                limit = request.params.get('limit', 100)
                return await data_distribution_service.get_historical_cached(request.product_id, granularity, limit)
            elif request.data_type == DataType.ACCOUNTS:
                return await data_distribution_service.get_accounts_cached()
            elif request.data_type == DataType.PRODUCTS:
                return await data_distribution_service.get_products_cached()
            elif request.data_type == DataType.BALANCE:
                currency = request.params.get('currency', 'USD')
                return await data_distribution_service.get_balance_cached(currency)
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")
        return None
    
    async def _warm_cache(self, request: APIRequest, result: Any):
        """Warm the cache with fresh API result."""
        try:
            # Import here to avoid circular imports
            from .shared_cache_service import data_distribution_service
            
            if request.data_type == DataType.TICKER:
                await data_distribution_service.warm_ticker_cache(request.product_id, result)
            elif request.data_type == DataType.HISTORICAL:
                granularity = request.params.get('granularity', 3600)
                limit = request.params.get('limit', 100)
                await data_distribution_service.warm_historical_cache(request.product_id, result, granularity, limit)
            elif request.data_type == DataType.ACCOUNTS:
                await data_distribution_service.warm_accounts_cache(result)
        except Exception as e:
            logger.warning(f"Error warming cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics and health information."""
        current_time = time.time()
        
        # Calculate calls per minute
        one_minute_ago = current_time - 60
        recent_calls = [t for t in self.call_history if t > one_minute_ago]
        calls_per_minute = len(recent_calls)
        
        return {
            "status": "running" if self.is_running else "stopped",
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "rate_limit_errors": self.stats.rate_limit_errors,
            "success_rate": (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100,
            "calls_per_minute": calls_per_minute,
            "max_calls_per_minute": self.MAX_CALLS_PER_MINUTE,
            "queue_size": self.request_queue.qsize(),
            "active_requests": len(self.active_requests),
            "circuit_breaker_open": self.stats.circuit_breaker_open,
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "last_request_time": self.stats.last_request_time,
            "time_since_last_call": current_time - self.last_api_call_time
        }


# Global instance for system-wide coordination
api_coordinator = CentralizedAPICoordinator()


# High-level API functions for easy migration
async def coordinated_get_ticker(product_id: str) -> Optional[Dict[str, Any]]:
    """Get ticker data through coordinated API calls."""
    request = APIRequest(
        product_id=product_id,
        data_type=DataType.TICKER,
        priority=Priority.BOT_EVALUATION,
        timestamp=time.time()
    )
    
    request_id = await api_coordinator.submit_request(request)
    result = await api_coordinator.get_request_result(request_id)
    
    return result.get('data') if result and result.get('status') == RequestStatus.COMPLETED else None


async def coordinated_get_historical(product_id: str, granularity: int = 3600, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
    """Get historical data through coordinated API calls."""
    request = APIRequest(
        product_id=product_id,
        data_type=DataType.HISTORICAL,
        priority=Priority.BOT_EVALUATION,
        timestamp=time.time(),
        params={'granularity': granularity, 'limit': limit}
    )
    
    request_id = await api_coordinator.submit_request(request)
    result = await api_coordinator.get_request_result(request_id)
    
    return result.get('data') if result and result.get('status') == RequestStatus.COMPLETED else None


async def coordinated_get_accounts() -> Optional[List[Dict[str, Any]]]:
    """Get accounts data through coordinated API calls."""
    request = APIRequest(
        product_id="global",
        data_type=DataType.ACCOUNTS,
        priority=Priority.BOT_EVALUATION,
        timestamp=time.time()
    )
    
    request_id = await api_coordinator.submit_request(request)
    result = await api_coordinator.get_request_result(request_id)
    
    return result.get('data') if result and result.get('status') == RequestStatus.COMPLETED else None


async def coordinated_get_products() -> Optional[List[Dict[str, Any]]]:
    """Get products data through coordinated API calls."""
    request = APIRequest(
        product_id="global",
        data_type=DataType.PRODUCTS,
        priority=Priority.MARKET_DATA,
        timestamp=time.time()
    )
    
    request_id = await api_coordinator.submit_request(request)
    result = await api_coordinator.get_request_result(request_id)
    
    return result.get('data') if result and result.get('status') == RequestStatus.COMPLETED else None