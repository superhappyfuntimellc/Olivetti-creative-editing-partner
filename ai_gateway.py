"""
============================================================
AI GATEWAY - Unified OpenAI Interface
============================================================
Single gateway for all AI calls with:
- Rate limiting
- Error handling & retry logic
- Performance monitoring
- Input validation
- Consistent temperature mapping
============================================================
"""

from typing import Dict, Any, Optional
import os
import time
import streamlit as st
from openai import OpenAI

# Import performance monitoring if available
try:
    from performance import PerformanceMonitor
    HAS_PERF = True
except ImportError:
    HAS_PERF = False

# Import error handling if available
try:
    from app import OlivettiError, APIError, safe_execute, validate_text_input
    HAS_ERROR_HANDLING = True
except ImportError:
    HAS_ERROR_HANDLING = False
    class OlivettiError(Exception):
        pass
    class APIError(OlivettiError):
        pass


def has_openai_key() -> bool:
    """Check if OpenAI API key is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))


def call_openai(system_brief: str, user_task: str, text: str, 
                temperature: Optional[float] = None) -> str:
    """
    ═══════════════════════════════════════════════════════════════
    UNIFIED AI GATEWAY
    ═══════════════════════════════════════════════════════════════
    All AI generation routes through this function.
    
    Args:
        system_brief: Complete Voice Bible brief from build_partner_brief()
        user_task: Specific task instructions (e.g., "Write 200 words")
        text: Current draft text for context
        temperature: Override temperature (default: use AI Intensity)
    
    Returns:
        Generated text from AI
    
    Raises:
        APIError: If OpenAI call fails after retries
    
    FEATURES:
    - Rate limiting check before API call
    - Input validation (max 100k chars)
    - Retry logic (3 attempts with exponential backoff)
    - Performance tracking (if enabled)
    - Error classification (rate limit vs. auth vs. general)
    ═══════════════════════════════════════════════════════════════
    """
    if not has_openai_key():
        raise APIError("OPENAI_API_KEY not configured")
    
    # Rate limiting check
    if hasattr(st.session_state, "rate_limiter"):
        can_proceed, wait_time = st.session_state.rate_limiter.check_rate_limit()
        if not can_proceed:
            raise APIError(f"Rate limit exceeded. Wait {wait_time:.0f}s before next call.")
    
    # Input validation
    if HAS_ERROR_HANDLING:
        system_brief = validate_text_input(system_brief, "system_brief", max_length=100000)
        user_task = validate_text_input(user_task, "user_task", max_length=10000)
        text = validate_text_input(text, "text", max_length=100000)
    else:
        # Basic validation
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
    
    for attempt in range(max_retries):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
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
            error_str = str(e).lower()
            
            # Classify error
            if "rate" in error_str or "429" in error_str:
                # Rate limit - don't retry
                raise APIError(f"Rate limit: {e}")
            elif "auth" in error_str or "401" in error_str:
                # Auth error - don't retry
                raise APIError(f"Authentication failed: {e}")
            elif "timeout" in error_str:
                # Timeout - retry with backoff
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait)
                    continue
            else:
                # General error - retry once
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
            
            # If we get here, it's the last attempt
            raise APIError(f"OpenAI call failed after {attempt + 1} attempts: {e}")
    
    # Should never reach here, but just in case
    raise APIError(f"OpenAI call failed: {last_error}")


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate (1 token ≈ 4 characters).
    Used for cost estimation and limits.
    """
    return len(text) // 4


def get_ai_status() -> Dict[str, Any]:
    """
    Get AI system status for display.
    
    Returns:
        Dict with keys: api_key_set, rate_limit_info, performance_stats
    """
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
