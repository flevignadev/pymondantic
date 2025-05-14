"""
Caching and logging functionality for PyMondantic.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from functools import wraps
import redis
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

T = TypeVar("T")

class CacheManager:
    """
    Cache manager for MongoDB operations using Redis.
    """
    
    def __init__(
        self,
        redis_url: str,
        ttl: int = 3600,
        prefix: str = "pymondantic:"
    ):
        """
        Initialize the cache manager.
        
        Args:
            redis_url: Redis connection URL
            ttl: Time to live for cached items in seconds
            prefix: Prefix for cache keys
        """
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl
        self.prefix = prefix
    
    def _get_key(self, model: Type[Any], query: Dict[str, Any]) -> str:
        """Generate a cache key for a query."""
        return f"{self.prefix}{model.__name__}:{json.dumps(query, sort_keys=True)}"
    
    def get(self, model: Type[Any], query: Dict[str, Any]) -> Optional[Any]:
        """Get a cached result."""
        key = self._get_key(model, query)
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def set(self, model: Type[Any], query: Dict[str, Any], value: Any) -> None:
        """Cache a result."""
        key = self._get_key(model, query)
        self.redis.setex(key, self.ttl, json.dumps(value))
    
    def delete(self, model: Type[Any], query: Dict[str, Any]) -> None:
        """Delete a cached result."""
        key = self._get_key(model, query)
        self.redis.delete(key)
    
    def clear_model(self, model: Type[Any]) -> None:
        """Clear all cached results for a model."""
        pattern = f"{self.prefix}{model.__name__}:*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)

def with_cache(
    cache_manager: Optional[CacheManager] = None,
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorator for caching MongoDB operation results.
    
    Args:
        cache_manager: Optional cache manager instance
        ttl: Optional time to live override
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # Get model and query from args
            model = args[0]
            query = args[2] if len(args) > 2 else kwargs.get("filter_dict", {})
            
            # Try to get from cache
            cached = cache_manager.get(model, query)
            if cached is not None:
                return cached
            
            # Execute query
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(model, query, result)
            return result
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not cache_manager:
                return func(*args, **kwargs)
            
            # Get model and query from args
            model = args[0]
            query = args[2] if len(args) > 2 else kwargs.get("filter_dict", {})
            
            # Try to get from cache
            cached = cache_manager.get(model, query)
            if cached is not None:
                return cached
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(model, query, result)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class MongoLogger:
    """
    Logger for MongoDB operations with OpenTelemetry integration.
    """
    
    def __init__(self, name: str = "pymondantic"):
        """Initialize the logger."""
        self.logger = logging.getLogger(name)
        self.tracer = trace.get_tracer(name)
    
    def log_operation(
        self,
        operation: str,
        model: Type[Any],
        query: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> None:
        """Log a MongoDB operation."""
        with self.tracer.start_as_current_span(
            f"mongodb.{operation}",
            attributes={
                "model": model.__name__,
                "query": str(query) if query else None
            }
        ) as span:
            if error:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(error)
                self.logger.error(
                    f"MongoDB {operation} failed for {model.__name__}: {error}",
                    exc_info=True
                )
            else:
                span.set_status(Status(StatusCode.OK))
                self.logger.debug(
                    f"MongoDB {operation} completed for {model.__name__}"
                ) 