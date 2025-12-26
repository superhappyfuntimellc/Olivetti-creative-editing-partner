"""AI Gateway - Unified OpenAI interface with rate limiting, retries & monitoring."""

from typing import Dict, Any, Optional
import os
import time
import streamlit as st
from openai import OpenAI

try:
    from performance import PerformanceMonitor
    HAS_PERF = True
except ImportError:
    HAS_PERF = False

# Define error classes locally to avoid circular import
class OlivettiError(Exception):
    pass

class APIError(OlivettiError):
    pass

HAS_ERROR_HANDLING = True


def _get_key() -> str:
    """Get API key from env or secrets."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            key = str(st.secrets.get("OPENAI_API_KEY", ""))
        except:
            pass
    return key or ""


def has_openai_key() -> bool:
    """Check if API key configured."""
    return bool(_get_key())


def call_openai(system_brief: str, user_task: str, text: str, 
                temperature: Optional[float] = None) -> str:
    """Unified AI gateway with rate limiting, retries, and validation."""
    if not has_openai_key():
        raise APIError("OPENAI_API_KEY not configured")
    
    # Rate limiting check
    if hasattr(st.session_state, "rate_limiter"):
        can_proceed, wait_time = st.session_state.rate_limiter.check_rate_limit()
        if not can_proceed:
            raise APIError(f"Rate limit exceeded. Wait {wait_time:.0f}s before next call.")
    
    # Input validation
    if len(system_brief) > 100000:
        raise APIError("system_brief exceeds 100k character limit")
    if len(user_task) > 10000:
        raise APIError("user_task exceeds 10k character limit")
    if len(text) > 100000:
        raise APIError("text exceeds 100k character limit")
    
    # Get temperature from AI Intensity if not provided
    if temperature is None:
        from voice_bible import temperature_from_intensity
        ai_x = st.session_state.get("ai_intensity", 0.5)
        temperature = temperature_from_intensity(ai_x)
    
    # Get model
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Start performance tracking
    start_time = time.time()
    
    # Construct messages
    messages = [
        {"role": "system", "content": system_brief},
        {"role": "user", "content": f"{user_task}\n\n{text}"}
    ]
    
    # Retry logic
    max_retries = 3
    last_error = None
    
    # Get API key
    api_key = _get_key()
    if not api_key:
        raise APIError("OPENAI_API_KEY not configured")
    
    for attempt in range(max_retries):
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=4000,
                timeout=90.0
            )
            
            result = response.choices[0].message.content or ""
            
            # Track performance
            elapsed = time.time() - start_time
            if HAS_PERF and hasattr(st.session_state, "perf_monitor"):
                st.session_state.perf_monitor.track_ai_call(elapsed, len(result))
            
            return result
            
        except Exception as e:
            last_error = e
            err = str(e).lower()
            
            # Don't retry auth/rate errors
            if "rate" in err or "429" in err:
                raise APIError(f"Rate limit: {e}")
            if "auth" in err or "401" in err:
                raise APIError(f"Auth failed: {e}")
            
            # Retry with backoff
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt if "timeout" in err else 1)
                continue
            
            raise APIError(f"Failed after {attempt + 1} attempts: {e}")
    
    # Should never reach here, but just in case
    raise APIError(f"OpenAI call failed: {last_error}")


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars)."""
    return len(text) // 4


def get_ai_status() -> Dict[str, Any]:
    """Get AI system status (key, rate limits, performance)."""
    status = {
        "api_key_set": has_openai_key(),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }
    
    # Rate limit info
    if hasattr(st.session_state, "rate_limiter"):
        rl = st.session_state.rate_limiter
        can_proceed, wait_time = rl.check_rate_limit()
        status["rate_limit"] = {
            "can_proceed": can_proceed,
            "wait_time_seconds": wait_time,
            "calls_per_minute": getattr(rl, "max_calls_per_minute", 10)
        }
    
    # Performance stats
    if HAS_PERF and hasattr(st.session_state, "perf_monitor"):
        pm = st.session_state.perf_monitor
        stats = pm.get_stats()
        status["performance"] = stats
    
    return status
