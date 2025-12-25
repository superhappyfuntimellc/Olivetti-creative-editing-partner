# ============================================================
# OLIVETTI CONFIGURATION MANAGEMENT
# Centralized configuration for production deployment
# ============================================================

import os
from typing import Optional

class Config:
    """Production configuration for Olivetti Creative Editing Partner"""
    
    # ═══ AI SERVICE ═══
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "90"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    
    # ═══ STORAGE ═══
    AUTOSAVE_DIR: str = os.getenv("AUTOSAVE_DIR", "autosave")
    AUTOSAVE_INTERVAL_SECONDS: int = int(os.getenv("AUTOSAVE_INTERVAL", "30"))
    MAX_BACKUPS: int = int(os.getenv("MAX_BACKUPS", "5"))
    
    # ═══ LIMITS ═══
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10MB
    MAX_DRAFT_LENGTH: int = int(os.getenv("MAX_DRAFT_LENGTH", "500000"))  # 500k chars
    MAX_PROJECTS: int = int(os.getenv("MAX_PROJECTS", "100"))
    
    # ═══ AI GENERATION ═══
    DEFAULT_AI_INTENSITY: float = float(os.getenv("DEFAULT_AI_INTENSITY", "0.75"))
    MIN_TEMPERATURE: float = 0.3
    MAX_TEMPERATURE: float = 1.2
    
    # ═══ RATE LIMITING ═══
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_CALLS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_CALLS", "10"))
    
    # ═══ LOGGING ═══
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "olivetti.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "3"))
    
    # ═══ FEATURES ═══
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"
    ENABLE_TELEMETRY: bool = os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"
    ENABLE_DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # ═══ PERFORMANCE ═══
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            return False
        if cls.MAX_UPLOAD_BYTES < 1024:
            return False
        if not (0 <= cls.DEFAULT_AI_INTENSITY <= 1.0):
            return False
        return True
    
    @classmethod
    def summary(cls) -> str:
        """Get configuration summary for logging"""
        return f"""
Olivetti Configuration:
  Model: {cls.OPENAI_MODEL}
  Autosave: {cls.AUTOSAVE_INTERVAL_SECONDS}s
  Max Upload: {cls.MAX_UPLOAD_BYTES / 1024 / 1024:.1f}MB
  Max Projects: {cls.MAX_PROJECTS}
  Rate Limiting: {cls.RATE_LIMIT_ENABLED}
  Analytics: {cls.ENABLE_ANALYTICS}
  Caching: {cls.ENABLE_CACHING}
  Debug Mode: {cls.ENABLE_DEBUG_MODE}
"""

# Export singleton
config = Config()
