# ============================================================
# OLIVETTI PERFORMANCE LAYER
# Caching, optimization, and performance monitoring
# ============================================================

import time
import hashlib
from typing import Any, Callable, Optional
from functools import wraps, lru_cache
import streamlit as st

class PerformanceMonitor:
    """Track performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "ai_calls": 0,
            "ai_total_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "autosaves": 0,
        }
    
    def record_ai_call(self, duration: float):
        self.metrics["ai_calls"] += 1
        self.metrics["ai_total_time"] += duration
    
    def record_cache_hit(self):
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        self.metrics["cache_misses"] += 1
    
    def record_autosave(self):
        self.metrics["autosaves"] += 1
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        total_cache = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = (self.metrics["cache_hits"] / total_cache * 100) if total_cache > 0 else 0
        avg_ai_time = (self.metrics["ai_total_time"] / self.metrics["ai_calls"]) if self.metrics["ai_calls"] > 0 else 0
        
        return {
            "ai_calls": self.metrics["ai_calls"],
            "avg_ai_time": f"{avg_ai_time:.2f}s",
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "autosaves": self.metrics["autosaves"],
        }

# Global performance monitor
perf_monitor = PerformanceMonitor()


def cache_result(ttl_seconds: int = 300):
    """Cache function results with TTL"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        timestamps = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_data = str((args, tuple(sorted(kwargs.items()))))
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            current_time = time.time()
            if cache_key in cache:
                if current_time - timestamps[cache_key] < ttl_seconds:
                    perf_monitor.record_cache_hit()
                    return cache[cache_key]
                else:
                    # Expired
                    del cache[cache_key]
                    del timestamps[cache_key]
            
            # Cache miss - compute
            perf_monitor.record_cache_miss()
            result = func(*args, **kwargs)
            cache[cache_key] = result
            timestamps[cache_key] = current_time
            
            # Cleanup old entries
            if len(cache) > 100:
                oldest = min(timestamps.items(), key=lambda x: x[1])
                del cache[oldest[0]]
                del timestamps[oldest[0]]
            
            return result
        
        return wrapper
    return decorator


def timed_execution(func: Callable) -> Callable:
    """Decorator to measure execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        # Log slow operations
        if duration > 1.0:
            import logging
            logger = logging.getLogger("Olivetti")
            logger.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper


@lru_cache(maxsize=128)
def _cached_hash_vec(text: str, dims: int = 512):
    """Cached version of hash vector computation"""
    # Import here to avoid circular dependency
    import re
    WORD_RE = re.compile(r"[A-Za-z']+")
    
    vec = [0.0] * dims
    toks = [w.lower() for w in WORD_RE.findall(text or "")]
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        vec[h % dims] += 1.0
    for i, v in enumerate(vec):
        if v > 0:
            import math
            vec[i] = 1.0 + math.log(v)
    return tuple(vec)  # Return tuple for hashability


def batch_process(items: list, batch_size: int = 10) -> list:
    """Process items in batches for better performance"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results.extend(batch)
    return results


class RateLimiter:
    """Simple rate limiter for AI calls"""
    
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [t for t in self.calls if now - t < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            return False
        
        self.calls.append(now)
        return True
    
    def wait_time(self) -> float:
        """Get seconds to wait before next call"""
        if len(self.calls) < self.calls_per_minute:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, 60.0 - (time.time() - oldest_call))


# Global rate limiter
rate_limiter = RateLimiter(calls_per_minute=10)
