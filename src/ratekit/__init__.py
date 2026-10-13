"""redis-ratekit — Atomic, Redis-backed rate limiting for Python."""

from .factory import RateLimiter

__all__ = ["RateLimiter"]
__version__ = "0.1.0"
