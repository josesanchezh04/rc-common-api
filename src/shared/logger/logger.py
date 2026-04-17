"""
Logger module using loguru for professional logging capabilities.

This module provides a configured logger instance with:
- Colored console output
- File rotation (daily and size-based)
- Custom formatting with timestamps, levels, and context
- Exception tracking with full stack traces
- Automatic tracking_id injection from context
"""

import sys
from pathlib import Path
from contextvars import ContextVar
from loguru import logger

# Context variables for request-scoped data
_tracking_id_var: ContextVar[str] = ContextVar("tracking_id", default="-")
_context_var: ContextVar[str] = ContextVar("context", default="-")

# Remove default handler
logger.remove()

# Define log directory
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def log_formatter(record):
    """Custom formatter that injects context variables into log records."""
    record["extra"]["tracking_id"] = _tracking_id_var.get()
    record["extra"]["context"] = _context_var.get()
    return True


# Custom format for logs
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[context]}</cyan>:<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
    "tracking_id=<yellow>{extra[tracking_id]}</yellow> - "
    "<level>{message}</level>"
)

# Console handler with colors
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
    filter=log_formatter,
)

# File handler with rotation
logger.add(
    LOG_DIR / "beautyfit.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="00:00",  # Rotate daily at midnight
    retention="30 days",  # Keep logs for 30 days
    compression="zip",  # Compress rotated logs
    backtrace=True,
    diagnose=True,
    enqueue=True,  # Thread-safe logging
    filter=log_formatter,
)

# Error file handler for errors only
logger.add(
    LOG_DIR / "errors.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",  # Rotate when file reaches 10MB
    retention="60 days",  # Keep error logs for 60 days
    compression="zip",
    backtrace=True,
    diagnose=True,
    enqueue=True,
    filter=log_formatter,
)


def set_tracking_id(tracking_id: str):
    """
    Set the tracking ID for the current request context.
    
    This should be called once per request, typically in middleware.
    All subsequent log calls in the same context will automatically include this tracking_id.
    
    Args:
        tracking_id: The tracking ID to set
    """
    _tracking_id_var.set(tracking_id)


def set_context(context: str):
    """
    Set the context for the current request.
    
    Args:
        context: The context name (e.g., "Mutation.register")
    """
    _context_var.set(context)


def get_logger(context: str = None):
    """
    Get the logger instance.
    
    The tracking_id is automatically injected from the context variable.
    You only need to specify the context (optional).
    
    Args:
        context: Optional context to set for this logger instance
        
    Returns:
        Logger instance
        
    Example:
        # In middleware: set_tracking_id(tracking_id)
        # In resolver:
        logger = get_logger("Mutation.register")
        logger.info("Processing request")  # tracking_id is automatically included
    """
    if context:
        set_context(context)
    
    return logger


# Export the main logger instance and utilities
__all__ = ["logger", "get_logger", "set_tracking_id", "set_context"]
