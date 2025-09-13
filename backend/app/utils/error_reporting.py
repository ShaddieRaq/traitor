"""
Error reporting wrapper for bot services
"""

import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(str, Enum):
    SIGNAL_CALCULATION = "signal_calculation"
    MARKET_DATA = "market_data" 
    CONFIGURATION = "configuration"
    TRADING_LOGIC = "trading_logic"
    SYSTEM = "system"

def report_bot_error(
    error_type: ErrorType,
    message: str,
    bot_id: Optional[int] = None,
    bot_name: Optional[str] = None,
    details: Optional[Dict] = None
):
    """Report bot error to the error tracking system"""
    try:
        # Import here to avoid circular imports
        from app.api.system_errors import ErrorStore
        return ErrorStore.add_error(error_type, message, bot_id, bot_name, details)
    except ImportError:
        # Fallback to just logging
        logger.error(f"Bot Error [{error_type.value}] {bot_name or 'Unknown'}: {message}")
        return None

def bot_error_handler(error_type: ErrorType, bot_id: Optional[int] = None, bot_name: Optional[str] = None):
    """Decorator to automatically catch and report bot errors"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Report the error
                report_bot_error(
                    error_type=error_type,
                    message=str(e),
                    bot_id=bot_id,
                    bot_name=bot_name,
                    details={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Truncate for safety
                        "kwargs": str(kwargs)[:200]
                    }
                )
                
                # Re-raise the exception so normal error handling still works
                raise e
        return wrapper
    return decorator

# Example usage:
# @bot_error_handler(ErrorType.SIGNAL_CALCULATION, bot_id=1, bot_name="BTC Bot")
# def calculate_rsi(data):
#     # This will automatically report any errors to the user-visible system
#     return rsi_calculation(data)
