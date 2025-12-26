# ============================================================
# OLIVETTI CREATIVE EDITING PARTNER
# Professional-Grade AI Author Engine
# ============================================================
#
# SYSTEM ARCHITECTURE (Spiderweb of Intelligent, Trainable Functions):
#
# ┌─────────────────────────────────────────────────────────────────┐
# │                    USER TRAINING INPUTS                          │
# ├─────────────────────────────────────────────────────────────────┤
# │ 1. Style Banks → Upload/paste samples → Per-lane training       │
# │ 2. Voice Vault → Add voice samples → Semantic vector storage    │
# │ 3. Story Bible → Import/generate → Canon enforcement            │
# │ 4. Voice Bible → Enable controls → Real-time modulation         │
# └─────────────────────────────────────────────────────────────────┘
#                              ↓
# ┌─────────────────────────────────────────────────────────────────┐
# │                   INTELLIGENT RETRIEVAL                          │
# ├─────────────────────────────────────────────────────────────────┤
# │ • retrieve_style_exemplars() ← Context-aware semantic search    │
# │ • retrieve_mixed_exemplars() ← Voice vault vector matching      │
# │ • _story_bible_text() ← Canon assembly                          │
# │ • engine_style_directive() ← Style guidance generation          │
# └─────────────────────────────────────────────────────────────────┘
#                              ↓
# ┌─────────────────────────────────────────────────────────────────┐
# │              UNIFIED AI BRIEF CONSTRUCTION                       │
# ├─────────────────────────────────────────────────────────────────┤
# │ build_partner_brief(action, lane):                              │
# │   ✓ AI Intensity → temperature_from_intensity()                 │
# │   ✓ Writing Style → engine_style_directive() + exemplars        │
# │   ✓ Genre Influence → mood/pacing directives                    │
# │   ✓ Trained Voice → semantic retrieval of user samples          │
# │   ✓ Match My Style → one-shot adaptation                        │
# │   ✓ POV/Tense → technical specs                                 │
# │   ✓ Story Bible → canon enforcement                             │
# │   ✓ Lane Detection → context-aware mode (Dialogue/Narration)    │
# └─────────────────────────────────────────────────────────────────┘
#                              ↓
# ┌─────────────────────────────────────────────────────────────────┐
# │                 UNIFIED AI GENERATION                            │
# ├─────────────────────────────────────────────────────────────────┤
# │ call_openai(brief, task, text):                                 │
# │   → OpenAI API with temperature from AI Intensity               │
# │   → System prompt = full Voice Bible brief                      │
# │   → User prompt = action-specific task                          │
# │   → Returns professional-grade prose                            │
# └─────────────────────────────────────────────────────────────────┘
#                              ↓
# ┌─────────────────────────────────────────────────────────────────┐
# │               ALL ACTIONS USE SAME ENGINE                        │
# ├─────────────────────────────────────────────────────────────────┤
# │ • partner_action(Write/Rewrite/Expand/etc) ← Writing desk       │
# │ • generate_story_bible_section() ← Story Bible generation       │
# │ • sb_breakdown_ai() ← Import document parsing (Voice Bible)     │
# │ ALL route through Voice Bible controls + call_openai()          │
# └─────────────────────────────────────────────────────────────────┘
#                              ↓
# ┌─────────────────────────────────────────────────────────────────┐
# │                  ADAPTIVE FEEDBACK LOOP                          │
# ├─────────────────────────────────────────────────────────────────┤
# │ User adds training → Vector storage → Semantic retrieval →      │
# │ → Better exemplars → Improved AI brief → Higher quality prose   │
# │                                                                  │
# │ CONTINUOUS IMPROVEMENT: More training = Better adaptation        │
# └─────────────────────────────────────────────────────────────────┘
#
# VERIFICATION CHECKLIST (All ✓ = Fully Connected):
# ✓ AI Intensity → temperature_from_intensity() → call_openai()
# ✓ Style Banks → retrieve_style_exemplars() → build_partner_brief()
# ✓ Voice Vault → retrieve_mixed_exemplars() → build_partner_brief()
# ✓ Story Bible → _story_bible_text() → build_partner_brief()
# ✓ Voice Bible Controls → build_partner_brief() → ALL AI actions
# ✓ Write/Rewrite/Expand → partner_action() → build_partner_brief()
# ✓ Generate Synopsis/etc → generate_story_bible_section() → Voice Bible
# ✓ Import → sb_breakdown_ai() → call_openai() → Voice Bible
# ✓ Status Display → _get_voice_bible_summary() → Real-time feedback
# ✓ Bay System → Project management → Story Bible linking
#
# DATA FLOW EXAMPLE (Write Action):
# User clicks "Write" 
#   → queue_action("Write")
#   → partner_action("Write")
#   → lane = current_lane_from_draft(text)  [Context detection]
#   → brief = build_partner_brief("Write", lane)
#        → ai_x = st.session_state.ai_intensity  [0.75]
#        → story_bible = _story_bible_text()  [Canon]
#        → style_exemplars = retrieve_style_exemplars(...)  [Semantic search]
#        → voice_exemplars = retrieve_mixed_exemplars(...)  [Vector match]
#        → Returns: 500-line unified prompt with ALL controls
#   → out = call_openai(brief, task, text)
#        → temperature = temperature_from_intensity(0.75) = 0.86
#        → OpenAI API call with full brief
#        → Returns: Professional prose matching ALL Voice Bible settings
#   → apply_append(out)  [Add to draft]
#   → status = "Write complete (AI:HIGH • Style:LYRICAL • Genre:Literary)"
#
# RESULT: Spiderweb fully connected. Every component feeds into unified AI.
# ============================================================

import os
import re
import math
import json
import hashlib
import logging
import traceback
import zipfile
from io import BytesIO
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from functools import wraps, lru_cache
from contextlib import contextmanager
import streamlit as st

# Optional DOCX support (import/export). UI will gracefully degrade if missing.
try:
    from docx import Document  # type: ignore
    from docx.shared import Pt, Inches  # type: ignore
    from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Optional EPUB support
try:
    from ebooklib import epub  # type: ignore
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# Optional PDF support (lightweight fpdf2)
try:
    from fpdf import FPDF  # type: ignore
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Optional audio export support (gTTS)
try:
    from gtts import gTTS  # type: ignore
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# ============================================================
# LOGGING & ERROR HANDLING INFRASTRUCTURE
# ============================================================

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

log_handler = RotatingFileHandler(
    'olivetti.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=3
)
log_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Olivetti")
logger.info("Olivetti application starting")

class OlivettiError(Exception):
    """Base exception for Olivetti-specific errors"""
    pass

class AIServiceError(OlivettiError):
    """Errors related to AI service calls"""
    pass

class DataValidationError(OlivettiError):
    """Errors related to data validation"""
    pass

class StorageError(OlivettiError):
    """Errors related to file storage operations"""
    pass

def safe_execute(func_name: str = "", fallback_value: Any = None, show_error: bool = True):
    """Decorator for safe function execution with error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            try:
                return func(*args, **kwargs)
            except OlivettiError as e:
                logger.error(f"{name} failed with OlivettiError: {e}")
                if show_error:
                    st.error(f"⚠️ {name}: {str(e)}")
                return fallback_value
            except Exception as e:
                logger.error(f"{name} failed with unexpected error: {e}\n{traceback.format_exc()}")
                if show_error:
                    st.error(f"❌ Unexpected error in {name}. Check logs for details.")
                return fallback_value
        return wrapper
    return decorator

@contextmanager
def error_boundary(context: str, silent: bool = False):
    """Context manager for error boundaries"""
    try:
        yield
    except OlivettiError as e:
        logger.error(f"Error in {context}: {e}")
        if not silent:
            st.error(f"⚠️ {context}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in {context}: {e}\n{traceback.format_exc()}")
        if not silent:
            st.error(f"❌ Unexpected error in {context}. Check logs for details.")

def validate_text_input(text: str, field_name: str, max_length: int = 1000000, min_length: int = 0) -> str:
    """Validate text input with length constraints"""
    if not isinstance(text, str):
        raise DataValidationError(f"{field_name} must be a string")
    if len(text) < min_length:
        raise DataValidationError(f"{field_name} must be at least {min_length} characters")
    if len(text) > max_length:
        raise DataValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
    return text

def validate_dict(data: Any, field_name: str) -> Dict:
    """Validate dictionary data"""
    if not isinstance(data, dict):
        raise DataValidationError(f"{field_name} must be a dictionary")
    return data

# ============================================================
# MODULE IMPORTS (Production Architecture)
# ============================================================
# Olivetti uses a modular architecture for maintainability.
# For single-file deployment, keep all code in this file.
# For development, split into focused modules.

# Optional module imports - graceful degradation if not available
try:
    from voice_bible import (
        build_partner_brief as _vb_build_brief,
        temperature_from_intensity as _vb_temp,
        get_voice_bible_summary as _vb_summary,
        engine_style_directive as _vb_style_directive
    )
    HAS_VOICE_BIBLE_MODULE = True
except ImportError:
    HAS_VOICE_BIBLE_MODULE = False
    logger.info("voice_bible.py not found, using inline implementations")

try:
    from voice_vault import (
        add_voice_sample as _vv_add,
        delete_voice_sample as _vv_delete,
        retrieve_mixed_exemplars as _vv_retrieve,
        get_voice_vault_stats as _vv_stats,
        list_voices as _vv_list,
        create_voice as _vv_create,
        delete_voice as _vv_delete_voice
    )
    HAS_VOICE_VAULT_MODULE = True
except ImportError:
    HAS_VOICE_VAULT_MODULE = False
    logger.info("voice_vault.py not found, using inline implementations")

try:
    from style_banks import (
        create_style_bank as _sb_create,
        add_style_exemplar as _sb_add,
        retrieve_style_exemplars as _sb_retrieve,
        get_style_bank_stats as _sb_stats
    )
    HAS_STYLE_BANKS_MODULE = True
except ImportError:
    HAS_STYLE_BANKS_MODULE = False
    logger.info("style_banks.py not found, using inline implementations")

try:
    from story_bible import (
        get_story_bible_text as _story_get,
        update_story_bible_section as _story_update
    )
    HAS_STORY_BIBLE_MODULE = True
except ImportError:
    HAS_STORY_BIBLE_MODULE = False
    logger.info("story_bible.py not found, using inline implementations")

try:
    from ai_gateway import (
        call_openai as _ai_call,
        has_openai_key as _ai_has_key,
        get_ai_status as _ai_status
    )
    HAS_AI_GATEWAY_MODULE = True
except ImportError:
    HAS_AI_GATEWAY_MODULE = False
    logger.info("ai_gateway.py not found, using inline implementations")

# ============================================================
# OLIVETTI DESK — one file, production-stable, paste+click
# ============================================================

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

DEFAULT_MODEL = "gpt-4o-mini"

def _get_openai_key_or_empty() -> str:
    try:
        return str(st.secrets.get("OPENAI_API_KEY", ""))  # type: ignore[attr-defined]
    except Exception:
        return ""

def _get_openai_model() -> str:
    try:
        return str(st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL))  # type: ignore[attr-defined]
    except Exception:
        return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

OPENAI_MODEL = _get_openai_model()

def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or _get_openai_key_or_empty())

def get_ai_intensity_safe() -> float:
    """Get AI intensity with safe fallback to prevent crashes."""
    try:
        val = st.session_state.get("ai_intensity", 0.75)
        val = float(val)
        return max(0.0, min(1.0, val))
    except (ValueError, TypeError, AttributeError):
        return 0.75

def require_openai_key() -> str:
    """Stop the app with a clear message if no OpenAI key is configured."""
    key = os.getenv("OPENAI_API_KEY") or _get_openai_key_or_empty()
    if not key:
        st.error(
            "OPENAI_API_KEY is not set. Add it as an environment variable (OPENAI_API_KEY) or as a Streamlit secret."
        )
        st.stop()
    return key


# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti Desk", layout="wide", initial_sidebar_state="expanded")

# Olivetti Quaderno-inspired UI — Sleek, sexy, fun, easy
st.markdown(
    """
<style>
/* ========== OLIVETTI QUADERNO LUXE PALETTE ========== */
:root{
  --olivetti-cream: #f5f0e8;
  --olivetti-beige: #e8dcc8;
  --olivetti-tan: #d4c4a8;
  --olivetti-bronze: #b8956a;
  --olivetti-gold: #cda35d;
  --olivetti-charcoal: #2a2520;
  --olivetti-dark: #1a1614;
  --olivetti-lcd: #3d4a3a;
  --olivetti-lcd-text: #c8d5b8;
  
  --accent-primary: #d4c4a8;
  --accent-gold: #cda35d;
  --accent-glow: rgba(212, 196, 168, 0.35);
  --text-primary: #f5f0e8;
  --text-muted: rgba(245, 240, 232, 0.7);
  --panel-bg: rgba(42, 37, 32, 0.75);
  --paper-bg: #fffef9;
  --paper-text: #1a1614;
}

/* ========== TYPOGRAPHY (Italian Elegance) ========== */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&family=Playfair+Display:wght@600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"]{
  font-family: 'IBM Plex Mono', 'Courier New', monospace;
  font-size: 14px;
  letter-spacing: 0.4px;
}

h1, h2, h3, h4, h5, h6, .stSubheader{
  font-family: 'Playfair Display', 'Libre Baskerville', Georgia, serif;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--accent-gold);
  text-shadow: 
    0 2px 12px rgba(205, 163, 93, 0.5),
    0 4px 24px rgba(0, 0, 0, 0.4);
  background: linear-gradient(145deg, #e8dcc8 0%, #cda35d 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ========== MAIN BACKGROUND (Luxe Quaderno hardware) ========== */
.stApp{
  background: 
    /* Noise texture */
    url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><filter id="n"><feTurbulence baseFrequency="0.9" numOctaves="4"/></filter><rect width="300" height="300" filter="url(%23n)" opacity="0.03"/></svg>'),
    /* Metallic sheen */
    repeating-linear-gradient(
      90deg,
      transparent 0px,
      rgba(212, 196, 168, 0.03) 1px,
      transparent 2px,
      transparent 4px
    ),
    /* Spotlight effects */
    radial-gradient(ellipse at 20% 10%, rgba(205, 163, 93, 0.15), transparent 40%),
    radial-gradient(ellipse at 80% 90%, rgba(184, 149, 106, 0.12), transparent 45%),
    radial-gradient(circle at 50% 50%, rgba(212, 196, 168, 0.08), transparent 60%),
    /* Deep gradient base */
    linear-gradient(135deg, 
      #14120f 0%, 
      #1a1614 20%,
      #2a2520 50%,
      #1a1614 80%,
      #14120f 100%
    );
  color: var(--text-primary);
  position: relative;
}

.stApp::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: radial-gradient(ellipse at top, rgba(205, 163, 93, 0.1), transparent);
  pointer-events: none;
  z-index: 0;
}

header[data-testid="stHeader"]{ 
  background: linear-gradient(180deg, rgba(26, 22, 20, 0.9), transparent);
  border-bottom: 2px solid rgba(205, 163, 93, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
}

/* ========== SIDEBAR (Premium Control Panel) ========== */
[data-testid="stSidebar"]{
  background: 
    /* Brushed metal texture */
    repeating-linear-gradient(
      180deg,
      rgba(212, 196, 168, 0.02) 0px,
      transparent 1px,
      transparent 2px,
      rgba(212, 196, 168, 0.02) 3px
    ),
    linear-gradient(180deg, 
      rgba(42, 37, 32, 0.98) 0%, 
      rgba(26, 22, 20, 1) 100%
    );
  border-right: 4px solid;
  border-image: linear-gradient(180deg, #cda35d 0%, #b8956a 50%, #cda35d 100%) 1;
  box-shadow: 
    inset -3px 0 15px rgba(205, 163, 93, 0.15),
    12px 0 40px rgba(0, 0, 0, 0.6),
    inset 0 0 60px rgba(26, 22, 20, 0.5);
}

[data-testid="stSidebar"]::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, 
    transparent 0%,
    rgba(205, 163, 93, 0.5) 20%,
    rgba(205, 163, 93, 0.8) 50%,
    rgba(205, 163, 93, 0.5) 80%,
    transparent 100%
  );
  box-shadow: 0 0 20px rgba(205, 163, 93, 0.4);
}

[data-testid="stSidebar"] *{ 
  color: var(--text-primary); 
}

section.main > div.block-container{
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1600px;
}

/* ========== EXPANDERS (Luxe LCD Panels) ========== */
details[data-testid="stExpander"]{
  background: 
    linear-gradient(135deg, rgba(61, 74, 58, 0.25), rgba(61, 74, 58, 0.15));
  border: 2px solid rgba(200, 213, 184, 0.3);
  border-radius: 10px;
  box-shadow: 
    0 6px 16px rgba(0, 0, 0, 0.5),
    0 2px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(200, 213, 184, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  overflow: hidden;
  margin: 1rem 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

details[data-testid="stExpander"]::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%,
    rgba(200, 213, 184, 0.4) 50%,
    transparent 100%
  );
}

details[data-testid="stExpander"]:hover{
  border-color: rgba(205, 163, 93, 0.5);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.6),
    0 4px 12px rgba(205, 163, 93, 0.2),
    inset 0 1px 0 rgba(205, 163, 93, 0.25),
    0 0 20px rgba(205, 163, 93, 0.15);
  transform: translateY(-2px);
}

details[data-testid="stExpander"] > summary{
  padding: 1rem 1.3rem !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase;
  color: var(--olivetti-lcd-text) !important;
  background: 
    linear-gradient(180deg, 
      rgba(61, 74, 58, 0.4) 0%, 
      rgba(61, 74, 58, 0.2) 100%
    );
  border-bottom: 1px solid rgba(200, 213, 184, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  text-shadow: 0 0 10px rgba(200, 213, 184, 0.3);
}

details[data-testid="stExpander"] > summary:hover{
  background: 
    linear-gradient(180deg, 
      rgba(61, 74, 58, 0.5) 0%, 
      rgba(61, 74, 58, 0.3) 100%
    );
  color: var(--accent-gold) !important;
  text-shadow: 0 0 15px rgba(205, 163, 93, 0.5);
}

details[data-testid="stExpander"][open] > summary{ 
  border-bottom: 2px solid rgba(205, 163, 93, 0.4);
  background: 
    linear-gradient(180deg, 
      rgba(205, 163, 93, 0.2) 0%, 
      rgba(61, 74, 58, 0.2) 100%
    );
  box-shadow: inset 0 -2px 8px rgba(205, 163, 93, 0.15);
}

/* ========== TEXT AREAS (Luxe Typewriter Paper) ========== */
div[data-testid="stTextArea"] textarea{
  font-family: 'Courier New', 'Courier', monospace !important;
  font-size: 17px !important;
  line-height: 1.75 !important;
  padding: 28px !important;
  resize: vertical !important;
  min-height: 540px !important;
  background: 
    /* Paper texture */
    repeating-linear-gradient(
      0deg,
      transparent 0px,
      transparent 1.7rem,
      rgba(212, 196, 168, 0.08) 1.7rem,
      rgba(212, 196, 168, 0.08) calc(1.7rem + 1px)
    ),
    linear-gradient(135deg, #fffef9 0%, #fbf9f4 100%) !important;
  color: var(--paper-text) !important;
  border: 4px solid rgba(205, 163, 93, 0.4) !important;
  border-radius: 6px !important;
  box-shadow: 
    /* Inner shadow for depth */
    inset 0 3px 12px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    /* Outer glow and elevation */
    0 10px 30px rgba(0, 0, 0, 0.4),
    0 4px 12px rgba(205, 163, 93, 0.2),
    0 0 40px rgba(205, 163, 93, 0.08) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stTextArea"] textarea:focus{
  outline: none !important;
  border: 4px solid rgba(205, 163, 93, 0.8) !important;
  box-shadow: 
    /* Intense focus glow */
    0 0 0 4px rgba(205, 163, 93, 0.25),
    0 0 0 8px rgba(205, 163, 93, 0.1),
    inset 0 3px 12px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 14px 40px rgba(0, 0, 0, 0.5),
    0 6px 20px rgba(205, 163, 93, 0.3),
    0 0 60px rgba(205, 163, 93, 0.2) !important;
  transform: translateY(-2px);
}

/* ========== BUTTONS (Premium Function Keys) ========== */
button[kind="secondary"], button[kind="primary"]{
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  padding: 0.85rem 1.4rem !important;
  border-radius: 8px !important;
  border: 2px solid transparent !important;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
}

button[kind="primary"]{
  background: linear-gradient(145deg, #e8dcc8 0%, #cda35d 50%, #b8956a 100%) !important;
  color: #1a1614 !important;
  border-color: rgba(184, 149, 106, 0.6) !important;
  box-shadow: 
    0 6px 16px rgba(205, 163, 93, 0.5),
    0 2px 8px rgba(0, 0, 0, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.4),
    inset 0 -2px 0 rgba(0, 0, 0, 0.25) !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
}

button[kind="primary"]::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

button[kind="primary"]:hover::before {
  left: 100%;
}

button[kind="secondary"]{
  background: 
    linear-gradient(145deg, 
      rgba(245, 240, 232, 0.12) 0%, 
      rgba(245, 240, 232, 0.06) 100%
    ) !important;
  color: var(--text-primary) !important;
  border-color: rgba(212, 196, 168, 0.4) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(245, 240, 232, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2) !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

button:hover{
  transform: translateY(-3px) scale(1.03) !important;
  border-color: var(--accent-gold) !important;
  box-shadow: 
    0 10px 28px rgba(205, 163, 93, 0.4),
    0 4px 16px rgba(205, 163, 93, 0.3),
    0 0 25px rgba(205, 163, 93, 0.2),
    inset 0 2px 0 rgba(255, 255, 255, 0.3) !important;
  filter: brightness(1.2) saturate(1.1) !important;
}

button:active{
  transform: translateY(-1px) scale(1.00) !important;
  box-shadow: 
    0 4px 12px rgba(205, 163, 93, 0.3),
    inset 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

/* ========== TABS (Luxe LCD Segments) ========== */
[data-testid="stTabs"] [data-baseweb="tab-list"]{ 
  gap: 8px; 
  border-bottom: 3px solid;
  border-image: linear-gradient(90deg, 
    transparent 0%,
    rgba(205, 163, 93, 0.3) 20%,
    rgba(205, 163, 93, 0.5) 50%,
    rgba(205, 163, 93, 0.3) 80%,
    transparent 100%
  ) 1;
  padding-bottom: 4px;
}

[data-testid="stTabs"] button[role="tab"]{
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  border-radius: 8px 8px 0 0 !important;
  padding: 0.75rem 1.3rem !important;
  background: 
    linear-gradient(180deg, 
      rgba(61, 74, 58, 0.3) 0%, 
      rgba(61, 74, 58, 0.15) 100%
    ) !important;
  border: 2px solid rgba(200, 213, 184, 0.25) !important;
  border-bottom: none !important;
  color: var(--olivetti-lcd-text) !important;
  transition: all 0.2s ease !important;
  position: relative;
  text-shadow: 0 0 8px rgba(200, 213, 184, 0.2);
}

[data-testid="stTabs"] button[role="tab"]:hover{
  background: 
    linear-gradient(180deg, 
      rgba(61, 74, 58, 0.4) 0%, 
      rgba(61, 74, 58, 0.25) 100%
    ) !important;
  color: var(--accent-gold) !important;
  text-shadow: 0 0 15px rgba(205, 163, 93, 0.5);
  border-color: rgba(205, 163, 93, 0.3) !important;
}

[data-testid="stTabs"] button[aria-selected="true"]{
  background: 
    linear-gradient(180deg, 
      rgba(205, 163, 93, 0.3) 0%, 
      rgba(205, 163, 93, 0.15) 50%,
      transparent 100%
    ) !important;
  border-color: rgba(205, 163, 93, 0.6) !important;
  color: var(--accent-gold) !important;
  box-shadow: 
    0 -3px 12px rgba(205, 163, 93, 0.3),
    inset 0 1px 0 rgba(205, 163, 93, 0.2),
    0 0 20px rgba(205, 163, 93, 0.15) !important;
  text-shadow: 0 0 20px rgba(205, 163, 93, 0.6);
}

/* ========== SLIDERS (Premium Tactile Controls) ========== */
div[data-baseweb="slider"] {
  padding: 0.75rem 0 !important;
}

div[data-baseweb="slider"] div[role="slider"] {
  background: 
    radial-gradient(circle, #e8dcc8 0%, #cda35d 50%, #b8956a 100%) !important;
  border: 3px solid rgba(184, 149, 106, 0.8) !important;
  box-shadow: 
    0 3px 12px rgba(205, 163, 93, 0.5),
    0 1px 4px rgba(0, 0, 0, 0.3),
    0 0 15px rgba(205, 163, 93, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
  width: 22px !important;
  height: 22px !important;
  transition: all 0.2s ease !important;
}

div[data-baseweb="slider"] div[role="slider"]:hover {
  transform: scale(1.15);
  box-shadow: 
    0 4px 16px rgba(205, 163, 93, 0.6),
    0 0 20px rgba(205, 163, 93, 0.4) !important;
}

div[data-baseweb="slider"] div[data-baseweb="slider-track"] {
  background: 
    linear-gradient(90deg, 
      rgba(205, 163, 93, 0.3) 0%, 
      rgba(205, 163, 93, 0.5) 100%
    ) !important;
  height: 5px !important;
  border-radius: 3px !important;
  box-shadow: 
    inset 0 1px 3px rgba(0, 0, 0, 0.3),
    0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

/* ========== METRICS (Luxe LCD Display) ========== */
div[data-testid="metric-container"] {
  background: 
    linear-gradient(135deg, 
      rgba(61, 74, 58, 0.3) 0%, 
      rgba(61, 74, 58, 0.2) 100%
    );
  border: 2px solid rgba(200, 213, 184, 0.4);
  border-radius: 8px;
  padding: 0.8rem !important;
  box-shadow: 
    inset 0 3px 10px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(200, 213, 184, 0.1),
    0 4px 12px rgba(0, 0, 0, 0.3);
  position: relative;
}

div[data-testid="metric-container"]::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%,
    rgba(200, 213, 184, 0.3) 50%,
    transparent 100%
  );
}

div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
  color: var(--olivetti-lcd-text) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
  text-shadow: 0 0 8px rgba(200, 213, 184, 0.3);
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: var(--accent-gold) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 20px !important;
  font-weight: 700 !important;
  text-shadow: 
    0 0 12px rgba(205, 163, 93, 0.5),
    0 2px 4px rgba(0, 0, 0, 0.3);
}

/* ========== CHECKBOX (Elegant Toggle Switches) ========== */
label[data-baseweb="checkbox"] {
  padding: 0.5rem 0 !important;
  transition: all 0.2s ease;
}

label[data-baseweb="checkbox"]:hover {
  transform: translateX(2px);
}

input[type="checkbox"] {
  accent-color: var(--accent-gold) !important;
  width: 20px !important;
  height: 20px !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  filter: drop-shadow(0 0 4px rgba(205, 163, 93, 0.3));
}

input[type="checkbox"]:checked {
  filter: drop-shadow(0 0 8px rgba(205, 163, 93, 0.5));
}

/* ========== DIVIDERS (Luxe Panel Separators) ========== */
hr {
  border: none !important;
  height: 3px !important;
  background: 
    linear-gradient(
      90deg,
      transparent 0%,
      rgba(205, 163, 93, 0.2) 5%,
      rgba(205, 163, 93, 0.6) 50%,
      rgba(205, 163, 93, 0.2) 95%,
      transparent 100%
    ) !important;
  margin: 2rem 0 !important;
  position: relative;
  box-shadow: 0 2px 8px rgba(205, 163, 93, 0.2);
}

hr::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 40%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 100%
  );
}

/* ========== CAPTIONS (Refined Status Text) ========== */
.stCaption {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.5px !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* ========== SUCCESS/WARNING/ERROR (Premium LCD Messages) ========== */
.stSuccess, .stWarning, .stError, .stInfo {
  font-family: 'IBM Plex Mono', monospace !important;
  border-left: 4px solid !important;
  border-radius: 8px !important;
  padding: 1rem 1.2rem !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
}

.stSuccess {
  background: 
    linear-gradient(135deg, 
      rgba(200, 213, 184, 0.2) 0%, 
      rgba(200, 213, 184, 0.1) 100%
    ) !important;
  border-color: var(--olivetti-lcd-text) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(200, 213, 184, 0.2);
}

.stWarning {
  background: 
    linear-gradient(135deg, 
      rgba(212, 196, 168, 0.2) 0%, 
      rgba(212, 196, 168, 0.1) 100%
    ) !important;
  border-color: var(--accent-primary) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(212, 196, 168, 0.2);
}

.stError {
  background: 
    linear-gradient(135deg, 
      rgba(184, 149, 106, 0.2) 0%, 
      rgba(184, 149, 106, 0.1) 100%
    ) !important;
  border-color: var(--olivetti-bronze) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(184, 149, 106, 0.2);
}

.stInfo {
  background: 
    linear-gradient(135deg, 
      rgba(61, 74, 58, 0.2) 0%, 
      rgba(61, 74, 58, 0.1) 100%
    ) !important;
  border-color: var(--olivetti-lcd) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(61, 74, 58, 0.2);
}

/* ========== SCROLLBAR (Premium Quaderno Theme) ========== */
::-webkit-scrollbar {
  width: 14px;
  height: 14px;
}

::-webkit-scrollbar-track {
  background: rgba(26, 22, 20, 0.6);
  border-radius: 8px;
  box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.5);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #e8dcc8 0%, #cda35d 50%, #b8956a 100%);
  border-radius: 8px;
  border: 3px solid rgba(26, 22, 20, 0.6);
  box-shadow: 
    0 0 8px rgba(205, 163, 93, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #f5f0e8 0%, #e8dcc8 50%, #cda35d 100%);
  box-shadow: 
    0 0 12px rgba(205, 163, 93, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

/* ========== INPUT FIELDS (Refined Controls) ========== */
input[type="text"], input[type="number"], select, textarea:not([data-testid="stTextArea"] textarea) {
  background: rgba(245, 240, 232, 0.08) !important;
  border: 2px solid rgba(212, 196, 168, 0.3) !important;
  border-radius: 6px !important;
  color: var(--text-primary) !important;
  padding: 0.6rem 0.8rem !important;
  font-family: 'IBM Plex Mono', monospace !important;
  transition: all 0.2s ease !important;
}

input[type="text"]:focus, input[type="number"]:focus, select:focus {
  outline: none !important;
  border-color: rgba(205, 163, 93, 0.6) !important;
  box-shadow: 
    0 0 0 3px rgba(205, 163, 93, 0.2),
    0 4px 12px rgba(205, 163, 93, 0.2) !important;
  background: rgba(245, 240, 232, 0.12) !important;
}

/* ========== FILE UPLOADER (Premium Style) ========== */
[data-testid="stFileUploader"] {
  border: 2px dashed rgba(205, 163, 93, 0.4) !important;
  border-radius: 10px !important;
  padding: 1.5rem !important;
  background: rgba(61, 74, 58, 0.1) !important;
  transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"]:hover {
  border-color: rgba(205, 163, 93, 0.7) !important;
  background: rgba(61, 74, 58, 0.15) !important;
  box-shadow: 0 0 20px rgba(205, 163, 93, 0.15);
}

/* ========== SELECTBOX (Elegant Dropdowns) ========== */
[data-baseweb="select"] {
  border-radius: 6px !important;
  background: rgba(245, 240, 232, 0.08) !important;
  border: 2px solid rgba(212, 196, 168, 0.3) !important;
  transition: all 0.2s ease !important;
}

[data-baseweb="select"]:hover {
  border-color: rgba(205, 163, 93, 0.5) !important;
  box-shadow: 0 0 15px rgba(205, 163, 93, 0.15);
}

/* ========== ANIMATIONS ========== */
@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* ========== OLIVETTI BRANDING ACCENT ========== */
.stApp::after {
  content: '';
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 80px;
  height: 80px;
  background: 
    radial-gradient(circle, 
      rgba(205, 163, 93, 0.1) 0%, 
      transparent 70%
    );
  border-radius: 50%;
  pointer-events: none;
  animation: glow-pulse 4s ease-in-out infinite;
  z-index: 1000;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# GLOBALS
# ============================================================
LANES = ["Dialogue", "Narration", "Interiority", "Action"]
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]


ENGINE_STYLES = ["NARRATIVE", "DESCRIPTIVE", "EMOTIONAL", "LYRICAL"]
AUTOSAVE_DIR = "autosave"
AUTOSAVE_PATH = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50MB - Increased from 10MB for larger manuscripts

WORD_RE = re.compile(r"[A-Za-z']+")


# ============================================================
# UTILS
# ============================================================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_text(s: str) -> str:
    t = (s or "").strip()
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _split_paragraphs(text: str) -> List[str]:
    t = _normalize_text(text)
    if not t:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", t, flags=re.MULTILINE) if p.strip()]


def _safe_filename(s: str, fallback: str = "olivetti") -> str:
    s = re.sub(r"[^\w\- ]+", "", (s or "").strip()).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:80] if s else fallback


def _clamp_text(s: str, max_chars: int = 12000) -> str:
    s = s or ""
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 40] + "\n\n… (truncated) …"


# ============================================================
# VECTOR / VOICE VAULT (lightweight, no external deps)
# ============================================================
def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or "")]


@lru_cache(maxsize=1024)
def _hash_vec_cached(text: str, dims: int = 512) -> tuple:
    """Cached version of hash vector computation - returns tuple for hashability"""
    vec = [0.0] * dims
    toks = _tokenize(text)
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        vec[h % dims] += 1.0
    for i, v in enumerate(vec):
        if v > 0:
            vec[i] = 1.0 + math.log(v)
    return tuple(vec)


def _hash_vec(text: str, dims: int = 512) -> List[float]:
    """Compute hash vector with caching for performance"""
    return list(_hash_vec_cached(text, dims))


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
        "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
    }


def rebuild_vectors_in_voice_vault(compact_voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (compact_voices or {}).items():
        created_ts = v.get("created_ts") or now_ts()
        lanes_in = v.get("lanes", {}) or {}
        lanes_out: Dict[str, Any] = {ln: [] for ln in LANES}
        for ln in LANES:
            samples = lanes_in.get(ln, []) or []
            for s in samples:
                txt = _normalize_text(s.get("text", ""))
                if not txt:
                    continue
                lanes_out[ln].append({
                    "ts": s.get("ts") or now_ts(),
                    "text": txt,
                    "vec": _hash_vec(txt),
                })
        out[vname] = {"created_ts": created_ts, "lanes": lanes_out}
    return out


def compact_voice_vault(voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (voices or {}).items():
        lanes_out: Dict[str, Any] = {}
        for ln in LANES:
            samples = (v.get("lanes", {}) or {}).get(ln, []) or []
            lanes_out[ln] = [
                {"ts": s.get("ts"), "text": s.get("text", "")}
                for s in samples
                if (s.get("text") or "").strip()
            ]
        out[vname] = {"created_ts": v.get("created_ts"), "lanes": lanes_out}
    return out


def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in (st.session_state.voices or {}).keys() if k not in ("Voice A", "Voice B")])
    return base + customs


def create_custom_voice(name: str) -> bool:
    n = (name or "").strip()
    if not n:
        return False
    if n in (st.session_state.voices or {}):
        return False
    st.session_state.voices[n] = {"created_ts": now_ts(), "lanes": {ln: [] for ln in LANES}}
    return True


def add_voice_sample(voice_name: str, lane: str, text: str) -> bool:
    vn = (voice_name or "").strip()
    if not vn:
        return False
    lane = lane if lane in LANES else "Narration"
    t = _normalize_text(text)
    if not t:
        return False
    v = (st.session_state.voices or {}).get(vn)
    if not v:
        # auto-create
        create_custom_voice(vn)
        v = st.session_state.voices.get(vn)
    v.setdefault("lanes", {ln: [] for ln in LANES})
    v["lanes"].setdefault(lane, [])
    v["lanes"][lane].append({"ts": now_ts(), "text": t, "vec": _hash_vec(t)})
    # cap per lane (keeps app fast)
    if len(v["lanes"][lane]) > 60:
        v["lanes"][lane] = v["lanes"][lane][-60:]
    st.session_state.voices[vn] = v
    return True


def delete_voice_sample(voice_name: str, lane: str, index_from_end: int = 0) -> bool:
    vn = (voice_name or "").strip()
    v = (st.session_state.voices or {}).get(vn)
    if not v:
        return False
    lane = lane if lane in LANES else "Narration"
    arr = (v.get("lanes", {}) or {}).get(lane, []) or []
    if not arr:
        return False
    idx = len(arr) - 1 - int(index_from_end)
    if idx < 0 or idx >= len(arr):
        return False
    arr.pop(idx)
    v["lanes"][lane] = arr
    st.session_state.voices[vn] = v
    return True


def analyze_style_samples(text: str) -> List[Dict[str, Any]]:
    """
    Analyze text for strongest writing samples based on:
    - Sentence variety and rhythm
    - Vocabulary richness (unique words)
    - Imagery and sensory language
    - Syntactic complexity
    Returns list of highlighted samples with scores.
    """
    if not text or not text.strip():
        return []
    
    # Split into sentences
    import re
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return []
    
    scored_samples = []
    
    for i, sent in enumerate(sentences):
        if len(sent) < 10:  # Skip very short sentences
            continue
            
        words = _tokenize(sent)
        if len(words) < 3:
            continue
        
        # Vocabulary richness (unique words ratio)
        unique_ratio = len(set(words)) / max(len(words), 1)
        
        # Sensory/imagery words
        sensory_words = {"saw", "see", "seen", "looked", "felt", "feel", "heard", "hear", "smelled", "smell", "tasted", "taste",
                        "touch", "sound", "sight", "color", "light", "dark", "bright", "shadow", "whisper", "shout",
                        "warm", "cold", "hot", "cool", "soft", "hard", "rough", "smooth", "bitter", "sweet", "sour"}
        sensory_count = sum(1 for w in words if w.lower() in sensory_words)
        
        # Sentence length variance (prefer medium-length sentences with complexity)
        length_score = 1.0 - abs(len(words) - 15) / 30.0  # Optimal around 15 words
        length_score = max(0.0, min(1.0, length_score))
        
        # Strong verbs (action)
        strong_verbs = ACTION_VERBS
        verb_count = sum(1 for w in words if w.lower() in strong_verbs)
        
        # Thought/interiority depth
        thought_count = sum(1 for w in words if w.lower() in THOUGHT_WORDS)
        
        # Calculate composite score
        score = (
            unique_ratio * 30.0 +          # Vocabulary richness
            sensory_count * 15.0 +         # Sensory language
            length_score * 20.0 +          # Optimal length
            verb_count * 10.0 +            # Action/dynamism
            thought_count * 5.0            # Depth
        )
        
        scored_samples.append({
            "text": sent,
            "score": score,
            "index": i,
            "words": len(words),
            "unique_ratio": unique_ratio,
            "sensory": sensory_count,
            "verbs": verb_count
        })
    
    # Sort by score and return top samples
    scored_samples.sort(key=lambda x: x["score"], reverse=True)
    return scored_samples[:10]  # Top 10 samples


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text for canon checking.
    Returns dict with entity types: characters, locations, dates, objects.
    """
    import re
    
    entities = {
        "characters": [],
        "locations": [],
        "dates": [],
        "objects": []
    }
    
    if not text or not text.strip():
        return entities
    
    # Find capitalized words (potential character names)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
    entities["characters"] = list(set(capitalized))[:20]  # Limit to top 20
    
    # Find day/month/time references
    date_patterns = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                     'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                     'September', 'October', 'November', 'December']
    for pattern in date_patterns:
        if pattern in text:
            entities["dates"].append(pattern)
    
    return entities


def analyze_canon_conformity(draft_text: str) -> List[Dict[str, Any]]:
    """
    Analyze draft against Story Bible for continuity violations.
    Returns list of potential issues with confidence scores.
    """
    if not draft_text or not draft_text.strip():
        return []
    
    issues = []
    
    # Get Story Bible content
    synopsis = (st.session_state.synopsis or "").lower()
    characters_bible = (st.session_state.characters or "").lower()
    world_bible = (st.session_state.world or "").lower()
    outline_bible = (st.session_state.outline or "").lower()
    
    # If Story Bible is empty, no canon to check
    if not any([synopsis, characters_bible, world_bible, outline_bible]):
        return []
    
    # Split draft into paragraphs for analysis
    paragraphs = [p.strip() for p in draft_text.split('\n\n') if p.strip()]
    
    for para_idx, para in enumerate(paragraphs):
        para_lower = para.lower()
        words = _tokenize(para)
        
        # Check for character trait contradictions
        # Look for descriptions that might conflict
        if characters_bible:
            # Eye color check
            eye_colors = ['blue eyes', 'green eyes', 'brown eyes', 'gray eyes', 'grey eyes', 'hazel eyes', 'amber eyes']
            for color in eye_colors:
                if color in para_lower:
                    # Check if Story Bible says different
                    for other_color in eye_colors:
                        if other_color != color and other_color in characters_bible:
                            # Extract character name near the eye color
                            import re
                            match = re.search(r'([A-Z][a-z]+).*?' + color.replace(' ', r'\s+'), para, re.IGNORECASE)
                            if match:
                                char_name = match.group(1)
                                if char_name.lower() in characters_bible:
                                    issues.append({
                                        "type": "character_trait",
                                        "severity": "error",
                                        "confidence": 85,
                                        "paragraph_index": para_idx,
                                        "text_snippet": para[:100],
                                        "issue": f"'{char_name}' has {color} in draft, but Story Bible suggests {other_color}",
                                        "resolution_options": ["Update Story Bible", "Fix Draft", "Ignore"]
                                    })
        
        # Check for dead character mentions
        death_markers = ['died', 'dead', 'killed', 'perished', 'deceased']
        for marker in death_markers:
            if marker in para_lower:
                # Find character name near death marker
                import re
                match = re.search(r'([A-Z][a-z]+).*?' + marker, para, re.IGNORECASE)
                if match:
                    dead_char = match.group(1).lower()
                    # Check if this character appears later in draft
                    later_paras = paragraphs[para_idx + 1:]
                    for later_idx, later_para in enumerate(later_paras, start=para_idx + 1):
                        if dead_char in later_para.lower():
                            # Check if they're doing living things
                            living_verbs = ['said', 'walked', 'ran', 'thought', 'smiled', 'laughed', 'grabbed']
                            if any(verb in later_para.lower() for verb in living_verbs):
                                issues.append({
                                    "type": "continuity",
                                    "severity": "error",
                                    "confidence": 75,
                                    "paragraph_index": later_idx,
                                    "text_snippet": later_para[:100],
                                    "issue": f"'{match.group(1)}' appears active after being marked as {marker}",
                                    "resolution_options": ["Fix Draft", "Ignore"]
                                })
                                break
        
        # Check for timeline contradictions
        if outline_bible:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                if day in para_lower:
                    # Check if outline specifies different day for this event
                    # Look for event keywords in paragraph
                    event_keywords = ['heist', 'meeting', 'battle', 'ceremony', 'wedding', 'funeral', 'attack']
                    for event in event_keywords:
                        if event in para_lower:
                            # Check if outline mentions this event with different day
                            for other_day in days:
                                if other_day != day and event in outline_bible and other_day in outline_bible:
                                    issues.append({
                                        "type": "timeline",
                                        "severity": "warning",
                                        "confidence": 60,
                                        "paragraph_index": para_idx,
                                        "text_snippet": para[:100],
                                        "issue": f"Event '{event}' on {day.title()}, but outline may indicate {other_day.title()}",
                                        "resolution_options": ["Update Outline", "Fix Draft", "Ignore"]
                                    })
        
        # Check for world-building contradictions
        if world_bible:
            # Technology level check
            modern_tech = ['phone', 'computer', 'car', 'internet', 'email', 'television', 'airplane']
            medieval_tech = ['sword', 'horse', 'castle', 'knight', 'dragon', 'magic', 'spell']
            
            has_modern = any(tech in para_lower for tech in modern_tech)
            has_medieval = any(tech in para_lower for tech in medieval_tech)
            
            if has_modern and has_medieval:
                if 'medieval' in world_bible or 'fantasy' in world_bible:
                    issues.append({
                        "type": "world_building",
                        "severity": "warning",
                        "confidence": 70,
                        "paragraph_index": para_idx,
                        "text_snippet": para[:100],
                        "issue": "Modern technology in medieval/fantasy setting (Story Bible suggests period setting)",
                        "resolution_options": ["Update World", "Fix Draft", "Ignore"]
                    })
    
    # Filter out ignored issues
    ignored_flags = st.session_state.get("canon_ignored_flags", [])
    filtered_issues = []
    for issue in issues:
        flag_id = f"{issue['type']}_{issue['paragraph_index']}_{issue['issue'][:30]}"
        if flag_id not in ignored_flags:
            filtered_issues.append(issue)
    
    return filtered_issues


def analyze_voice_conformity(text: str) -> List[Dict[str, Any]]:
    """
    Analyze how well text conforms to active Voice Bible controls.
    Returns list of paragraphs with conformity scores (0-100).
    Higher score = better conformity, lower = more deviation.
    """
    if not text or not text.strip():
        return []
    
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return []
    
    results = []
    
    for idx, para in enumerate(paragraphs):
        words = _tokenize(para)
        if len(words) < 3:
            continue
        
        score = 100.0  # Start at perfect conformity
        issues = []
        
        # Check POV conformity (if technical controls enabled)
        if st.session_state.vb_technical_on:
            pov = st.session_state.pov
            first_person = sum(1 for w in words if w.lower() in ['i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our'])
            third_person = sum(1 for w in words if w.lower() in ['he', 'she', 'they', 'him', 'her', 'them', 'his', 'hers', 'their'])
            
            if pov == "First" and third_person > first_person:
                score -= 20
                issues.append("POV mismatch: too much third-person")
            elif pov in ["Close Third", "Omniscient"] and first_person > third_person * 0.5:
                score -= 20
                issues.append("POV mismatch: too much first-person")
        
        # Check tense conformity (if technical controls enabled)
        if st.session_state.vb_technical_on:
            tense = st.session_state.tense
            past_markers = sum(1 for w in words if w.endswith('ed') or w in ['was', 'were', 'had', 'did'])
            present_markers = sum(1 for w in words if w.endswith('s') and len(w) > 2 or w in ['is', 'are', 'am', 'does', 'do'])
            
            if tense == "Past" and present_markers > past_markers:
                score -= 15
                issues.append("Tense mismatch: too much present tense")
            elif tense == "Present" and past_markers > present_markers:
                score -= 15
                issues.append("Tense mismatch: too much past tense")
        
        # Check style conformity (if style engine enabled)
        if st.session_state.vb_style_on:
            style = st.session_state.writing_style
            
            # LYRICAL expects poetic/sensory language
            if style == "LYRICAL":
                sensory_count = sum(1 for w in words if w.lower() in {
                    "light", "dark", "shadow", "sound", "whisper", "touch", "soft", "rough",
                    "color", "bright", "warm", "cold", "scent", "taste"
                })
                if sensory_count < len(words) * 0.03:  # Less than 3% sensory
                    score -= 15
                    issues.append("Style: needs more sensory/poetic language")
            
            # SPARSE expects brevity
            elif style == "SPARSE":
                avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
                if avg_word_len > 5.5:
                    score -= 15
                    issues.append("Style: words too long for sparse style")
            
            # ORNATE expects complexity
            elif style == "ORNATE":
                avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
                if avg_word_len < 4.5:
                    score -= 15
                    issues.append("Style: needs more elaborate vocabulary")
        
        # Check genre conformity (if genre intelligence enabled)
        if st.session_state.vb_genre_on:
            genre = st.session_state.genre
            
            # NOIR expects hardboiled tone
            if genre == "Noir":
                noir_words = sum(1 for w in words if w.lower() in {
                    "dark", "shadow", "night", "smoke", "rain", "gun", "blood", "dead", "dame"
                })
                if noir_words < 1 and len(words) > 30:
                    score -= 10
                    issues.append("Genre: lacks noir atmosphere")
            
            # HORROR expects tension
            elif genre == "Horror":
                horror_words = sum(1 for w in words if w.lower() in {
                    "fear", "terror", "scream", "blood", "dark", "shadow", "death", "cold", "alone"
                })
                if horror_words < 1 and len(words) > 30:
                    score -= 10
                    issues.append("Genre: lacks horror elements")
        
        # Ensure score stays in bounds
        score = max(0.0, min(100.0, score))
        
        results.append({
            "text": para,
            "score": score,
            "index": idx,
            "words": len(words),
            "issues": issues
        })
    
    return results


def retrieve_exemplars(voice_name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    v = (st.session_state.voices or {}).get(voice_name)
    if not v:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = v.get("lanes", {}).get(lane, []) or []
    if not pool:
        return []
    qv = _hash_vec(query_text)
    scored = [(_cosine(qv, s.get("vec", [])), s.get("text", "")) for s in pool[-140:]]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [txt for score, txt in scored[:k] if score > 0.0 and txt][:k]


def retrieve_mixed_exemplars(voice_name: str, lane: str, query_text: str) -> List[str]:
    lane_ex = retrieve_exemplars(voice_name, lane, query_text, k=2)
    if lane == "Narration":
        return lane_ex if lane_ex else retrieve_exemplars(voice_name, "Narration", query_text, k=3)
    nar_ex = retrieve_exemplars(voice_name, "Narration", query_text, k=1)
    out = lane_ex + [x for x in nar_ex if x not in lane_ex]
    return out[:3]


# ============================================================
# LANE DETECTION (lightweight)
# ============================================================
THOUGHT_WORDS = {
    "think",
    "thought",
    "felt",
    "wondered",
    "realized",
    "remembered",
    "knew",
    "noticed",
    "decided",
    "hoped",
    "feared",
    "wanted",
    "imagined",
    "could",
    "should",
    "would",
}
ACTION_VERBS = {
    "run",
    "ran",
    "walk",
    "walked",
    "grab",
    "grabbed",
    "push",
    "pushed",
    "pull",
    "pulled",
    "slam",
    "slammed",
    "hit",
    "struck",
    "kick",
    "kicked",
    "turn",
    "turned",
    "snap",
    "snapped",
    "dive",
    "dived",
    "duck",
    "ducked",
    "rush",
    "rushed",
    "lunge",
    "lunged",
    "climb",
    "climbed",
    "drop",
    "dropped",
    "throw",
    "threw",
    "fire",
    "fired",
    "aim",
    "aimed",
    "break",
    "broke",
    "shatter",
    "shattered",
    "step",
    "stepped",
    "move",
    "moved",
    "reach",
    "reached",
}


def detect_lane(paragraph: str) -> str:
    p = (paragraph or "").strip()
    if not p:
        return "Narration"

    quote_count = p.count('"') + p.count("“") + p.count("”")
    has_dialogue_punct = p.startswith(("—", "- ", "“", '"'))

    dialogue_score = 0.0
    if quote_count >= 2:
        dialogue_score += 2.5
    if has_dialogue_punct:
        dialogue_score += 1.5

    toks = _tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i", "me", "my", "mine", "myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1:
            interior_score += 2.2

    action_score = 0.0
    if toks:
        verb_hits = sum(1 for t in toks if t in ACTION_VERBS)
        if verb_hits >= 2:
            action_score += 1.6
        if "!" in p:
            action_score += 0.3

    scores = {"Dialogue": dialogue_score, "Interiority": interior_score, "Action": action_score, "Narration": 0.25}
    lane = max(scores.items(), key=lambda kv: kv[1])[0]
    return "Narration" if scores[lane] < 0.9 else lane


def current_lane_from_draft(text: str) -> str:
    paras = _split_paragraphs(text)
    if not paras:
        return "Narration"
    return detect_lane(paras[-1])


# ============================================================
# INTENSITY (GLOBAL AI AGGRESSION KNOB)
# ============================================================
def intensity_profile(x: float) -> str:
    if x <= 0.25:
        return "LOW: conservative, literal, minimal invention, prioritize continuity and clarity."
    if x <= 0.60:
        return "MED: balanced creativity, stronger phrasing, controlled invention within canon."
    if x <= 0.85:
        return "HIGH: bolder choices, richer specificity; still obey canon and lane."
    return "MAX: aggressive originality and voice; still obey canon, no derailments."


def temperature_from_intensity(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    return 0.15 + (x * 0.95)


def _get_voice_bible_summary() -> str:
    """Generate a brief summary of active Voice Bible controls for status display."""
    parts = []
    ai_int = get_ai_intensity_safe()
    
    # AI Intensity is always shown
    if ai_int <= 0.25:
        parts.append("AI:LOW")
    elif ai_int <= 0.60:
        parts.append("AI:MED")
    elif ai_int <= 0.85:
        parts.append("AI:HIGH")
    else:
        parts.append("AI:MAX")
    
    # Show active Voice Bible controls
    if st.session_state.vb_style_on:
        parts.append(f"Style:{st.session_state.writing_style}")
    if st.session_state.vb_genre_on:
        parts.append(f"Genre:{st.session_state.genre}")
    if st.session_state.vb_trained_on and st.session_state.trained_voice != "— None —":
        parts.append(f"Voice:{st.session_state.trained_voice}")
    if st.session_state.vb_match_on:
        parts.append("Match:ON")

    if st.session_state.vb_technical_on:
        parts.append(f"Tech:{st.session_state.pov}/{st.session_state.tense}")
    
    return " • ".join(parts) if len(parts) > 1 else parts[0] if parts else "Defaults"


def _verify_system_integrity() -> Dict[str, bool]:
    """
    ═══════════════════════════════════════════════════════════════
    SYSTEM INTEGRITY CHECK - Verifies all components are connected.
    Run at startup to ensure the spiderweb is fully wired.
    ═══════════════════════════════════════════════════════════════
    """
    checks = {
        "ai_intensity_exists": "ai_intensity" in st.session_state,
        "story_bible_sections": all(k in st.session_state for k in ["synopsis", "genre_style_notes", "world", "characters", "outline"]),
        "voice_bible_controls": all(k in st.session_state for k in ["vb_style_on", "vb_genre_on", "vb_trained_on", "vb_match_on", "vb_technical_on"]),
        "style_banks_exist": "style_banks" in st.session_state,
        "voices_exist": "voices" in st.session_state,
        "project_system": all(k in st.session_state for k in ["projects", "active_bay", "project_id"]),
        "functions_callable": all(callable(f) for f in [
            build_partner_brief, 
            call_openai, 
            partner_action, 
            retrieve_style_exemplars,
            retrieve_mixed_exemplars,
            generate_story_bible_section,
            temperature_from_intensity
        ]),
    }
    return checks


# ============================================================
# PROJECT MODEL
# ============================================================
def _fingerprint_story_bible(sb: Dict[str, str]) -> str:
    parts = [
        (sb.get("synopsis", "") or "").strip(),
        (sb.get("genre_style_notes", "") or "").strip(),
        (sb.get("world", "") or "").strip(),
        (sb.get("characters", "") or "").strip(),
        (sb.get("outline", "") or "").strip(),
    ]
    blob = "\n\n---\n\n".join(parts)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def new_project_payload(title: str) -> Dict[str, Any]:
    ts = now_ts()
    title = title.strip() if title.strip() else "Untitled Project"
    story_bible_id = hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": hashlib.md5(f"{title}|{ts}".encode("utf-8")).hexdigest()[:12],
        "title": title,
        "created_ts": ts,
        "updated_ts": ts,
        "bay": "NEW",
        "draft": "",
        "story_bible_id": story_bible_id,
        "story_bible_created_ts": ts,

        "story_bible_fingerprint": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "voice_bible": {
            "vb_style_on": True,
            "vb_genre_on": True,
            "vb_trained_on": False,
            "vb_match_on": False,
            "vb_technical_on": True,
            "writing_style": "Neutral",
            "genre": "Literary",
            "trained_voice": "— None —",
            "voice_sample": "",
            "style_intensity": 0.6,
            "genre_intensity": 0.6,
            "trained_intensity": 0.7,
            "match_intensity": 0.8,
            "technical_intensity": 0.8,
            "pov": "Close Third",
            "tense": "Past",
            "ai_intensity": 0.75,
        },
        "voices": default_voice_vault(),
        "style_banks": default_style_banks(),
    }


# ============================================================

# ============================================================
# ENGINE STYLE BANKS (project/workspace) — trainable writing styles
# ============================================================
def default_style_banks() -> Dict[str, Any]:
    ts = now_ts()
    return {s: {"created_ts": ts, "lanes": {ln: [] for ln in LANES}} for s in ENGINE_STYLES}


def rebuild_vectors_in_style_banks(banks: Dict[str, Any]) -> Dict[str, Any]:
    src = banks or {}
    out: Dict[str, Any] = {}
    for style in ENGINE_STYLES:
        b = (src.get(style) or {}) if isinstance(src, dict) else {}
        lanes = b.get("lanes") or {}
        new_lanes: Dict[str, List[Dict[str, Any]]] = {}
        for ln in LANES:
            samples = (lanes.get(ln) or []) if isinstance(lanes, dict) else []
            rebuilt: List[Dict[str, Any]] = []
            for it in samples:
                if isinstance(it, str):
                    t = it.strip()
                    if not t:
                        continue
                    rebuilt.append({"ts": now_ts(), "text": t, "vec": _hash_vec(t)})
                    continue
                if not isinstance(it, dict):
                    continue
                t = (it.get("text") or "").strip()
                if not t:
                    continue
                vec = it.get("vec") if isinstance(it.get("vec"), list) else None
                if not vec:
                    vec = _hash_vec(t)
                rebuilt.append({"ts": it.get("ts") or now_ts(), "text": t, "vec": vec})
            new_lanes[ln] = rebuilt
        out[style] = {"created_ts": b.get("created_ts") or now_ts(), "lanes": new_lanes}
    return out if out else default_style_banks()


def compact_style_banks(banks: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(banks, dict):
        return default_style_banks()
    out: Dict[str, Any] = {}
    for style in ENGINE_STYLES:
        b = banks.get(style) or {}
        lanes = b.get("lanes") or {}
        c_lanes: Dict[str, List[Dict[str, Any]]] = {}
        for ln in LANES:
            ss = (lanes.get(ln) or []) if isinstance(lanes, dict) else []
            cleaned: List[Dict[str, Any]] = []
            for it in ss:
                if not isinstance(it, dict):
                    continue
                t = (it.get("text") or "").strip()
                if not t:
                    continue
                cleaned.append({"ts": it.get("ts") or now_ts(), "text": _clamp_text(t, 9000)})
            c_lanes[ln] = cleaned
        out[style] = {"created_ts": b.get("created_ts") or now_ts(), "lanes": c_lanes}
    return out


def add_style_samples(style: str, lane: str, raw_text: str, split_mode: str = "Paragraphs", cap_per_lane: int = 250) -> int:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return 0
    lane = lane if lane in LANES else "Narration"
    t = _normalize_text(raw_text)
    if not t.strip():
        return 0

    parts = _split_paragraphs(t) if split_mode == "Paragraphs" else [t.strip()]
    parts = [p for p in parts if len(p.strip()) >= 40]

    sb = st.session_state.get("style_banks")
    if not isinstance(sb, dict) or style not in sb:
        sb = rebuild_vectors_in_style_banks(default_style_banks())
        st.session_state.style_banks = sb

    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    lane_list = list((lanes.get(lane) or [])) if isinstance(lanes, dict) else []

    added = 0
    for p in parts:
        p = _clamp_text(p.strip(), 9000)
        lane_list.append({"ts": now_ts(), "text": p, "vec": _hash_vec(p)})
        added += 1

    # cap: keep newest
    lane_list = lane_list[-cap_per_lane:]
    lanes[lane] = lane_list
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb
    return added


def delete_last_style_sample(style: str, lane: str) -> bool:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return False
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or {}
    bank = (sb.get(style) or {})
    lanes = bank.get("lanes") or {}
    lane_list = (lanes.get(lane) or [])
    if not lane_list:
        return False
    lane_list.pop()
    lanes[lane] = lane_list
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb
    return True


def clear_style_lane(style: str, lane: str) -> None:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks())
    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    lanes[lane] = []
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb


def retrieve_style_exemplars(style: str, lane: str, query: str, k: int = 2) -> List[str]:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return []
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or {}
    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    pool = (lanes.get(lane) or [])
    if not pool:
        # fallback: all lanes pooled
        pool = []
        for ln in LANES:
            pool.extend(lanes.get(ln) or [])
    if not pool:
        return []
    # favor newest slice for speed
    pool = pool[-160:]
    qv = _hash_vec(query or "")
    scored = []
    for it in pool:
        if not isinstance(it, dict):
            continue
        vec = it.get("vec")
        if not isinstance(vec, list):
            continue
        scored.append((_cosine(qv, vec), it.get("text") or ""))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = [t.strip() for _, t in scored[: max(0, k)] if (t or "").strip()]
    return out


_ENGINE_STYLE_GUIDE = {
    "NARRATIVE": "Narrative clarity, clean cause→effect, confident pacing. Prioritize story logic and readability.",
    "DESCRIPTIVE": "Sensory precision, spatial clarity, vivid concrete nouns, controlled detail density (no purple bloat).",
    "EMOTIONAL": "Interior depth, subtext, emotional specificity. Show the feeling through behavior, sensation, and thought.",
    "LYRICAL": "Rhythm, musical syntax, image-forward language, elegant metaphor with restraint. Make prose sing without obscuring meaning.",
}


def engine_style_directive(style: str, intensity: float, lane: str) -> str:
    style = (style or "").strip().upper()
    base = _ENGINE_STYLE_GUIDE.get(style, "")
    x = float(intensity)
    if x <= 0.33:
        mod = "Keep it subtle and controlled. Minimal overt stylization."
    elif x <= 0.66:
        mod = "Medium stylization. Let the style clearly shape diction and cadence."
    else:
        mod = "High stylization. Strong stylistic fingerprint, but still professional and coherent."
    return f"{base}\\nLane: {lane}\\n{mod}"


# STORY BIBLE WORKSPACE (pre-project creation space)
# ============================================================
def default_story_bible_workspace() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "workspace_story_bible_id": hashlib.md5(f"wsb|{ts}".encode("utf-8")).hexdigest()[:12],
        "workspace_story_bible_created_ts": ts,
        "title": "",
        "draft": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "voice_sample": "",
        "ai_intensity": 0.75,
        "voices": default_voice_vault(),
        "style_banks": default_style_banks(),
    }


def in_workspace_mode() -> bool:
    return (st.session_state.active_bay == "NEW") and (st.session_state.project_id is None)


def save_workspace_from_session() -> None:
    w = st.session_state.sb_workspace or default_story_bible_workspace()
    w["title"] = st.session_state.get("workspace_title", w.get("title", ""))
    w["draft"] = st.session_state.main_text
    w["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    w["voice_sample"] = st.session_state.voice_sample
    w["ai_intensity"] = float(st.session_state.ai_intensity)
    w["voices"] = compact_voice_vault(st.session_state.voices)
    w["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))
    st.session_state.sb_workspace = w


def set_ai_intensity(val: float) -> None:
    """Safely set ai_intensity with bounds checking."""
    try:
        val = float(val)
        # Ensure value is within valid range [0.0, 1.0]
        val = max(0.0, min(1.0, val))
        st.session_state["ai_intensity"] = val
    except (ValueError, TypeError):
        logger.warning(f"Invalid AI intensity value: {val}, defaulting to 0.75")
        st.session_state["ai_intensity"] = 0.75


def load_workspace_into_session() -> None:
    w = st.session_state.sb_workspace or default_story_bible_workspace()
    sb = w.get("story_bible", {}) or {}
    st.session_state.project_id = None
    st.session_state.project_title = "—"
    st.session_state.main_text = w.get("draft", "") or ""
    st.session_state.synopsis = sb.get("synopsis", "") or ""
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "") or ""
    st.session_state.world = sb.get("world", "") or ""
    st.session_state.characters = sb.get("characters", "") or ""
    st.session_state.outline = sb.get("outline", "") or ""
    st.session_state.voice_sample = w.get("voice_sample", "") or ""
    set_ai_intensity(float(w.get("ai_intensity", 0.75)))
    st.session_state.voices = rebuild_vectors_in_voice_vault(w.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True
    st.session_state.style_banks = rebuild_vectors_in_style_banks(w.get("style_banks", default_style_banks()))
    st.session_state.workspace_title = w.get("title", "") or ""


def reset_workspace_story_bible(keep_templates: bool = True) -> None:
    old = st.session_state.sb_workspace or default_story_bible_workspace()
    neww = default_story_bible_workspace()
    if keep_templates:
        neww["voice_sample"] = old.get("voice_sample", "")
        neww["ai_intensity"] = float(old.get("ai_intensity", 0.75))
        neww["voices"] = old.get("voices", default_voice_vault())
        neww["style_banks"] = old.get("style_banks", default_style_banks())
    st.session_state.sb_workspace = neww
    if in_workspace_mode():
        load_workspace_into_session()


# ============================================================
# SESSION INIT
# ============================================================
def init_state() -> None:
    defaults: Dict[str, Any] = {
        "active_bay": "NEW",
        "projects": {},
        "active_project_by_bay": {b: None for b in BAYS},
        "sb_workspace": default_story_bible_workspace(),
        "workspace_title": "",
        "project_id": None,
        "project_title": "—",
        "autosave_time": None,
        "last_action": "—",
        "voice_status": "—",
        "main_text": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",
        "junk": "",
        "tool_output": "",
        "pending_action": None,
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_technical_on": True,
        "writing_style": "Neutral",
        "genre": "Literary",
        "trained_voice": "— None —",
        "voice_sample": "",
        "style_intensity": 0.6,
        "genre_intensity": 0.6,
        "trained_intensity": 0.7,
        "match_intensity": 0.8,
        "technical_intensity": 0.8,
        "pov": "Close Third",
        "tense": "Past",
        "ai_intensity": 0.75,
        "voices": {},
        "voices_seeded": False,
        "style_banks": rebuild_vectors_in_style_banks(default_style_banks()),
        "last_saved_digest": "",
        "analyzed_style_samples": [],
        "voice_heatmap_data": [],
        "show_voice_heatmap": False,
        "canon_guardian_on": False,
        "canon_issues": [],
        "canon_ignored_flags": [],

        # Undo/Redo System
        "undo_history": [],
        "undo_position": -1,
        "max_undo_states": 50,

        # internal UI helpers (not widgets)
        "ui_notice": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
    # Initialize performance monitoring and rate limiting
    if "perf_monitor" not in st.session_state:
        from performance import PerformanceMonitor, RateLimiter
        st.session_state.perf_monitor = PerformanceMonitor()
        st.session_state.rate_limiter = RateLimiter(calls_per_minute=10)
        logger.info("Performance monitoring and rate limiting initialized")


init_state()



# ============================================================
# PROJECT <-> SESSION SYNC
# ============================================================
def load_project_into_session(pid: str) -> None:
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return

    st.session_state.project_id = pid
    st.session_state.project_title = p.get("title", "Untitled Project")
    st.session_state.main_text = p.get("draft", "")

    sb = p.get("story_bible", {}) or {}
    st.session_state.synopsis = sb.get("synopsis", "")
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "")
    st.session_state.world = sb.get("world", "")
    st.session_state.characters = sb.get("characters", "")
    st.session_state.outline = sb.get("outline", "")

    vb = p.get("voice_bible", {}) or {}
    for k in [
        "vb_style_on",
        "vb_genre_on",
        "vb_trained_on",
        "vb_match_on",
        "vb_technical_on",
        "writing_style",
        "genre",
        "trained_voice",
        "voice_sample",
        "style_intensity",
        "genre_intensity",
        "trained_intensity",
        "match_intensity",
        "technical_intensity",
        "pov",
        "tense",
        "ai_intensity",
    ]:
        if k in vb:
            st.session_state[k] = vb[k]

    # No lock system - all editable

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True
    
    # Load heatmap data per-project (restore analysis state)
    st.session_state.voice_heatmap_data = p.get("voice_heatmap_data", [])
    st.session_state.show_voice_heatmap = p.get("show_voice_heatmap", False)
    st.session_state.canon_issues = p.get("canon_issues", [])
    st.session_state.canon_guardian_on = p.get("canon_guardian_on", False)
    
    # Auto-analyze if heatmap was previously enabled for this project
    if st.session_state.show_voice_heatmap and st.session_state.main_text:
        try:
            st.session_state.voice_heatmap_data = analyze_voice_conformity(st.session_state.main_text)
        except Exception:
            pass  # Silent fail - user can manually re-analyze


def save_session_into_project() -> None:
    pid = st.session_state.project_id
    if not pid:
        return
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return

    p["updated_ts"] = now_ts()
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    p["voice_bible"] = {
        "vb_style_on": st.session_state.vb_style_on,
        "vb_genre_on": st.session_state.vb_genre_on,
        "vb_trained_on": st.session_state.vb_trained_on,
        "vb_match_on": st.session_state.vb_match_on,
        "vb_technical_on": st.session_state.vb_technical_on,
        "writing_style": st.session_state.writing_style,
        "genre": st.session_state.genre,
        "trained_voice": st.session_state.trained_voice,
        "voice_sample": st.session_state.voice_sample,
        "style_intensity": st.session_state.style_intensity,
        "genre_intensity": st.session_state.genre_intensity,
        "trained_intensity": st.session_state.trained_intensity,
        "match_intensity": st.session_state.match_intensity,
        "technical_intensity": st.session_state.technical_intensity,
        "pov": st.session_state.pov,
        "tense": st.session_state.tense,
        "ai_intensity": float(st.session_state.ai_intensity),
    }
    # No lock system - all editable
    p["voices"] = compact_voice_vault(st.session_state.voices)
    p["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))
    
    # Save heatmap data per-project
    p["voice_heatmap_data"] = st.session_state.get("voice_heatmap_data", [])
    p["show_voice_heatmap"] = st.session_state.get("show_voice_heatmap", False)
    p["canon_issues"] = st.session_state.get("canon_issues", [])
    p["canon_guardian_on"] = st.session_state.get("canon_guardian_on", False)
    
    # keep fingerprint up to date
    try:
        p["story_bible_fingerprint"] = _fingerprint_story_bible(p["story_bible"])
    except Exception:
        pass


def list_projects_in_bay(bay: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for pid, p in (st.session_state.projects or {}).items():
        if isinstance(p, dict) and p.get("bay") == bay:
            items.append((pid, p.get("title", "Untitled")))
    items.sort(key=lambda x: (x[1] or "").lower())
    return items


def ensure_bay_has_active_project(bay: str) -> None:
    pid = (st.session_state.active_project_by_bay or {}).get(bay)
    if pid and pid in (st.session_state.projects or {}) and (st.session_state.projects[pid].get("bay") == bay):
        return
    items = list_projects_in_bay(bay)
    st.session_state.active_project_by_bay[bay] = items[0][0] if items else None


def switch_bay(target_bay: str) -> None:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()

    st.session_state.active_bay = target_bay
    ensure_bay_has_active_project(target_bay)
    pid = st.session_state.active_project_by_bay.get(target_bay)

    if pid:
        load_project_into_session(pid)
        st.session_state.voice_status = f"{target_bay}: {st.session_state.project_title}"
    else:
        st.session_state.project_id = None
        st.session_state.project_title = "—"
        if target_bay == "NEW":
            load_workspace_into_session()
            st.session_state.voice_status = "NEW: (Story Bible workspace)"
        else:
            st.session_state.main_text = ""
            st.session_state.synopsis = ""
            st.session_state.genre_style_notes = ""
            st.session_state.world = ""
            st.session_state.characters = ""
            st.session_state.outline = ""
            st.session_state.voice_sample = ""
            set_ai_intensity(0.75)
            st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
            st.session_state.voices_seeded = True
            st.session_state.voice_status = f"{target_bay}: (empty)"

    st.session_state.last_action = f"Bay → {target_bay}"


def create_project_from_current_bible(title: str) -> str:
    title = title.strip() if title.strip() else f"New Project {now_ts()}"
    source = "workspace" if in_workspace_mode() else "clone"

    source_story_bible_id = None
    source_story_bible_created_ts = None
    if source == "workspace":
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        source_story_bible_id = w.get("workspace_story_bible_id")
        source_story_bible_created_ts = w.get("workspace_story_bible_created_ts")
    else:
        pid = st.session_state.project_id
        if pid and pid in (st.session_state.projects or {}):
            source_story_bible_id = st.session_state.projects[pid].get("story_bible_id")

    p = new_project_payload(title)
    p["bay"] = "NEW"
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }

    if source == "workspace" and source_story_bible_id:
        p["story_bible_id"] = source_story_bible_id
        if source_story_bible_created_ts:
            p["story_bible_created_ts"] = source_story_bible_created_ts

    p["story_bible_fingerprint"] = _fingerprint_story_bible(p["story_bible"])

    # Voice templates + intensity
    p["voice_bible"]["voice_sample"] = st.session_state.voice_sample
    p["voice_bible"]["ai_intensity"] = float(st.session_state.ai_intensity)
    p["voices"] = compact_voice_vault(st.session_state.voices)
    p["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    if source == "workspace":
        reset_workspace_story_bible(keep_templates=True)

    return p["id"]


def promote_project(pid: str, to_bay: str) -> None:
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return
    p["bay"] = to_bay
    p["updated_ts"] = now_ts()


def next_bay(bay: str) -> Optional[str]:
    if bay == "NEW":
        return "ROUGH"
    if bay == "ROUGH":
        return "EDIT"
    if bay == "EDIT":
        return "FINAL"
    return None


# ============================================================
# AUTOSAVE (atomic + backup)
# ============================================================
def _payload() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-prod-stable-v1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "sb_workspace": st.session_state.sb_workspace,
        "projects": st.session_state.projects,
    }


def _digest(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


@safe_execute("Autosave", fallback_value=None, show_error=False)
def save_all_to_disk(force: bool = False) -> None:
    """Autosave state to disk with atomic write and rotating backups."""
    os.makedirs(AUTOSAVE_DIR, exist_ok=True)
    payload = _payload()
    dig = _digest(payload)
    
    if (not force) and dig == st.session_state.last_saved_digest:
        logger.debug("Skipping autosave - no changes detected")
        return

    tmp_path = AUTOSAVE_PATH + ".tmp"
    
    # Create rotating backups (keep last 5)
    try:
        if os.path.exists(AUTOSAVE_PATH):
            import shutil
            
            # Rotate existing backups
            for i in range(4, 0, -1):
                old_bak = f"{AUTOSAVE_PATH}.bak{i}"
                new_bak = f"{AUTOSAVE_PATH}.bak{i+1}"
                if os.path.exists(old_bak):
                    shutil.move(old_bak, new_bak)
            
            # Create new backup
            shutil.copy2(AUTOSAVE_PATH, f"{AUTOSAVE_PATH}.bak1")
            logger.debug("Created rotating backup")
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")

    # Atomic write
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, AUTOSAVE_PATH)

    st.session_state.last_saved_digest = dig
    logger.info(f"Autosave completed ({len(st.session_state.projects)} projects, {len(payload)} bytes)")


@safe_execute("Load autosave", show_error=True)
def load_all_from_disk() -> None:
    main_path = AUTOSAVE_PATH
    
    # Try loading from main file and rotating backups
    backup_paths = [main_path] + [f"{AUTOSAVE_PATH}.bak{i}" for i in range(1, 6)]

    def _boot_new() -> None:
        st.session_state.sb_workspace = st.session_state.get("sb_workspace") or default_story_bible_workspace()
        switch_bay("NEW")

    # Check if any autosave exists
    if not any(os.path.exists(p) for p in backup_paths):
        logger.info("No autosave found, booting fresh workspace")
        _boot_new()
        return

    payload = None
    loaded_from = "primary"
    last_err = None
    
    # Try loading from main file, then backups in order
    for i, path in enumerate(backup_paths):
        if not os.path.exists(path):
            continue
        
        label = "primary" if i == 0 else f"backup{i}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            loaded_from = label
            logger.info(f"Successfully loaded from {label} autosave: {path}")
            break
        except Exception as e:
            last_err = e
            logger.warning(f"Failed to load {label} autosave: {e}")
            payload = None

    if payload is None:
        logger.error(f"All autosave loads failed. Last error: {last_err}")
        st.session_state.voice_status = f"⚠️ All autosave files corrupted. Starting fresh."
        _boot_new()
        return

    try:
        projs = payload.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = payload.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            for b in BAYS:
                apbb.setdefault(b, None)
            st.session_state.active_project_by_bay = apbb

        w = payload.get("sb_workspace")
        if isinstance(w, dict) and w.get("workspace_story_bible_id"):
            st.session_state.sb_workspace = w
        else:
            st.session_state.sb_workspace = default_story_bible_workspace()

        # Migration guards
        for _, p in (st.session_state.projects or {}).items():
            if not isinstance(p, dict):
                continue
            ts = p.get("created_ts") or now_ts()
            title = p.get("title", "Untitled")
            p.setdefault("story_bible_id", hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12])
            p.setdefault("story_bible_created_ts", ts)

            # No lock system - all editable
            p.setdefault("voices", default_voice_vault())
            p.setdefault("style_banks", default_style_banks())
            if "story_bible_fingerprint" not in p:
                try:
                    p["story_bible_fingerprint"] = _fingerprint_story_bible(p.get("story_bible", {}) or {})
                except Exception:
                    p["story_bible_fingerprint"] = ""

        ab = payload.get("active_bay", "NEW")
        if ab not in BAYS:
            ab = "NEW"
        st.session_state.active_bay = ab

        ensure_bay_has_active_project(ab)
        pid = st.session_state.active_project_by_bay.get(ab)
        if pid:
            load_project_into_session(pid)
        else:
            if ab == "NEW":
                load_workspace_into_session()
                st.session_state.voice_status = "NEW: (Story Bible workspace)"
            else:
                switch_bay(ab)

        saved_at = (payload.get("meta", {}) or {}).get("saved_at", "")
        src = "autosave" if loaded_from == "primary" else "backup autosave"
        st.session_state.voice_status = f"Loaded {src} ({saved_at})."
        st.session_state.last_saved_digest = _digest(_payload())
        logger.info(f"Successfully initialized workspace with {len(st.session_state.projects)} projects")
    except Exception as e:
        logger.error(f"Failed to process loaded payload: {e}\n{traceback.format_exc()}")
        st.session_state.voice_status = f"Load warning: {e}"
        _boot_new()


if "did_load_autosave" not in st.session_state:
    st.session_state.did_load_autosave = True
    load_all_from_disk()


def push_undo_state() -> None:
    """Capture current main_text state to undo history before making changes."""
    current_text = st.session_state.main_text or ""
    history = st.session_state.undo_history
    position = st.session_state.undo_position
    
    # If we're not at the end of history, truncate future states
    if position < len(history) - 1:
        history = history[:position + 1]
        st.session_state.undo_history = history
    
    # Don't save if text hasn't changed
    if history and position >= 0 and history[position] == current_text:
        return
    
    # Add new state
    history.append(current_text)
    
    # Limit history size
    max_states = st.session_state.max_undo_states
    if len(history) > max_states:
        history = history[-max_states:]
        st.session_state.undo_history = history
    
    st.session_state.undo_position = len(history) - 1


def autosave_with_undo() -> None:
    """Autosave wrapper that captures undo state on text changes."""
    # Only push undo state if this is a manual edit (text changed from last saved state)
    if "last_text_for_undo" not in st.session_state:
        st.session_state.last_text_for_undo = ""
    
    current = st.session_state.main_text or ""
    if current != st.session_state.last_text_for_undo:
        push_undo_state()
        st.session_state.last_text_for_undo = current
    
    autosave()


def undo() -> bool:
    """Undo to previous state. Returns True if successful."""
    history = st.session_state.undo_history
    position = st.session_state.undo_position
    
    if position <= 0:
        st.session_state.voice_status = "Nothing to undo"
        return False
    
    # Move back in history
    st.session_state.undo_position = position - 1
    st.session_state.main_text = history[st.session_state.undo_position]
    st.session_state.voice_status = f"Undo ({position} steps available)"
    autosave()
    return True


def redo() -> bool:
    """Redo to next state. Returns True if successful."""
    history = st.session_state.undo_history
    position = st.session_state.undo_position
    
    if position >= len(history) - 1:
        st.session_state.voice_status = "Nothing to redo"
        return False
    
    # Move forward in history
    st.session_state.undo_position = position + 1
    st.session_state.main_text = history[st.session_state.undo_position]
    st.session_state.voice_status = f"Redo ({len(history) - position - 1} steps available)"
    autosave()
    return True


def autosave() -> None:
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    
    # Save chapter content if in chapter mode
    if st.session_state.active_bay in ["ROUGH", "EDIT", "FINAL"] and st.session_state.project_id:
        proj = st.session_state.projects.get(st.session_state.project_id)
        if proj and "chapters" in proj and "active_chapter" in proj:
            active_chapter = proj["active_chapter"]
            if active_chapter in proj["chapters"]:
                proj["chapters"][active_chapter]["content"] = st.session_state.main_text
    
    save_all_to_disk()


# ============================================================
# EXPORT FUNCTIONS
# ============================================================
def export_as_txt(content: str, title: str = "Untitled") -> bytes:
    """Export text content as .txt file."""
    return content.encode('utf-8')


def export_as_docx(content: str, title: str = "Untitled") -> bytes:
    """Export text content as .docx file."""
    if not DOCX_AVAILABLE:
        raise OlivettiError("DOCX export requires python-docx. Install with: pip install python-docx")
    
    doc = Document()
    
    # Add title
    heading = doc.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add content paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            p = doc.add_paragraph(para.strip())
            # Set font
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)
    
    # Save to bytes
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def export_as_pdf(content: str, title: str = "Untitled") -> bytes:
    """Export text content as .pdf file."""
    if not PDF_AVAILABLE:
        raise OlivettiError("PDF export requires fpdf2. Install with: pip install fpdf2")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    
    # Content
    pdf.set_font('Arial', '', 12)
    
    # Split into paragraphs and encode properly
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            # Replace problematic characters
            clean_para = para.strip().replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
            clean_para = clean_para.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, clean_para)
            pdf.ln(4)
    
    return pdf.output(dest='S').encode('latin-1')


def get_export_content() -> Tuple[str, str]:
    """Get content and title for export based on current context."""
    if st.session_state.active_bay in ["ROUGH", "EDIT", "FINAL"] and st.session_state.project_id:
        # Chapter mode - export current chapter
        proj = st.session_state.projects.get(st.session_state.project_id)
        if proj:
            title = f"{proj.get('title', 'Untitled')} - Chapter {proj.get('active_chapter', '1')}"
            content = st.session_state.main_text or ""
            return content, title
    
    # Default - export main text
    title = st.session_state.project_title if st.session_state.project_title != "—" else "Untitled"
    content = st.session_state.main_text or ""
    return content, title


def export_full_manuscript() -> Tuple[str, str]:
    """Export all chapters as one document."""
    if st.session_state.project_id:
        proj = st.session_state.projects.get(st.session_state.project_id)
        if proj and "chapters" in proj:
            title = proj.get('title', 'Untitled')
            chapters = proj["chapters"]
            
            parts = []
            for ch_num in sorted(chapters.keys(), key=lambda x: int(x)):
                ch = chapters[ch_num]
                parts.append(f"Chapter {ch_num}")
                parts.append("="*50)
                parts.append(ch.get("content", ""))
                parts.append("\n\n")
            
            return "\n\n".join(parts), f"{title} - Full Manuscript"
    
    return get_export_content()


# ============================================================
# IMPORT / EXPORT
# ============================================================
@safe_execute("File upload", fallback_value=("", ""), show_error=True)
def _read_uploaded_text(uploaded) -> Tuple[str, str]:
    """Read .txt/.md/.docx from Streamlit UploadedFile with validation."""
    if uploaded is None:
        return "", ""
    
    name = getattr(uploaded, "name", "") or ""
    raw = uploaded.getvalue()
    
    if raw is None:
        logger.warning(f"Upload failed: no data in {name}")
        return "", name
    
    if len(raw) > MAX_UPLOAD_BYTES:
        logger.warning(f"Upload rejected: {name} exceeds {MAX_UPLOAD_BYTES} bytes")
        raise DataValidationError(f"File too large: {name} ({len(raw)} bytes). Max: {MAX_UPLOAD_BYTES} bytes")
    
    ext = os.path.splitext(name.lower())[1]
    logger.info(f"Processing upload: {name} ({len(raw)} bytes, {ext})")

    if ext in (".txt", ".md", ".markdown", ".text", ""):
        try:
            content = raw.decode("utf-8")
            logger.info(f"Decoded text file: {len(content)} chars")
            return content, name
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed, trying with errors=ignore")
            return raw.decode("utf-8", errors="ignore"), name

    if ext == ".docx":
        if not DOCX_AVAILABLE:
            raise DataValidationError("DOCX support not available. Install python-docx (pip install python-docx).")
        try:
            doc = Document(BytesIO(raw))
            parts = []
            for p in doc.paragraphs:
                t = (p.text or "").strip()
                if t:
                    parts.append(t)
            result = "\n\n".join(parts)
            logger.info(f"Extracted from DOCX: {len(result)} chars, {len(parts)} paragraphs")
            return result, name
        except Exception as e:
            logger.warning(f"DOCX extraction failed: {e}, trying fallback")
            try:
                return raw.decode("utf-8", errors="ignore"), name
            except Exception:
                return "", name

    # Unknown extension - try as text
    try:
        content = raw.decode("utf-8", errors="ignore")
        logger.info(f"Decoded unknown file type as text: {len(content)} chars")
        return content, name
    except Exception as e:
        logger.error(f"Failed to decode {name}: {e}")
        return "", name


def _sb_sections_from_text_heuristic(text: str) -> Dict[str, str]:
    t = _normalize_text(text)
    if not t:
        return {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""}

    heading_map = {
        "synopsis": ["synopsis", "premise", "logline"],
        "genre_style_notes": ["genre", "style", "tone", "voice"],
        "world": ["world", "setting", "lore"],
        "characters": ["characters", "cast"],
        "outline": ["outline", "beats", "plot", "structure"],
    }

    lines = t.splitlines()
    buckets = {k: [] for k in heading_map.keys()}
    current = None

    def _match_heading(line: str) -> Optional[str]:
        l = re.sub(r"^[#\-\*\s]+", "", (line or "").strip()).lower()
        l = re.sub(r"[:\-\s]+$", "", l)
        for key, aliases in heading_map.items():
            if any(l == a or l.startswith(a + " ") for a in aliases):
                return key
        return None

    for line in lines:
        key = _match_heading(line)
        if key:
            current = key
            continue
        if current:
            buckets[current].append(line)
        else:
            buckets["synopsis"].append(line)

    return {k: _normalize_text("\n".join(v)) for k, v in buckets.items()}


def _extract_json_object(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    s2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE | re.MULTILINE)
    m = re.search(r"\{.*\}", s2, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def story_bible_markdown(title: str, sb: Dict[str, str], meta: Dict[str, Any]) -> str:
    t = title or "Untitled"

    def sec(h: str, k: str) -> str:
        body = (sb.get(k, "") or "").strip()
        return f"## {h}\n\n{body}\n" if body else f"## {h}\n\n\n"

    front = f"# Story Bible — {t}\n\n- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n"
    return front + "\n".join(
        [
            sec("Synopsis", "synopsis"),
            sec("Genre / Style Notes", "genre_style_notes"),
            sec("World", "world"),
            sec("Characters", "characters"),
            sec("Outline", "outline"),
        ]
    )


def draft_markdown(title: str, draft: str, meta: Dict[str, Any]) -> str:
    t = title or "Untitled"
    front = f"# Draft — {t}\n\n- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n---\n\n"
    return front + (draft or "")


def make_project_bundle(pid: str) -> Dict[str, Any]:
    p = (st.session_state.projects or {}).get(pid, {}) or {}
    return {"meta": {"exported_at": now_ts(), "type": "project_bundle", "version": "1"}, "project": p}


def make_library_bundle() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()
    return {
        "meta": {"exported_at": now_ts(), "type": "library_bundle", "version": "1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "sb_workspace": st.session_state.sb_workspace,
        "projects": st.session_state.projects,
    }


def _new_pid_like(seed: str) -> str:
    return hashlib.md5(f"{seed}|{now_ts()}".encode("utf-8")).hexdigest()[:12]


def import_project_bundle(bundle: Dict[str, Any], target_bay: str = "NEW", rename: str = "") -> Optional[str]:
    if not isinstance(bundle, dict):
        return None
    proj = bundle.get("project")
    if not isinstance(proj, dict):
        return None

    pid = str(proj.get("id") or _new_pid_like("import"))
    if pid in (st.session_state.projects or {}):
        pid = _new_pid_like(pid)

    proj = json.loads(json.dumps(proj))
    proj["id"] = pid
    if rename.strip():
        proj["title"] = rename.strip()
    if target_bay in BAYS:
        proj["bay"] = target_bay
    proj["updated_ts"] = now_ts()

    ts = proj.get("created_ts") or now_ts()
    title = proj.get("title", "Untitled")
    proj.setdefault("story_bible_id", hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12])
    proj.setdefault("story_bible_created_ts", ts)

    # No lock system - all editable
    proj.setdefault("voices", default_voice_vault())
    proj.setdefault("style_banks", default_style_banks())
    proj.setdefault("story_bible_fingerprint", "")

    st.session_state.projects[pid] = proj
    st.session_state.active_project_by_bay[proj.get("bay", "NEW")] = pid
    return pid


def import_library_bundle(bundle: Dict[str, Any]) -> int:
    if not isinstance(bundle, dict):
        return 0
    projs = bundle.get("projects")
    if not isinstance(projs, dict):
        return 0
    imported = 0
    for _, proj in projs.items():
        if not isinstance(proj, dict):
            continue
        pid = import_project_bundle({"project": proj}, target_bay=proj.get("bay", "NEW"), rename="")
        if pid:
            imported += 1

    w = bundle.get("sb_workspace")
    if isinstance(w, dict) and w.get("workspace_story_bible_id"):
        cur = st.session_state.sb_workspace or default_story_bible_workspace()
        cur_sb = (cur.get("story_bible", {}) or {})
        cur_empty = not any((cur_sb.get(k, "") or "").strip() for k in ["synopsis", "genre_style_notes", "world", "characters", "outline"])
        if cur_empty:
            st.session_state.sb_workspace = w
    return imported


def _bundle_summary(obj: Dict[str, Any]) -> str:
    """Return a short human-readable summary of a bundle for UI feedback."""
    meta = obj.get("meta") if isinstance(obj, dict) else {}
    btype = (meta or {}).get("type", "unknown")
    if btype == "library_bundle":
        projs = obj.get("projects") if isinstance(obj.get("projects"), dict) else {}
        return f"Library bundle • {len(projs)} project(s)"
    if btype == "project_bundle":
        p = obj.get("project") or {}
        title = p.get("title", "Untitled") if isinstance(p, dict) else "Untitled"
        return f"Project bundle • {title}"
    if obj.get("projects"):
        return "Library bundle (no meta)"
    if obj.get("project"):
        return "Project bundle (no meta)"
    return "Unrecognized bundle"


# ============================================================
# JUNK DRAWER COMMANDS
# ============================================================
CMD_FIND = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)


def _run_find(term: str) -> str:
    term = (term or "").strip()
    if not term:
        return "Find: missing search term. Use /find: word"

    def _hits(label: str, text: str) -> List[str]:
        lines = (text or "").splitlines()
        out = []
        for i, line in enumerate(lines, start=1):
            if term.lower() in (line or "").lower():
                out.append(f"{label} L{i}: {line.strip()}")
            if len(out) >= 20:
                break
        return out

    hits = []
    hits += _hits("DRAFT", st.session_state.main_text)
    hits += _hits("SYNOPSIS", st.session_state.synopsis)
    hits += _hits("WORLD", st.session_state.world)
    hits += _hits("CHARS", st.session_state.characters)
    hits += _hits("OUTLINE", st.session_state.outline)

    if not hits:
        return f"Find: no matches for '{term}'."
    return "\n".join(hits[:30])


def handle_junk_commands() -> None:
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return

    m = CMD_CREATE.match(raw)
    if m:
        title = m.group(1).strip()
        pid = create_project_from_current_bible(title)
        st.session_state.active_project_by_bay["NEW"] = pid
        st.session_state.active_bay = "NEW"
        load_project_into_session(pid)
        st.session_state.voice_status = f"Created project in NEW: {st.session_state.project_title}"
        st.session_state.last_action = "Create Project"
        st.session_state.junk = ""
        autosave()
        return

    if CMD_PROMOTE.match(raw):
        pid = st.session_state.project_id
        bay = st.session_state.active_bay
        nb = next_bay(bay)
        if not pid or not nb:
            st.session_state.tool_output = "Promote: no project selected, or already FINAL."
            st.session_state.voice_status = "Promote blocked."
            st.session_state.junk = ""
            autosave()
            return
        save_session_into_project()
        promote_project(pid, nb)
        st.session_state.active_project_by_bay[nb] = pid
        switch_bay(nb)
        st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
        st.session_state.last_action = f"Promote → {nb}"
        st.session_state.junk = ""
        autosave()
        return

    m = CMD_FIND.match(raw)
    if m:
        st.session_state.tool_output = _clamp_text(_run_find(m.group(1)))
        st.session_state.voice_status = "Find complete"
        st.session_state.last_action = "Find"
        st.session_state.junk = ""
        autosave()
        return


# Run junk commands early (before widgets instantiate)
handle_junk_commands()


# ============================================================
# AI BRIEF + CALL
# ============================================================
def _story_bible_text() -> str:
    sb = []
    if (st.session_state.synopsis or "").strip():
        sb.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if (st.session_state.genre_style_notes or "").strip():
        sb.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if (st.session_state.world or "").strip():
        sb.append(f"WORLD:\n{st.session_state.world.strip()}")
    if (st.session_state.characters or "").strip():
        sb.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if (st.session_state.outline or "").strip():
        sb.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
    return "\n\n".join(sb).strip() if sb else "— None provided —"


def build_partner_brief(action_name: str, lane: str) -> str:
    """
    ═══════════════════════════════════════════════════════════════
    CORE INTEGRATION HUB - Assembles all Voice Bible controls into
    a unified AI prompt. Used by ALL AI generation functions.
    ═══════════════════════════════════════════════════════════════
    """
    story_bible = _story_bible_text()
    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
        vb.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {st.session_state.trained_intensity:.2f})")
    if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_technical_on:
        vb.append(f"Technical Controls: POV={st.session_state.pov}, Tense={st.session_state.tense} (enforcement {st.session_state.technical_intensity:.2f})")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    # Engine Style (trainable banks) → Semantic retrieval of trained samples
    style_name = (st.session_state.writing_style or "").strip().upper()
    style_directive = ""
    style_exemplars: List[str] = []
    if st.session_state.vb_style_on and style_name in ENGINE_STYLES:
        style_directive = engine_style_directive(style_name, float(st.session_state.style_intensity), lane)
        ctx2 = (st.session_state.main_text or "")[-2500:]
        q2 = ctx2 if ctx2.strip() else (st.session_state.synopsis or "")
        k = 1 + int(max(0.0, min(1.0, float(st.session_state.style_intensity))) * 2.0)
        style_exemplars = retrieve_style_exemplars(style_name, lane, q2, k=k)  # ← INTELLIGENT RETRIEVAL

    # Trained Voice → Vector-based semantic matching
    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)  # ← ADAPTIVE RETRIEVAL
    ex_block = "\n\n---\n\n".join(exemplars) if exemplars else "— None —"
    style_ex_block = "\n\n---\n\n".join(style_exemplars) if style_exemplars else "— None —"

    ai_x = float(st.session_state.ai_intensity)
    return f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
Professional output only. No UI talk. No process talk.

STORY BIBLE IS CANON + IDEA BANK.
When generating NEW material, pull at least 2 concrete specifics from the Story Bible.
Never contradict canon. Never add random characters/places unless Story Bible supports it.

LANE: {lane}

AI INTENSITY: {ai_x:.2f}
INTENSITY PROFILE: {intensity_profile(ai_x)}

VOICE CONTROLS:
{voice_controls}

ENGINE STYLE DIRECTIVE:
{style_directive if style_directive else "— None —"}

STYLE EXEMPLARS (mimic cadence/diction, not content):
{style_ex_block}

TRAINED EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE:
{story_bible}

ACTION: {action_name}
""".strip()


@safe_execute("AI Generation", fallback_value="[AI generation failed]", show_error=True)
def call_openai(system_brief: str, user_task: str, text: str) -> str:
    """
    ═══════════════════════════════════════════════════════════════
    UNIFIED AI GATEWAY - Single entry point for ALL AI generation.
    Applies AI Intensity → Temperature conversion automatically.
    Includes error handling, rate limiting, and logging.
    ═══════════════════════════════════════════════════════════════
    """
    # Rate limiting check
    if hasattr(st.session_state, 'rate_limiter'):
        if not st.session_state.rate_limiter.check_rate_limit():
            wait_time = st.session_state.rate_limiter.wait_time()
            logger.warning(f"Rate limit exceeded, need to wait {wait_time:.1f}s")
            raise AIServiceError(f"⏱️ Rate limit reached. Please wait {int(wait_time)}s before next request.")
    
    # Validate inputs
    validate_text_input(system_brief, "system_brief", max_length=50000, min_length=10)
    validate_text_input(user_task, "user_task", max_length=10000, min_length=5)
    validate_text_input(text, "draft_text", max_length=100000)
    
    key = require_openai_key()
    
    try:
        from openai import OpenAI
    except ImportError as e:
        logger.error("OpenAI SDK not installed")
        raise AIServiceError("OpenAI SDK not installed. Add to requirements.txt: openai") from e

    try:
        client = OpenAI(api_key=key, timeout=90, max_retries=3)
    except TypeError:
        client = OpenAI(api_key=key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise AIServiceError(f"Failed to initialize AI client: {e}") from e

    temperature = temperature_from_intensity(st.session_state.ai_intensity)
    
    logger.info(f"AI call: model={OPENAI_MODEL}, temp={temperature:.2f}, brief={len(system_brief)}chars, text={len(text)}chars")
    
    # Track performance
    import time
    start_time = time.time()
    
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_brief},
                {"role": "user", "content": f"{user_task}\n\nDRAFT:\n{text.strip()}"},
            ],
            temperature=temperature,
        )
        result = (resp.choices[0].message.content or "").strip()
        
        # Log completion stats
        if hasattr(resp, 'usage') and resp.usage:
            logger.info(f"AI response: {resp.usage.total_tokens} tokens, {len(result)} chars")
        else:
            logger.info(f"AI response: {len(result)} chars")
        
        # Record performance metrics
        duration = time.time() - start_time
        if hasattr(st.session_state, 'perf_monitor'):
            st.session_state.perf_monitor.record_ai_call(duration)
        logger.info(f"AI call completed in {duration:.2f}s")
            
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"OpenAI API call failed after {time.time() - start_time:.2f}s: {error_msg}")
        
        # Classify error types
        if "rate_limit" in error_msg.lower():
            raise AIServiceError("⏱️ Rate limit exceeded. Please wait a moment and try again.") from e
        elif "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
            raise AIServiceError("💳 API quota exceeded. Check your OpenAI billing.") from e
        elif "invalid_api_key" in error_msg.lower():
            raise AIServiceError("🔑 Invalid API key. Check your OpenAI credentials.") from e
        elif "timeout" in error_msg.lower():
            raise AIServiceError("⏰ Request timed out. Try with shorter text or try again.") from e
        else:
            raise AIServiceError(f"AI service error: {error_msg}") from e


def local_cleanup(text: str) -> str:
    t = (text or "")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{4,}", "\n\n\n", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,.;:!?])([A-Za-z0-9])", r"\1 \2", t)
    t = re.sub(r"\.\.\.", "…", t)
    t = re.sub(r"\s*--\s*", " — ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def sb_breakdown_ai(text: str) -> Dict[str, str]:
    """
    AI-powered import breakdown - RESPECTS VOICE BIBLE CONTROLS.
    Analyzes source document and extracts Story Bible sections.
    """
    # Build Voice Bible brief (same pattern as other AI functions)
    vb_controls = []
    if st.session_state.vb_style_on:
        vb_controls.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb_controls.append(f"Genre: {st.session_state.genre}")
    
    voice_brief = "\n".join(vb_controls) if vb_controls else "— Use clear, neutral analysis —"
    
    ai_x = float(st.session_state.ai_intensity)
    
    system_brief = f"""You are a precise literary analyst extracting Story Bible sections from source material.

AI INTENSITY: {ai_x:.2f}

VOICE CONTROLS (apply to your analysis):
{voice_brief}

POV: {st.session_state.pov}
TENSE: {st.session_state.tense}

Return STRICT JSON with these exact keys: synopsis, genre_style_notes, world, characters, outline

Rules:
- Use clear, concrete specifics (names, places, stakes)
- Preserve existing proper nouns from the text
- If a section is unknown, return an empty string for it
- No commentary. JSON only."""

    task = "Analyze the source document and extract Story Bible sections. Return valid JSON only."
    
    try:
        out = call_openai(system_brief, task, text)
        obj = _extract_json_object(out) or {}
        return {
            "synopsis": _normalize_text(str(obj.get("synopsis", ""))),
            "genre_style_notes": _normalize_text(str(obj.get("genre_style_notes", ""))),
            "world": _normalize_text(str(obj.get("world", ""))),
            "characters": _normalize_text(str(obj.get("characters", ""))),
            "outline": _normalize_text(str(obj.get("outline", ""))),
        }
    except Exception:
        return _sb_sections_from_text_heuristic(text)


def _merge_section(existing: str, incoming: str, mode: str) -> str:
    ex = (existing or "").strip()
    inc = (incoming or "").strip()
    if mode == "Replace":
        return inc
    if not ex:
        return inc
    if not inc:
        return ex
    return (ex + "\n\n" + inc).strip()


def format_manuscript_standard(title: str, author: str, text: str, word_count: int) -> str:
    """
    Format text according to industry-standard manuscript guidelines:
    - Title page with word count
    - Proper spacing and indentation
    - Chapter breaks
    - Page headers
    """
    lines = []
    
    # Title Page
    lines.append(f"{author}")
    lines.append(f"{word_count} words")
    lines.append("")
    lines.append("")
    lines.append("")
    lines.append("")
    lines.append(f"{title.upper()}")
    lines.append("")
    lines.append(f"by {author}")
    lines.append("")
    lines.append("")
    lines.append("\n" * 10)  # Page break
    lines.append("")
    
    # Format body text
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Detect chapter headings (all caps or starts with "Chapter")
        if para.isupper() or para.startswith("Chapter") or para.startswith("CHAPTER"):
            lines.append("\n" * 3)  # Extra spacing before chapter
            lines.append(para)
            lines.append("")
        else:
            # Regular paragraph with proper indentation
            lines.append(f"    {para}")
            lines.append("")
    
    return "\n".join(lines)


def format_ebook_html(title: str, author: str, text: str) -> str:
    """
    Format text as clean HTML suitable for ebook conversion.
    Includes proper semantic markup for chapters, paragraphs, etc.
    """
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('    <meta charset="UTF-8">')
    html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append(f'    <title>{title}</title>')
    html.append('    <style>')
    html.append('        body { font-family: Georgia, serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; }')
    html.append('        h1 { text-align: center; margin: 2em 0; font-size: 2em; }')
    html.append('        h2 { text-align: center; margin: 2em 0 1em 0; page-break-before: always; }')
    html.append('        p { text-indent: 2em; margin: 0 0 1em 0; }')
    html.append('        p.first { text-indent: 0; }')
    html.append('        .title-page { text-align: center; margin: 4em 0; page-break-after: always; }')
    html.append('        .author { font-size: 1.2em; margin-top: 1em; }')
    html.append('    </style>')
    html.append('</head>')
    html.append('<body>')
    
    # Title page
    html.append('    <div class="title-page">')
    html.append(f'        <h1>{title}</h1>')
    html.append(f'        <p class="author">by {author}</p>')
    html.append('    </div>')
    
    # Body text
    paragraphs = text.split('\n\n')
    in_chapter = False
    first_in_chapter = True
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Detect chapter headings
        if para.isupper() or para.startswith("Chapter") or para.startswith("CHAPTER"):
            html.append(f'    <h2>{para}</h2>')
            in_chapter = True
            first_in_chapter = True
        else:
            # Regular paragraph
            p_class = ' class="first"' if first_in_chapter else ''
            html.append(f'    <p{p_class}>{para}</p>')
            first_in_chapter = False
    
    html.append('</body>')
    html.append('</html>')
    
    return '\n'.join(html)


def build_epub_bytes(title: str, author: str, text: str) -> Optional[bytes]:
        if not EPUB_AVAILABLE:
                return None
        book = epub.EpubBook()
        book.set_title(title or "Untitled")
        book.add_author(author or "Author")

        # Title page
        c_over = epub.EpubHtml(title="Title", file_name="title.xhtml", lang="en")
        c_over.content = f"""
        <h1>{title}</h1>
        <p>by {author}</p>
        """
        book.add_item(c_over)

        # Body
        paragraphs = text.split("\n\n")
        chap_items = []
        chap_html = []
        for para in paragraphs:
                para = para.strip()
                if not para:
                        continue
                if para.isupper() or para.startswith("Chapter") or para.startswith("CHAPTER"):
                        if chap_html:
                                ch = epub.EpubHtml(title="Chapter", file_name=f"chap_{len(chap_items)}.xhtml", lang="en")
                                ch.content = """<html><body>""" + """\n""".join(chap_html) + """</body></html>"""
                                book.add_item(ch)
                                chap_items.append(ch)
                                chap_html = []
                        chap_html.append(f"<h2>{para}</h2>")
                else:
                        chap_html.append(f"<p>{para}</p>")
        if chap_html:
                ch = epub.EpubHtml(title="Chapter", file_name=f"chap_{len(chap_items)}.xhtml", lang="en")
                ch.content = """<html><body>""" + """\n""".join(chap_html) + """</body></html>"""
                book.add_item(ch)
                chap_items.append(ch)

        # Spine / TOC
        spine = ['nav', c_over] + chap_items
        book.toc = tuple(chap_items)
        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        buf = BytesIO()
        epub.write_epub(buf, book)
        return buf.getvalue()


def build_pdf_bytes(title: str, author: str, text: str) -> Optional[bytes]:
        if not PDF_AVAILABLE:
                return None
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Times", 'B', 16)
        pdf.multi_cell(0, 10, txt=title or "Untitled", align='C')
        pdf.ln(6)
        pdf.set_font("Times", '', 12)
        pdf.multi_cell(0, 8, txt=f"by {author or 'Author'}", align='C')
        pdf.ln(10)
        pdf.set_font("Times", '', 12)
        paragraphs = text.split("\n\n")
        for para in paragraphs:
                para = para.strip()
                if not para:
                        continue
                if para.isupper() or para.startswith("Chapter") or para.startswith("CHAPTER"):
                        pdf.ln(4)
                        pdf.set_font("Times", 'B', 13)
                        pdf.multi_cell(0, 8, txt=para, align='C')
                        pdf.set_font("Times", '', 12)
                        pdf.ln(2)
                else:
                        pdf.multi_cell(0, 8, txt=para)
                        pdf.ln(2)
        output = pdf.output(dest='S')
        # Handle both bytes, bytearray, and string outputs from different fpdf2 versions
        if isinstance(output, (bytes, bytearray)):
                return bytes(output)
        return output.encode('latin1')


def build_kindle_package(title: str, author: str, text: str) -> bytes:
        html = format_ebook_html(title, author, text)
        buf = BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("index.html", html)
                opf = f"""
<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
    <metadata>
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">{title}</dc:title>
        <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{author}</dc:creator>
        <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>
        <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="bookid">urn:uuid:placeholder</dc:identifier>
    </metadata>
    <manifest>
        <item id="html" href="index.html" media-type="text/html" />
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    </manifest>
    <spine toc="ncx">
        <itemref idref="html" />
    </spine>
</package>
"""
                toc = f"""
<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:placeholder"/>
    </head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
        <navPoint id="navPoint-1" playOrder="1">
            <navLabel><text>Start</text></navLabel>
            <content src="index.html"/>
        </navPoint>
    </navMap>
</ncx>
"""
                zf.writestr("content.opf", opf)
                zf.writestr("toc.ncx", toc)
        return buf.getvalue()


# ============================================================
# STORY BIBLE AI GENERATION
# ============================================================
def generate_story_bible_section(section_type: str) -> None:
    """Generate content for a specific Story Bible section using AI.
    RESPECTS ALL VOICE BIBLE SETTINGS - uses same engine as writing actions."""
    if not has_openai_key():
        st.session_state.tool_output = f"AI generation requires OPENAI_API_KEY to be configured."
        st.session_state.voice_status = f"{section_type}: AI unavailable"
        autosave()
        return

    # Gather context from existing Story Bible sections and draft
    context_parts = []
    if st.session_state.main_text:
        context_parts.append(f"DRAFT TEXT:\n{st.session_state.main_text[:3000]}")
    if st.session_state.synopsis and section_type != "Synopsis":
        context_parts.append(f"SYNOPSIS:\n{st.session_state.synopsis}")
    if st.session_state.genre_style_notes and section_type != "Genre/Style":
        context_parts.append(f"GENRE/STYLE:\n{st.session_state.genre_style_notes}")
    if st.session_state.world and section_type != "World":
        context_parts.append(f"WORLD:\n{st.session_state.world}")
    if st.session_state.characters and section_type != "Characters":
        context_parts.append(f"CHARACTERS:\n{st.session_state.characters}")
    if st.session_state.outline and section_type != "Outline":
        context_parts.append(f"OUTLINE:\n{st.session_state.outline}")
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No context available yet."

    # Section-specific generation prompts
    prompts = {
        "Synopsis": "Write a concise, compelling 2-3 paragraph synopsis that captures the story's core conflict, main characters, and stakes. Be specific with names and situations.",
        "Genre/Style": "Describe the genre, tone, voice, and stylistic approach for this story. Include specific markers like 'hardboiled detective', 'lyrical literary fiction', 'tight thriller prose', etc.",
        "World": "Detail the world, setting, and key locations. Include rules, atmosphere, time period, and any special systems (magic, technology, social structures). Be concrete and specific.",
        "Characters": "List and describe the main characters with names, roles, relationships, motivations, and key traits. Format as a character list with details.",
        "Outline": "Create a story outline with acts, major beats, key scenes, and turning points. Structure it clearly with progression from beginning to end.",
    }

    try:
        task = prompts.get(section_type, f"Generate {section_type} content for the Story Bible.")
        
        # BUILD FULL VOICE BIBLE BRIEF - same as writing actions
        # This ensures Story Bible generation respects ALL Voice Bible controls
        vb_controls = []
        if st.session_state.vb_style_on:
            vb_controls.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
        if st.session_state.vb_genre_on:
            vb_controls.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
        if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
            vb_controls.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {st.session_state.trained_intensity:.2f})")
        if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
            vb_controls.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
        
        voice_brief = "\n\n".join(vb_controls) if vb_controls else "— No Voice Bible controls active —"
        
        ai_x = float(st.session_state.ai_intensity)
        brief = f"""You are a story development expert helping build a comprehensive Story Bible.

AI INTENSITY: {ai_x:.2f}
INTENSITY PROFILE: {intensity_profile(ai_x)}

VOICE CONTROLS (apply these to your output):
{voice_brief}

POV: {st.session_state.pov}
TENSE: {st.session_state.tense}

EXISTING CONTEXT:
{context}"""
        
        result = call_openai(brief, task, "")
        
        if result:
            if section_type == "Synopsis":
                st.session_state.synopsis = result.strip()
            elif section_type == "Genre/Style":
                st.session_state.genre_style_notes = result.strip()
            elif section_type == "World":
                st.session_state.world = result.strip()
            elif section_type == "Characters":
                st.session_state.characters = result.strip()
            elif section_type == "Outline":
                st.session_state.outline = result.strip()
            
            st.session_state.voice_status = f"Generated: {section_type} (Voice Bible applied)"
            st.session_state.last_action = f"Generate {section_type}"
            autosave()
    except Exception as e:
        st.session_state.tool_output = f"AI generation error: {str(e)}"
        st.session_state.voice_status = f"{section_type}: generation failed"
        autosave()


# ============================================================
# ACTIONS (queued for Streamlit safety)
# ============================================================
def partner_action(action: str) -> None:
    """
    ═══════════════════════════════════════════════════════════════
    WRITING ACTIONS ROUTER - All bottom bar functions route here.
    Uses build_partner_brief() → Ensures ALL actions use Voice Bible.
    Results appear in AI output window for user approval.
    ═══════════════════════════════════════════════════════════════
    """
    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)  # ← UNIFIED BRIEF with ALL Voice Bible controls
    use_ai = has_openai_key()
    
    # Track action start
    start_word_count = len(text.split()) if text else 0

    def stage_result(result: str, mode: str = "append") -> None:
        """Stage AI result in output window for user approval."""
        if result and result.strip():
            st.session_state.ai_generated_text = result.strip()
            st.session_state.ai_generation_mode = mode
            st.session_state.last_action = action
            vb_summary = _get_voice_bible_summary()
            st.session_state.voice_status = f"{action} complete - Review in AI Output Window"
            
            # Track analytics
            if hasattr(st.session_state, 'analytics'):
                result_word_count = len(result.split())
                st.session_state.analytics.track_event(action.lower(), {
                    "word_count": result_word_count,
                    "lane": lane,
                    "use_ai": use_ai,
                })
            
            autosave()

    try:
        if action == "Write":
            if use_ai:
                task = (
                    f"Continue decisively in lane ({lane}). Add 1–3 paragraphs that advance the scene. "
                    "MANDATORY: incorporate at least 2 Story Bible specifics. "
                    "No recap. No planning. Just prose."
                )
                out = call_openai(brief, task, text if text.strip() else "Start the opening.")
                stage_result(out, mode="append")
            else:
                st.session_state.tool_output = "Write requires OPENAI_API_KEY. Set it in Streamlit Secrets."
                st.session_state.voice_status = "Action blocked: missing API key"
                autosave()
            return

        if action == "Rewrite":
            if use_ai:
                task = f"Rewrite for professional quality in lane ({lane}). Preserve meaning and canon. Return full revised text."
                out = call_openai(brief, task, text)
                stage_result(out, mode="replace")
            else:
                stage_result(local_cleanup(text), mode="replace")
            return

        if action == "Expand":
            if use_ai:
                task = f"Expand with meaningful depth in lane ({lane}). No padding. Preserve canon. Return full revised text."
                out = call_openai(brief, task, text)
                stage_result(out, mode="replace")
            else:
                st.session_state.tool_output = "Expand requires OPENAI_API_KEY. Set it in Streamlit Secrets."
                st.session_state.voice_status = "Action blocked: missing API key"
                autosave()
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Replace the final sentence with a stronger one (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text)
                stage_result(out, mode="replace")
            else:
                st.session_state.tool_output = "Rephrase requires OPENAI_API_KEY. Set it in Streamlit Secrets."
                st.session_state.voice_status = "Action blocked: missing API key"
                autosave()
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text)
                stage_result(out, mode="replace")
            else:
                st.session_state.tool_output = "Describe requires OPENAI_API_KEY. Set it in Streamlit Secrets."
                st.session_state.voice_status = "Action blocked: missing API key"
                autosave()
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = "Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text."
                out = call_openai(brief, task, cleaned)
                stage_result(out if out else cleaned, mode="replace")
            else:
                stage_result(cleaned, mode="replace")
            return

        if action == "Synonym":
            # Tool output only (does not change draft)
            last = ""
            m = re.search(r"([A-Za-z']{3,})\W*$", text.strip())
            if m:
                last = m.group(1)
            if not last:
                st.session_state.tool_output = "Synonym: couldn't detect a target word (try ending with a word)."
                st.session_state.voice_status = "Synonym: no target"
                autosave()
                return
            if use_ai:
                task = (
                    f"Give 12 strong synonyms for '{last}'. "
                    "Group them by nuance (formal, punchy, poetic, archaic, etc). "
                    "No filler." 
                )
                out = call_openai(brief, task, text)
                st.session_state.tool_output = _clamp_text(out)
            else:
                st.session_state.tool_output = f"Synonym requires OPENAI_API_KEY (target word: {last})."
            st.session_state.voice_status = f"Synonym: {last}"
            st.session_state.last_action = "Synonym"
            autosave()
            return

        if action == "Sentence":
            # Tool output only
            last_sentence = ""
            sentences = re.split(r"(?<=[.!?])\s+", text.strip())
            if sentences:
                last_sentence = sentences[-1].strip()
            if not last_sentence:
                st.session_state.tool_output = "Sentence: couldn't detect a final sentence."
                st.session_state.voice_status = "Sentence: no target"
                autosave()
                return
            if use_ai:
                task = (
                    "Provide 8 alternative rewrites of the final sentence. "
                    "Keep meaning. Vary rhythm and diction. Return as a numbered list."
                )
                out = call_openai(brief, task, text)
                st.session_state.tool_output = _clamp_text(out)
            else:
                st.session_state.tool_output = "Sentence requires OPENAI_API_KEY."
            st.session_state.voice_status = "Sentence options"
            st.session_state.last_action = "Sentence"
            autosave()
            return

    except Exception as e:
        msg = str(e)
        if ("insufficient_quota" in msg) or ("exceeded your current quota" in msg.lower()):
            st.session_state.voice_status = "Engine: OpenAI quota exceeded."
            st.session_state.tool_output = _clamp_text(
                "OpenAI returned a quota/billing error.\n\nFix:\n• Confirm your API key is correct\n• Check billing/usage limits\n• Or swap to a different key in Streamlit Secrets"
            )
        elif "OPENAI_API_KEY not set" in msg:
            st.session_state.voice_status = "Engine: missing OPENAI_API_KEY."
            st.session_state.tool_output = "Set OPENAI_API_KEY in Streamlit Secrets (or environment) to enable AI."
        else:
            st.session_state.voice_status = f"Engine: {msg}"
            st.session_state.tool_output = _clamp_text(f"ERROR:\n{msg}")
        autosave()


def queue_action(action: str) -> None:
    st.session_state.pending_action = action


def run_pending_action() -> None:
    action = st.session_state.get("pending_action")
    if not action:
        return
    st.session_state.pending_action = None
    
    # Set processing status
    st.session_state.voice_status = f"Processing: {action}..."

    # Get context variables
    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)
    use_ai = has_openai_key()

    def stage_result(result: str, mode: str = "append") -> None:
        """Stage AI result in output window for user approval."""
        if result and result.strip():
            st.session_state.ai_generated_text = result.strip()
            st.session_state.ai_generation_mode = mode
            st.session_state.last_action = action
            st.session_state.voice_status = f"{action} complete - Review in AI Output Window"
            autosave()

    # Find & Replace action
    if action == "Find & Replace":
        if use_ai:
            # Use AI to intelligently find and replace patterns
            task = (
                "Find and replace text based on user's writing. "
                "Identify all instances of words/phrases that should be changed. "
                "Return the full revised text with all replacements made. "
                "Be consistent with replacements throughout."
            )
            out = call_openai(brief, task, text)
            stage_result(out, mode="replace")
        else:
            st.session_state.tool_output = "Find & Replace requires OPENAI_API_KEY for intelligent replacement."
            st.session_state.voice_status = "Action blocked: missing API key"
            autosave()
        return

    # Non-engine UI hint (keeps session_state mutations pre-widget)
    if action == "__FIND_HINT__":
        st.session_state.tool_output = "Find is wired via /find: in Junk Drawer."
        st.session_state.voice_status = "Find: use /find: in Junk Drawer."
        st.session_state.last_action = "Find (hint)"
        autosave()
        return

    if action == "__VAULT_CLEAR_SAMPLE__":
        # Clear the vault sample text area safely (pre-widget) and surface status.
        st.session_state.vault_sample_text = ""
        note = (st.session_state.get("ui_notice") or "").strip()
        if note:
            st.session_state.voice_status = note
            st.session_state.ui_notice = ""
        st.session_state.last_action = "Voice Vault"
        autosave()
        return
    
    # Execute AI action
    try:
        partner_action(action)
    except Exception as e:
        st.session_state.voice_status = f"Error: {str(e)}"
        st.session_state.tool_output = f"Action failed: {str(e)}"
        autosave()


# Run queued actions early (pre-widget)
run_pending_action()


# ============================================================
# UI — TOP BAR (Integrated Navigation)
# ============================================================
top = st.container()
with top:
    # Connection status indicator
    if has_openai_key():
        st.success("✅ AI Connected | System Ready")
    else:
        st.error("❌ AI Not Connected | Set OPENAI_API_KEY in Streamlit Secrets to enable AI features")
    
    # Main navigation: Bays + Story Bible + Flow Controls
    nav_cols = st.columns([0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 2])

    # Bay navigation
    if nav_cols[0].button("🆕 New", key="bay_new", use_container_width=True):
        switch_bay("NEW")
        save_all_to_disk(force=True)

    if nav_cols[1].button("✏️ Rough", key="bay_rough", use_container_width=True):
        switch_bay("ROUGH")
        save_all_to_disk(force=True)

    if nav_cols[2].button("🛠 Edit", key="bay_edit", use_container_width=True):
        switch_bay("EDIT")
        save_all_to_disk(force=True)

    if nav_cols[3].button("✅ Final", key="bay_final", use_container_width=True):
        switch_bay("FINAL")
        save_all_to_disk(force=True)
    
    # Story Bible quick access
    if nav_cols[4].button("📖 Bible", key="nav_story_bible", use_container_width=True, help="Jump to Story Bible (left panel)"):
        # Toggle Story Bible focus via UI hint
        st.session_state.ui_notice = "📖 Story Bible ready (see left panel)"
    
    # Flow control: Promote to next bay
    current_bay = st.session_state.active_bay
    has_project = bool(st.session_state.project_id)
    next_bay_name = next_bay(current_bay)
    
    if next_bay_name and has_project:
        if nav_cols[5].button(f"→ {next_bay_name[0]}", key="nav_promote", use_container_width=True, 
                              help=f"Promote to {next_bay_name}"):
            save_session_into_project()
            promote_project(st.session_state.project_id, next_bay_name)
            st.session_state.active_project_by_bay[next_bay_name] = st.session_state.project_id
            switch_bay(next_bay_name)
            st.session_state.voice_status = f"Promoted → {next_bay_name}: {st.session_state.project_title}"
            st.session_state.last_action = f"Promote → {next_bay_name}"
            save_all_to_disk(force=True)
            st.rerun()
    
    # Status display
    nav_cols[6].markdown(
        f"""
        <div style='text-align:right;font-size:12px;'>
            <b>{st.session_state.active_bay}</b>: {st.session_state.project_title}
            &nbsp;•&nbsp; AI: {get_ai_intensity_safe():.2f}
            <br/>{st.session_state.voice_status}
            &nbsp;•&nbsp; {st.session_state.autosave_time or '—'}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ============================================================
# LOCKED LAYOUT (same ratios)
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])


# ============================================================
# LEFT — STORY BIBLE (NEW) or CHAPTERS (ROUGH/EDIT/FINAL)
# ============================================================
with left:
    bay = st.session_state.active_bay
    
    if bay == "NEW":
        # NEW BAY: Story Bible workspace only
        st.subheader("📖 Story Bible Setup")
        
        # Display workspace story bible status
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        wsb_id = w.get('workspace_story_bible_id', '—')
        wsb_created = w.get('workspace_story_bible_created_ts', '—')
        st.caption(f"Workspace Story Bible • Bible ID: **{wsb_id}** • Created: **{wsb_created}**")
        st.caption("Build your Story Bible, then send to ROUGH/EDIT/FINAL as chapters")
        
        st.divider()
        
        # Two simple options
        setup_mode = st.radio(
            "Story Bible creation",
            ["✍️ Manual Entry", "🤖 AI Breakdown"],
            key="sb_setup_mode",
            horizontal=True
        )
        
        if setup_mode == "🤖 AI Breakdown":
            st.caption("Upload a document and AI will break it into Story Bible sections")
            up = st.file_uploader("Upload (.txt, .md, .docx)", type=["txt", "md", "docx"], key="ai_upload")
            paste = st.text_area("Or paste text", key="ai_paste", height=100)
            
            if st.button("🤖 Run AI Breakdown", key="run_ai_breakdown", use_container_width=True):
                src_file, name = _read_uploaded_text(up)
                src = _normalize_text(paste if (paste or "").strip() else src_file)
                
                if not src.strip():
                    st.session_state.tool_output = "AI Breakdown: no text provided"
                    autosave()
                elif not has_openai_key():
                    st.session_state.tool_output = "AI Breakdown requires OPENAI_API_KEY"
                    autosave()
                else:
                    sections = sb_breakdown_ai(src)
                    st.session_state.synopsis = sections.get("synopsis", "")
                    st.session_state.genre_style_notes = sections.get("genre_style_notes", "")
                    st.session_state.world = sections.get("world", "")
                    st.session_state.characters = sections.get("characters", "")
                    st.session_state.outline = sections.get("outline", "")
                    st.session_state.voice_status = f"AI Breakdown complete from {name or 'paste'}"
                    st.session_state.last_action = "AI Breakdown"
                    autosave()
                    st.rerun()
        else:
            st.caption("Fill in Story Bible sections manually below (see tabs)")
        
        st.divider()
        
        # Send to production bays as chapters
        st.subheader("🚀 Send to Bay")
        target_bay = st.selectbox("Destination", ["ROUGH", "EDIT", "FINAL"], key="target_bay")
        project_title = st.text_input("Project title", value="New Chapter Project", key="new_project_title")
        
        if st.button(f"📤 Send to {target_bay}", key="send_to_bay", use_container_width=True):
            # Create project with chapters structure
            if "chapters" not in st.session_state:
                st.session_state.chapters = {}
            
            pid = create_project_from_current_bible(project_title)
            proj = st.session_state.projects[pid]
            proj["bay"] = target_bay
            
            # Initialize chapter structure
            proj["chapters"] = {"1": {"title": "Chapter 1", "content": ""}}
            proj["active_chapter"] = "1"
            
            st.session_state.active_project_by_bay[target_bay] = pid
            switch_bay(target_bay)
            load_project_into_session(pid)
            st.session_state.voice_status = f"Story Bible → {target_bay}: {project_title}"
            st.session_state.last_action = f"Send to {target_bay}"
            autosave()
            st.rerun()
    
    else:
        # ROUGH/EDIT/FINAL: Chapter navigation
        st.subheader(f"📚 {bay} Bay")
        
        # Project selector
        bay_projects = list_projects_in_bay(bay)
        if not bay_projects:
            st.caption(f"No projects in {bay}")
            st.caption("💡 Create projects in NEW bay")
        else:
            project_options = ["—"] + [title for pid, title in bay_projects]
            project_ids = [None] + [pid for pid, title in bay_projects]
            
            current_pid = st.session_state.project_id
            current_idx = project_ids.index(current_pid) if current_pid in project_ids else 0
            
            sel = st.selectbox("Project", project_options, index=current_idx, key="chapter_project_selector")
            sel_pid = project_ids[project_options.index(sel)]
            
            if sel_pid != st.session_state.project_id:
                if sel_pid:
                    load_project_into_session(sel_pid)
                    st.session_state.voice_status = f"{bay}: {st.session_state.project_title}"
                else:
                    st.session_state.project_id = None
                    st.session_state.project_title = "—"
                st.session_state.last_action = "Select Project"
                autosave()
                st.rerun()
            
            # Chapter management
            if sel_pid:
                st.divider()
                proj = st.session_state.projects.get(sel_pid, {})
                
                # Initialize chapters if not present
                if "chapters" not in proj:
                    proj["chapters"] = {"1": {"title": "Chapter 1", "content": ""}}
                    proj["active_chapter"] = "1"
                
                chapters = proj.get("chapters", {})
                active_chapter = proj.get("active_chapter", "1")
                
                # Chapter selector
                chapter_nums = sorted(chapters.keys(), key=lambda x: int(x))
                chapter_labels = [f"Ch {num}: {chapters[num].get('title', f'Chapter {num}')}" for num in chapter_nums]
                
                if active_chapter not in chapter_nums:
                    active_chapter = chapter_nums[0] if chapter_nums else "1"
                    proj["active_chapter"] = active_chapter
                
                active_idx = chapter_nums.index(active_chapter) if active_chapter in chapter_nums else 0
                
                sel_chapter = st.selectbox("Chapter", chapter_labels, index=active_idx, key="chapter_selector")
                sel_chapter_num = chapter_nums[chapter_labels.index(sel_chapter)]
                
                if sel_chapter_num != active_chapter:
                    proj["active_chapter"] = sel_chapter_num
                    # Load chapter content into main_text
                    st.session_state.main_text = chapters[sel_chapter_num].get("content", "")
                    autosave()
                    st.rerun()
                
                # Chapter actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("➕", key="add_chapter", help="Add new chapter"):
                        new_num = str(max([int(n) for n in chapter_nums]) + 1)
                        chapters[new_num] = {"title": f"Chapter {new_num}", "content": ""}
                        proj["active_chapter"] = new_num
                        st.session_state.main_text = ""
                        autosave()
                        st.rerun()
                
                with col2:
                    if len(chapter_nums) > 1 and st.button("🗑️", key="del_chapter", help="Delete current chapter"):
                        del chapters[active_chapter]
                        chapter_nums = sorted(chapters.keys(), key=lambda x: int(x))
                        proj["active_chapter"] = chapter_nums[0] if chapter_nums else "1"
                        st.session_state.main_text = chapters[proj["active_chapter"]].get("content", "")
                        autosave()
                        st.rerun()
                
                # Chapter title editor
                chapter_title = st.text_input(
                    "Chapter title",
                    value=chapters[active_chapter].get("title", f"Chapter {active_chapter}"),
                    key="chapter_title_input"
                )
                if chapter_title != chapters[active_chapter].get("title"):
                    chapters[active_chapter]["title"] = chapter_title
                    autosave()

    # AI Intensity - MASTER CONTROL for all AI generation
    st.divider()
    st.subheader("🎚️ AI Intensity")
    st.caption("⚙️ Controls ALL AI generation")
    
    ai_int_col1, ai_int_col2 = st.columns([3, 1])
    with ai_int_col1:
        st.slider(
            "AI Intensity",
            0.0,
            1.0,
            key="ai_intensity",
            help="0.0 = conservative/precise, 1.0 = bold/creative",
            on_change=autosave,
        )
    with ai_int_col2:
        current_ai = get_ai_intensity_safe()
        if current_ai <= 0.25:
            label, desc = "LOW", "Conservative"
        elif current_ai <= 0.60:
            label, desc = "MED", "Balanced"
        elif current_ai <= 0.85:
            label, desc = "HIGH", "Bold"
        else:
            label, desc = "MAX", "Creative"
        st.metric("Mode", label, desc)

    # Import / Export hub
    with st.expander("📦 Import / Export", expanded=False):
        tab_imp, tab_exp, tab_bundle = st.tabs(["Import", "Export", "Bundles"])

        with tab_imp:
            st.caption("📥 Import documents for editing, formatting, and structure work.")
            
            # Simple import interface
            up = st.file_uploader("Upload (.txt, .md, .docx)", type=["txt", "md", "docx"], key="io_upload")
            paste = st.text_area("Paste text", key="io_paste", height=140)
            
            target = st.selectbox(
                "Import destination",
                ["Draft", "Synopsis", "Genre & Style Notes", "World", "Characters", "Outline"],
                key="io_target",
                help="Where to place the imported content"
            )
            
            merge_mode = st.radio("Merge mode", ["Append", "Replace"], horizontal=True, key="io_merge")

            if st.button("📥 Import", key="io_run_import", use_container_width=True):
                src_file, name = _read_uploaded_text(up)
                src = _normalize_text(paste if (paste or "").strip() else src_file)
                if not src.strip():
                    st.session_state.tool_output = "Import: no text provided (or file too large)."
                    st.session_state.voice_status = "Import blocked"
                    autosave()
                else:
                    # Map friendly names to session state keys
                    target_map = {
                        "Draft": "main_text",
                        "Synopsis": "synopsis",
                        "Genre & Style Notes": "genre_style_notes",
                        "World": "world",
                        "Characters": "characters",
                        "Outline": "outline"
                    }
                    key = target_map.get(target, "main_text")
                    current_val = getattr(st.session_state, key, "")
                    setattr(st.session_state, key, _merge_section(current_val, src, merge_mode))
                    st.session_state.voice_status = f"Imported → {target} ({name or 'paste'})"
                    st.session_state.last_action = f"Import → {target}"
                    autosave()
            
            # Optional AI Breakdown feature (separate from import)
            st.divider()
            st.caption("🤖 **Optional:** AI-powered breakdown of imported Story Bible content")
            
            if has_openai_key():
                breakdown_source = st.selectbox(
                    "Source for AI breakdown",
                    ["Synopsis", "Genre & Style Notes", "World", "Characters", "Outline"],
                    key="ai_breakdown_source",
                    help="AI will analyze this section and distribute content across all Story Bible categories"
                )
                
                if st.button("✨ Run AI Breakdown", key="io_ai_breakdown", use_container_width=True):
                    source_map = {
                        "Synopsis": "synopsis",
                        "Genre & Style Notes": "genre_style_notes",
                        "World": "world",
                        "Characters": "characters",
                        "Outline": "outline"
                    }
                    source_key = source_map.get(breakdown_source, "synopsis")
                    source_text = getattr(st.session_state, source_key, "").strip()
                    
                    if not source_text:
                        st.session_state.tool_output = f"AI Breakdown: {breakdown_source} is empty."
                        st.session_state.voice_status = "Breakdown blocked"
                        autosave()
                    else:
                        sections = sb_breakdown_ai(source_text)
                        st.session_state.synopsis = _merge_section(st.session_state.synopsis, sections.get("synopsis", ""), "Append")
                        st.session_state.genre_style_notes = _merge_section(
                            st.session_state.genre_style_notes, sections.get("genre_style_notes", ""), "Append"
                        )
                        st.session_state.world = _merge_section(st.session_state.world, sections.get("world", ""), "Append")
                        st.session_state.characters = _merge_section(st.session_state.characters, sections.get("characters", ""), "Append")
                        st.session_state.outline = _merge_section(st.session_state.outline, sections.get("outline", ""), "Append")
                        st.session_state.voice_status = f"AI Breakdown → Story Bible (from {breakdown_source})"
                        st.session_state.last_action = "AI Breakdown"
                        st.session_state.tool_output = f"AI analyzed {breakdown_source} and distributed content across all Story Bible sections."
                        autosave()
            else:
                st.caption("⚠️ AI Breakdown requires OPENAI_API_KEY (see Settings)")

        with tab_exp:
            title = "Workspace" if in_workspace_mode() else st.session_state.project_title
            meta = {"Context": "Workspace" if in_workspace_mode() else "Project", "Bay": st.session_state.active_bay}
            if st.session_state.project_id:
                meta["Project ID"] = st.session_state.project_id
            stem = _safe_filename(title, "olivetti")

            # Ensure latest writes are saved into project/workspace
            if in_workspace_mode():
                save_workspace_from_session()
            else:
                save_session_into_project()

            draft_txt = st.session_state.main_text or ""
            sb_dict = {
                "synopsis": st.session_state.synopsis,
                "genre_style_notes": st.session_state.genre_style_notes,
                "world": st.session_state.world,
                "characters": st.session_state.characters,
                "outline": st.session_state.outline,
            }
            
            # Word count
            word_count = len(draft_txt.split())
            
            st.caption(f"**Draft Stats:** {word_count:,} words • Bay: {st.session_state.active_bay}")
            
            # Professional formatting options
            if st.session_state.active_bay == "FINAL":
                st.info("✨ **FINAL Bay** - Professional manuscript formatting available")
            
            # Manuscript formatting inputs
            with st.expander("📖 Manuscript Formatting Options", expanded=st.session_state.active_bay == "FINAL"):
                author_name = st.text_input("Author Name", value="Author Name", key="export_author")
                st.caption("Professional manuscript format follows industry standards (Shunn format)")

            st.subheader("Standard Exports")
            
            st.caption("💾 **Optional:** Save to workspace folder for organized project management")
            
            # Folder save feature
            save_to_folder = st.checkbox("Save to workspace folder", key="save_to_folder", value=False)
            folder_path = None
            if save_to_folder:
                folder_name = st.text_input("Folder name", value=stem, key="folder_name", help="Files will be saved to /workspaces/superhappyfuntimellc/exports/<folder>")
                folder_path = f"/workspaces/superhappyfuntimellc/exports/{folder_name}"
                st.caption(f"📁 Files will be saved to: `{folder_path}`")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                st.download_button("Download Draft (.txt)", data=draft_txt, file_name=f"{stem}_draft.txt", mime="text/plain", use_container_width=True)
            with col_exp2:
                st.download_button(
                    "Download Draft (.md)",
                    data=draft_markdown(title, draft_txt, meta),
                    file_name=f"{stem}_draft.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            st.download_button(
                "Download Story Bible (.md)",
                data=story_bible_markdown(title, sb_dict, meta),
                file_name=f"{stem}_story_bible.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            # Folder save button
            if save_to_folder and folder_path:
                if st.button("💾 Save All to Folder", key="save_folder_btn", use_container_width=True):
                    import os
                    try:
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Save files
                        with open(f"{folder_path}/{stem}_draft.txt", "w", encoding="utf-8") as f:
                            f.write(draft_txt)
                        with open(f"{folder_path}/{stem}_draft.md", "w", encoding="utf-8") as f:
                            f.write(draft_markdown(title, draft_txt, meta))
                        with open(f"{folder_path}/{stem}_story_bible.md", "w", encoding="utf-8") as f:
                            f.write(story_bible_markdown(title, sb_dict, meta))
                        
                        st.session_state.tool_output = f"✅ Saved 3 files to {folder_path}"
                        st.session_state.voice_status = f"Saved to folder: {folder_name}"
                        autosave()
                    except Exception as e:
                        st.session_state.tool_output = f"❌ Folder save failed: {str(e)}"
                        autosave()
            
            st.subheader("📖 Professional Formats")
            
            # Manuscript format
            manuscript_txt = format_manuscript_standard(title, st.session_state.get("export_author", "Author Name"), draft_txt, word_count)
            col_man1, col_man2 = st.columns(2)
            with col_man1:
                st.download_button(
                    "📝 Manuscript (.txt)",
                    data=manuscript_txt,
                    file_name=f"{stem}_manuscript.txt",
                    mime="text/plain",
                    help="Industry-standard manuscript format (Shunn format)",
                    use_container_width=True
                )
            
            # eBook HTML
            ebook_html = format_ebook_html(title, st.session_state.get("export_author", "Author Name"), draft_txt)
            with col_man2:
                st.download_button(
                    "📱 eBook (.html)",
                    data=ebook_html,
                    file_name=f"{stem}_ebook.html",
                    mime="text/html",
                    help="Clean HTML for ebook conversion (import into Calibre/Kindle Create)",
                    use_container_width=True
                )
            # EPUB
            epub_bytes = build_epub_bytes(title, st.session_state.get("export_author", "Author Name"), draft_txt) if EPUB_AVAILABLE else None
            if EPUB_AVAILABLE:
                st.download_button(
                    "📗 EPUB (.epub)",
                    data=epub_bytes or b"",
                    file_name=f"{stem}.epub",
                    mime="application/epub+zip",
                    help="Ready-to-load EPUB (uses ebooklib)",
                    use_container_width=True,
                    disabled=epub_bytes is None
                )
            else:
                st.caption("EPUB export unavailable (install ebooklib to enable).")

            # PDF
            pdf_bytes = build_pdf_bytes(title, st.session_state.get("export_author", "Author Name"), draft_txt) if PDF_AVAILABLE else None
            if PDF_AVAILABLE:
                st.download_button(
                    "📄 PDF (.pdf)",
                    data=pdf_bytes or b"",
                    file_name=f"{stem}.pdf",
                    mime="application/pdf",
                    help="Lightweight PDF export (fpdf2)",
                    use_container_width=True,
                    disabled=pdf_bytes is None
                )
            else:
                st.caption("PDF export unavailable (install fpdf2 to enable).")

            # Kindle package (HTML + OPF + NCX zip)
            kindle_zip = build_kindle_package(title, st.session_state.get("export_author", "Author Name"), draft_txt)
            st.download_button(
                "📦 Kindle Package (.zip)",
                data=kindle_zip,
                file_name=f"{stem}_kindle_package.zip",
                mime="application/zip",
                help="Contains index.html, content.opf, toc.ncx for Kindle ingestion",
                use_container_width=True
            )
            
            st.caption("💡 **Tip:** Import .html into Calibre or Kindle Create to generate EPUB/MOBI files")

            st.divider()
            st.subheader("🔊 Audio Export (Text-to-Speech)")
            
            st.caption("📢 Generate audio narration of your work for accessibility or review")
            
            if not GTTS_AVAILABLE:
                st.warning("⚠️ Audio export unavailable. Install gTTS: `pip install gTTS`")
                st.caption("Use online TTS services like [Natural Reader](https://www.naturalreaders.com/) or [TTSReader](https://ttsreader.com/)")
            else:
                # TTS Settings
                tts_col1, tts_col2, tts_col3 = st.columns(3)
                with tts_col1:
                    tts_language = st.selectbox(
                        "Language",
                        [("en", "English"), ("es", "Spanish"), ("fr", "French"), ("de", "German"), ("it", "Italian")],
                        format_func=lambda x: x[1],
                        key="tts_language_select"
                    )
                with tts_col2:
                    tts_accent = st.selectbox(
                        "Accent",
                        [("com", "US"), ("co.uk", "UK"), ("com.au", "Australia"), ("ca", "Canada")],
                        format_func=lambda x: x[1],
                        key="tts_accent_select"
                    )
                with tts_col3:
                    tts_speed = st.checkbox(
                        "Slow Speed",
                        value=False,
                        key="tts_slow_select",
                        help="Enable slower narration for learning/accessibility"
                    )
                
                # Full text audio generation (no character limit)
                tts_text = draft_txt
                
                # Generate audio file
                if st.button("🎙️ Generate Audio File (MP3)", key="tts_generate", use_container_width=True):
                    if not tts_text.strip():
                        st.warning("No text to convert. Write something in the draft first.")
                    else:
                        with st.spinner(f"Generating audio from {len(tts_text.split())} words..."):
                            try:
                                # Generate audio using gTTS
                                lang_code = tts_language[0]
                                tld = tts_accent[0]
                                
                                tts = gTTS(
                                    text=tts_text,
                                    lang=lang_code,
                                    tld=tld,
                                    slow=tts_speed
                                )
                                
                                # Save to bytes
                                audio_buffer = BytesIO()
                                tts.write_to_fp(audio_buffer)
                                audio_buffer.seek(0)
                                audio_bytes = audio_buffer.read()
                                
                                # Calculate duration estimate (rough: 150 words per minute normal, 100 slow)
                                word_count = len(tts_text.split())
                                wpm = 100 if tts_speed else 150
                                duration_minutes = word_count / wpm
                                
                                st.success(f"✅ Audio generated: ~{duration_minutes:.1f} minutes ({word_count:,} words)")
                                
                                # Download button
                                st.download_button(
                                    "📥 Download Audio (MP3)",
                                    data=audio_bytes,
                                    file_name=f"{stem}_audio.mp3",
                                    mime="audio/mpeg",
                                    use_container_width=True
                                )
                                
                                # Audio player
                                st.audio(audio_bytes, format="audio/mp3")
                                
                            except Exception as e:
                                logger.error(f"Audio generation failed: {e}")
                                st.error(f"Audio generation failed: {str(e)}")
                                st.caption("Try reducing text length or check internet connection (gTTS requires online access).")
                
                st.caption("💡 **Full text converted** - No character limits. Audio generation requires internet connection.")

            st.divider()
            st.subheader("�📄 DOCX Export")

            if not DOCX_AVAILABLE:
                st.caption("DOCX export unavailable (install python-docx to enable).")
            else:
                def _docx_bytes(doc: "Document") -> bytes:
                    buf = BytesIO()
                    doc.save(buf)
                    return buf.getvalue()

                # Standard draft DOCX
                d = Document()
                d.add_heading(f"Draft — {title}", level=0)
                for mk, mv in meta.items():
                    d.add_paragraph(f"{mk}: {mv}")
                d.add_paragraph(now_ts())
                d.add_paragraph("")
                for para in _split_paragraphs(draft_txt):
                    d.add_paragraph(para)
                
                col_doc1, col_doc2 = st.columns(2)
                with col_doc1:
                    st.download_button(
                        "Download Draft (.docx)",
                        data=_docx_bytes(d),
                        file_name=f"{stem}_draft.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                
                # Professional manuscript DOCX
                md = Document()
                section = md.sections[0]
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
                
                p = md.add_paragraph()
                p.add_run(st.session_state.get("export_author", "Author Name")).bold = True
                p.add_run(f"\n{word_count:,} words")
                
                md.add_page_break()
                
                title_para = md.add_heading(title.upper(), level=1)
                title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                by_para = md.add_paragraph(f"by {st.session_state.get('export_author', 'Author Name')}")
                by_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                md.add_page_break()
                
                for para_text in _split_paragraphs(draft_txt):
                    if para_text.isupper() or para_text.startswith("Chapter") or para_text.startswith("CHAPTER"):
                        ch = md.add_heading(para_text, level=2)
                        ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:
                        p = md.add_paragraph(para_text)
                        p_format = p.paragraph_format
                        p_format.first_line_indent = Inches(0.5)
                        p_format.space_after = Pt(0)
                
                with col_doc2:
                    st.download_button(
                        "📝 Manuscript (.docx)",
                        data=_docx_bytes(md),
                        file_name=f"{stem}_manuscript.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        help="Professional manuscript format with proper margins and spacing",
                        use_container_width=True
                    )

        with tab_bundle:
            st.caption("Bundle exports are merge-safe (imports never wipe your library).")
            if st.session_state.project_id:
                pj = json.dumps(make_project_bundle(st.session_state.project_id), ensure_ascii=False, indent=2)
                st.download_button(
                    "Download Project Bundle (.json)",
                    data=pj,
                    file_name=f"{_safe_filename(st.session_state.project_title,'project')}_bundle.json",
                    mime="application/json",
                )
            lib = json.dumps(make_library_bundle(), ensure_ascii=False, indent=2)
            st.download_button("Download Full Library (.json)", data=lib, file_name="olivetti_library_bundle.json", mime="application/json")

            st.divider()
            target_bay = st.selectbox("Imported projects go to bay", BAYS, index=0, key="io_bundle_target")
            rename = st.text_input("Optional rename (single project import)", key="io_bundle_rename")
            upb = st.file_uploader("Upload .json bundle", type=["json"], key="io_bundle_upload")
            switch_after = st.checkbox("Switch to imported project after import", value=True, key="io_bundle_switch")

            if st.button("Import Bundle", key="io_bundle_import"):
                if upb is None:
                    st.session_state.tool_output = "Import bundle: upload a .json file first."
                    autosave()
                else:
                    raw = upb.getvalue()
                    if raw is not None and len(raw) > MAX_UPLOAD_BYTES:
                        st.session_state.tool_output = "Import bundle: file too large."
                        autosave()
                    else:
                        try:
                            obj = json.loads((raw or b"").decode("utf-8"))
                        except Exception:
                            obj = None
                        if not isinstance(obj, dict):
                            st.session_state.tool_output = "Import bundle: invalid JSON structure."
                            autosave()
                        else:
                            summary = _bundle_summary(obj)
                            st.session_state.tool_output = f"Detected: {summary}"
                            if obj.get("projects"):
                                n = import_library_bundle(obj)
                                st.session_state.voice_status = f"Imported library bundle: {n} project(s) merged."
                                st.session_state.last_action = "Import Library Bundle"
                                autosave()
                            elif obj.get("project"):
                                pid = import_project_bundle(obj, target_bay=target_bay, rename=rename)
                                if pid:
                                    st.session_state.voice_status = f"Imported project bundle → {pid}"
                                    st.session_state.last_action = "Import Project Bundle"
                                    autosave()
                                    if switch_after:
                                        switch_bay(target_bay)
                                        load_project_into_session(pid)
                                        st.session_state.voice_status = f"{target_bay}: {st.session_state.project_title} (imported)"
                                        autosave()
                                        st.rerun()
                                else:
                                    st.session_state.tool_output = "Import bundle: JSON did not look like a project bundle."
                                    autosave()
                            else:
                                st.session_state.tool_output = "Import bundle: bundle type not recognized."
                                autosave()

    # Story Bible Tabs - Each section in its own pane
    st.divider()
    bible_tabs = st.tabs(["🗃 Tools", "📝 Synopsis", "🎭 Genre", "🌍 World", "👤 Characters", "🧱 Outline"])
    
    # Tab 0: Tools (Junk Drawer)
    with bible_tabs[0]:
        st.text_area(
            "Junk Drawer",
            key="junk",
            height=80,
            on_change=autosave,
            label_visibility="collapsed",
            help="Commands: /create: Title  |  /promote  |  /find: term",
        )
        st.text_area("Tool Output", value=st.session_state.tool_output, height=140, disabled=True, label_visibility="collapsed")
    
    # Tab 1: Synopsis
    with bible_tabs[1]:
        st.text_area("Synopsis", key="synopsis", height=400, on_change=autosave, label_visibility="collapsed")
        if has_openai_key():
            if st.button("✨ Generate Synopsis", key="gen_synopsis", use_container_width=True):
                generate_story_bible_section("Synopsis")
                st.rerun()
    
    # Tab 2: Genre / Style Notes
    with bible_tabs[2]:
        st.text_area(
            "Genre / Style Notes",
            key="genre_style_notes",
            height=400,
            on_change=autosave,
            label_visibility="collapsed",
        )
        if has_openai_key():
            if st.button("✨ Generate Genre/Style", key="gen_genre", use_container_width=True):
                generate_story_bible_section("Genre/Style")
                st.rerun()
    
    # Tab 3: World Elements
    with bible_tabs[3]:
        st.text_area("World", key="world", height=400, on_change=autosave, label_visibility="collapsed")
        if has_openai_key():
            if st.button("✨ Generate World", key="gen_world", use_container_width=True):
                generate_story_bible_section("World")
                st.rerun()
    
    # Tab 4: Characters
    with bible_tabs[4]:
        st.text_area(
            "Characters",
            key="characters",
            height=400,
            on_change=autosave,
            label_visibility="collapsed",
        )
        if has_openai_key():
            if st.button("✨ Generate Characters", key="gen_characters", use_container_width=True):
                generate_story_bible_section("Characters")
                st.rerun()
    
    # Tab 5: Outline
    with bible_tabs[5]:
        st.text_area("Outline", key="outline", height=400, on_change=autosave, label_visibility="collapsed")
        if has_openai_key():
            if st.button("✨ Generate Outline", key="gen_outline", use_container_width=True):
                generate_story_bible_section("Outline")
                st.rerun()


# ============================================================
# CENTER — WRITING DESK
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")
    
    # Voice Bible Status - Show what's controlling AI generation
    vb_status = _get_voice_bible_summary()
    st.caption(f"🎚️ **Active Controls:** {vb_status}")
    
    # Canon Guardian + Heatmap row (Project-Wide Analysis)
    col_tools1, col_tools2, col_tools3, col_tools4 = st.columns([2, 1, 2, 1])
    with col_tools1:
        st.checkbox("📖 Canon Guardian", key="canon_guardian_on", on_change=autosave, help="Real-time continuity validation against Story Bible")
    with col_tools2:
        if st.button("🔍 Check", key="btn_check_canon", disabled=not st.session_state.canon_guardian_on, use_container_width=True):
            text = (st.session_state.main_text or "").strip()
            if text:
                st.session_state.canon_issues = analyze_canon_conformity(text)
                error_count = sum(1 for i in st.session_state.canon_issues if i['severity'] == 'error')
                warn_count = sum(1 for i in st.session_state.canon_issues if i['severity'] == 'warning')
                st.session_state.ui_notice = f"📖 Found {error_count} error(s), {warn_count} warning(s)"
                autosave()  # Save analysis results
            else:
                st.session_state.ui_notice = "⚠️ No text to check"
                st.session_state.canon_issues = []
    
    with col_tools3:
        st.checkbox("🔥 Voice Heatmap", key="show_voice_heatmap", on_change=autosave, help="Project-wide: Analyzes draft against Voice Bible controls")
    with col_tools4:
        if st.button("🔄 Analyze", key="btn_analyze_heatmap", disabled=not st.session_state.show_voice_heatmap, use_container_width=True):
            text = (st.session_state.main_text or "").strip()
            if text:
                st.session_state.voice_heatmap_data = analyze_voice_conformity(text)
                st.session_state.ui_notice = f"✅ Analyzed {len(st.session_state.voice_heatmap_data)} paragraph(s) • Saved to project"
                autosave()  # Save analysis results with project
            else:
                st.session_state.ui_notice = "⚠️ No text to analyze"
                st.session_state.voice_heatmap_data = []
    
    # Show color-coded text view when heatmap is enabled
    if st.session_state.show_voice_heatmap and st.session_state.voice_heatmap_data:
        st.caption("📊 **Live Heatmap View** (Green = On target, Yellow = Minor issues, Red = Major deviation)")
        
        # Build colored HTML view
        html_parts = ['<div style="background-color: #1e1e1e; padding: 15px; border-radius: 5px; font-family: monospace; line-height: 1.8; max-height: 650px; overflow-y: auto;">']
        
        for para_data in st.session_state.voice_heatmap_data:
            score = para_data["score"]
            # Determine color based on score
            if score >= 85:
                bg_color = "rgba(40, 167, 69, 0.3)"  # Green with transparency
                border_color = "#28a745"
            elif score >= 70:
                bg_color = "rgba(255, 193, 7, 0.3)"  # Yellow with transparency
                border_color = "#ffc107"
            elif score >= 50:
                bg_color = "rgba(253, 126, 20, 0.3)"  # Orange with transparency
                border_color = "#fd7e14"
            else:
                bg_color = "rgba(220, 53, 69, 0.3)"  # Red with transparency
                border_color = "#dc3545"
            
            # Add paragraph with inline background color
            issues_text = f" • {', '.join(para_data['issues'])}" if para_data['issues'] else ""
            html_parts.append(
                f'<div style="background-color: {bg_color}; border-left: 3px solid {border_color}; padding: 8px 12px; margin: 4px 0; border-radius: 3px; color: #e0e0e0;">'
                f'<span style="font-size: 0.8em; color: {border_color}; font-weight: bold;">[{score:.0f}/100{issues_text}]</span><br>'
                f'{para_data["text"]}'
                f'</div>'
            )
        
        html_parts.append('</div>')
        st.markdown(''.join(html_parts), unsafe_allow_html=True)
        
        st.caption("⚠️ Edit in text area below, then click 'Analyze' to update heatmap")
    
    # Display Canon Guardian issues if enabled
    if st.session_state.canon_guardian_on and st.session_state.canon_issues:
        error_count = sum(1 for i in st.session_state.canon_issues if i['severity'] == 'error')
        warn_count = sum(1 for i in st.session_state.canon_issues if i['severity'] == 'warning')
        
        st.warning(f"📖 **Canon Guardian**: {error_count} error(s), {warn_count} warning(s) detected")
        
        for idx, issue in enumerate(st.session_state.canon_issues[:5]):  # Show top 5
            severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
            confidence_color = "#dc3545" if issue['severity'] == 'error' else "#ffc107"
            
            with st.expander(f"{severity_icon} {issue['type'].replace('_', ' ').title()} (Confidence: {issue['confidence']}%)", expanded=idx==0):
                st.markdown(
                    f'<div style="background-color: rgba(220, 53, 69, 0.1); padding: 10px; border-radius: 4px; border-left: 3px solid {confidence_color};">'
                    f'<strong>Issue:</strong> {issue["issue"]}<br><br>'
                    f'<strong>Text:</strong> "{issue["text_snippet"]}..."'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Resolution buttons
                st.caption("**Resolution Options:**")
                res_cols = st.columns(len(issue['resolution_options']))
                for col_idx, option in enumerate(issue['resolution_options']):
                    if res_cols[col_idx].button(option, key=f"resolve_{idx}_{col_idx}", use_container_width=True):
                        if option == "Ignore":
                            # Add to ignored flags
                            flag_id = f"{issue['type']}_{issue['paragraph_index']}_{issue['issue'][:30]}"
                            if "canon_ignored_flags" not in st.session_state:
                                st.session_state.canon_ignored_flags = []
                            st.session_state.canon_ignored_flags.append(flag_id)
                            st.session_state.ui_notice = f"✅ Ignored: {issue['type']}"
                            st.rerun()
                        elif option == "Update Story Bible":
                            st.session_state.ui_notice = "💡 Navigate to Story Bible section to update canon"
                        elif option == "Fix Draft":
                            st.session_state.ui_notice = "💡 Edit the highlighted paragraph in your draft"
                        elif option == "Update Outline":
                            st.session_state.ui_notice = "💡 Navigate to Story Bible → Outline to update"
                        elif option == "Update World":
                            st.session_state.ui_notice = "💡 Navigate to Story Bible → World to update"
        
        if len(st.session_state.canon_issues) > 5:
            st.caption(f"... and {len(st.session_state.canon_issues) - 5} more issues")
    
    # Text area for editing (always shown)
    st.text_area("Draft", key="main_text", height=650 if not (st.session_state.show_voice_heatmap and st.session_state.voice_heatmap_data) else 300, on_change=autosave_with_undo, label_visibility="collapsed")

    # Export Controls
    exp_cols = st.columns([1, 1, 1, 2])
    
    with exp_cols[0]:
        content, title = get_export_content()
        if content.strip():
            txt_data = export_as_txt(content, title)
            st.download_button(
                "📄 TXT",
                data=txt_data,
                file_name=f"{title}.txt",
                mime="text/plain",
                use_container_width=True,
                help="Export current chapter as plain text"
            )
        else:
            st.button("📄 TXT", disabled=True, use_container_width=True, help="No content to export")
    
    with exp_cols[1]:
        if DOCX_AVAILABLE and content.strip():
            try:
                docx_data = export_as_docx(content, title)
                st.download_button(
                    "📘 DOCX",
                    data=docx_data,
                    file_name=f"{title}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    help="Export as Word document"
                )
            except Exception as e:
                st.button("📘 DOCX", disabled=True, use_container_width=True, help=f"Error: {str(e)}")
        else:
            st.button("📘 DOCX", disabled=True, use_container_width=True, help="Install python-docx to enable")
    
    with exp_cols[2]:
        if PDF_AVAILABLE and content.strip():
            try:
                pdf_data = export_as_pdf(content, title)
                st.download_button(
                    "📕 PDF",
                    data=pdf_data,
                    file_name=f"{title}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    help="Export as PDF"
                )
            except Exception as e:
                st.button("📕 PDF", disabled=True, use_container_width=True, help=f"Error: {str(e)}")
        else:
            st.button("📕 PDF", disabled=True, use_container_width=True, help="Install fpdf2 to enable")
    
    with exp_cols[3]:
        # Full manuscript export (if in chapter mode)
        if st.session_state.active_bay in ["ROUGH", "EDIT", "FINAL"] and st.session_state.project_id:
            proj = st.session_state.projects.get(st.session_state.project_id)
            if proj and "chapters" in proj and len(proj["chapters"]) > 1:
                full_content, full_title = export_full_manuscript()
                if full_content.strip():
                    full_txt = export_as_txt(full_content, full_title)
                    st.download_button(
                        "📚 Full Manuscript (TXT)",
                        data=full_txt,
                        file_name=f"{full_title}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Export all chapters as one document"
                    )
                else:
                    st.caption("💡 Export current chapter or full manuscript")
            else:
                st.caption("💡 Single chapter - use buttons on left")
        else:
            st.caption("💡 Export options: TXT, DOCX, PDF")

    # Primary Actions (all respect Voice Bible + AI Intensity)
    b1 = st.columns(5)
    if b1[0].button("Write", key="btn_write", help="Continue writing (Voice Bible controlled)"):
        queue_action("Write")
        st.rerun()
    if b1[1].button("Rewrite", key="btn_rewrite", help="Rewrite for quality (Voice Bible controlled)"):
        queue_action("Rewrite")
        st.rerun()
    if b1[2].button("Expand", key="btn_expand", help="Add depth (Voice Bible controlled)"):
        queue_action("Expand")
        st.rerun()
    if b1[3].button("Rephrase", key="btn_rephrase", help="Rephrase last sentence (Voice Bible controlled)"):
        queue_action("Rephrase")
        st.rerun()
    if b1[4].button("Describe", key="btn_describe", help="Add description (Voice Bible controlled)"):
        queue_action("Describe")
        st.rerun()

    # Secondary Actions
    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell", help="Fix spelling/grammar (Voice Bible controlled)"):
        queue_action("Spell")
        st.rerun()
    if b2[1].button("Grammar", key="btn_grammar", help="Copyedit grammar (Voice Bible controlled)"):
        queue_action("Grammar")
        st.rerun()
    if b2[2].button("Find & Replace", key="btn_find", help="AI-powered find and replace (Voice Bible controlled)"):
        queue_action("Find & Replace")
        st.rerun()
    if b2[3].button("Synonym", key="btn_synonym", help="Get synonyms for last word (Voice Bible aware)"):
        queue_action("Synonym")
        st.rerun()
    if b2[4].button("Sentence", key="btn_sentence", help="Rewrite last sentence options (Voice Bible aware)"):
        queue_action("Sentence")
        st.rerun()
    
    # AI Generation Output Window (beneath command buttons)
    st.divider()
    # Undo/Redo controls
    undo_cols = st.columns([1, 1, 3])
    with undo_cols[0]:
        undo_disabled = st.session_state.undo_position <= 0
        if st.button("↶ Undo", key="undo_btn", disabled=undo_disabled, use_container_width=True, help="Undo last change (Ctrl+Z)"):
            if undo():
                st.rerun()
    with undo_cols[1]:
        redo_disabled = st.session_state.undo_position >= len(st.session_state.undo_history) - 1
        if st.button("↷ Redo", key="redo_btn", disabled=redo_disabled, use_container_width=True, help="Redo last undone change (Ctrl+Y)"):
            if redo():
                st.rerun()
    with undo_cols[2]:
        history_count = len(st.session_state.undo_history)
        position = st.session_state.undo_position + 1
        if history_count > 0:
            st.caption(f"📝 History: {position}/{history_count} states • {len(st.session_state.main_text or '')} characters")
        else:
            st.caption(f"📝 {len(st.session_state.main_text or '')} characters")
    
    st.caption("🤖 AI Generation Output")
    
    # Show generated text with apply/discard options
    if "ai_generated_text" in st.session_state and st.session_state.ai_generated_text:
        gen_mode = st.session_state.get("ai_generation_mode", "append")
        
        st.text_area(
            "Generated by AI",
            value=st.session_state.ai_generated_text,
            height=200,
            key="ai_output_display",
            label_visibility="collapsed"
        )
        
        action_cols = st.columns([1, 1, 2])
        if action_cols[0].button("✅ Apply", key="apply_ai", use_container_width=True):
            push_undo_state()  # Save state before applying
            if gen_mode == "replace":
                st.session_state.main_text = st.session_state.ai_generated_text
            else:  # append
                if (st.session_state.main_text or "").strip():
                    st.session_state.main_text = (st.session_state.main_text.rstrip() + "\n\n" + st.session_state.ai_generated_text).strip()
                else:
                    st.session_state.main_text = st.session_state.ai_generated_text
            st.session_state.ai_generated_text = ""
            st.session_state.voice_status = "Applied AI generation to draft"
            autosave()
            st.rerun()
        
        if action_cols[1].button("❌ Discard", key="discard_ai", use_container_width=True):
            st.session_state.ai_generated_text = ""
            st.session_state.voice_status = "Discarded AI generation"
            st.rerun()
        
        action_cols[2].caption(f"Mode: {gen_mode.upper()} | Ready to apply or discard")
    else:
        st.text_area(
            "Waiting for AI generation...",
            value="",
            height=200,
            disabled=True,
            key="ai_output_empty",
            label_visibility="collapsed",
            placeholder="AI-generated text will appear here. Use the buttons above to generate content."
        )


# ============================================================
# RIGHT — VOICE BIBLE (Tabbed Interface)
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")
    st.caption("Your intelligent, trainable author engine. Each control adapts to your writing.")
    
    # Voice Bible Status Summary
    active_controls = []
    if st.session_state.vb_style_on:
        active_controls.append(f"Style:{st.session_state.writing_style}")
    if st.session_state.vb_genre_on:
        active_controls.append(f"Genre:{st.session_state.genre}")
    if st.session_state.vb_trained_on and st.session_state.trained_voice != "— None —":
        active_controls.append(f"🎤{st.session_state.trained_voice}")
    if st.session_state.vb_match_on:
        active_controls.append(f"✨Match")
    if st.session_state.vb_technical_on:
        active_controls.append(f"⚙️{st.session_state.pov}/{st.session_state.tense}")

    if active_controls:
        st.success("✅ " + " • ".join(active_controls))
    else:
        st.warning("⚠️ No controls active")

    # Voice Bible Tabs
    vb_tabs = st.tabs(["🎛️ Presets", "✍️ Style", "🎭 Genre", "🧬 Voice", "✨ Match", "⚙️ Tech"])
    
    # Tab 0: Presets
    with vb_tabs[0]:
        st.caption("Quick configuration presets")
        pcol1, pcol2, pcol3 = st.columns(3)
        if pcol1.button("Subtle", key="vb_preset_subtle", use_container_width=True):
            st.session_state.style_intensity = 0.3
            st.session_state.match_intensity = 0.3
            autosave()
            st.rerun()
        if pcol2.button("Balanced", key="vb_preset_balanced", use_container_width=True):
            st.session_state.style_intensity = 0.55
            st.session_state.match_intensity = 0.55
            autosave()
            st.rerun()
        if pcol3.button("Bold", key="vb_preset_bold", use_container_width=True):
            st.session_state.style_intensity = 0.78
            st.session_state.match_intensity = 0.78
            autosave()
            st.rerun()
    
    # Tab 1: Writing Style Engine
    with vb_tabs[1]:
        st.checkbox("Enable Writing Style", key="vb_style_on", on_change=autosave)
        
        st.selectbox(
            "Writing Style",
            ENGINE_STYLES,
            key="writing_style",
            disabled=not st.session_state.vb_style_on,
            on_change=autosave,
        )
        
        st.slider(
            "Style Intensity", 
            0.0, 1.0, 
            key="style_intensity", 
            disabled=not st.session_state.vb_style_on, 
            on_change=autosave,
        )

        
        # Style Bank Training (nested expander within tab)
        with st.expander("🎨 Train This Style", expanded=False):
            st.caption("Add samples to train this style")
            
            s_cols = st.columns([1.5, 1.0])
            st_lane = s_cols[0].selectbox("Lane", LANES, key="style_train_lane")
            split_mode = s_cols[1].selectbox("Split", ["Paragraphs", "Whole"], key="style_train_split")
            
            paste = st.text_area("Training text", key="style_train_paste", height=140, placeholder="Paste sample text...")
            
            if st.button("Add Samples", key="style_train_add", use_container_width=True):
                src = _normalize_text((paste or "").strip())
                if src.strip():
                    n = add_style_samples(st.session_state.writing_style, st_lane, src, split_mode=split_mode)
                    st.session_state.ui_notice = f"✅ Added {n} sample(s)"
                    autosave()
                    st.rerun()
    
    # Tab 2: Genre Intelligence
    with vb_tabs[2]:
        st.checkbox("Enable Genre Influence", key="vb_genre_on", on_change=autosave)
        
        st.selectbox(
            "Genre",
            ["Literary", "Noir", "Thriller", "Comedy", "Lyrical", "Horror", "Romance", "SciFi", "Fantasy"],
            key="genre",
            disabled=not st.session_state.vb_genre_on,
            on_change=autosave,
        )
        
        st.slider(
            "Genre Intensity", 
            0.0, 1.0, 
            key="genre_intensity", 
            disabled=not st.session_state.vb_genre_on, 
            on_change=autosave,
        )
    
    # Tab 3: Trained Voice (Vector Matching)
    with vb_tabs[3]:
        st.checkbox("Enable Trained Voice", key="vb_trained_on", on_change=autosave)
        
        trained_options = voice_names_for_selector()
        if st.session_state.trained_voice not in trained_options:
            st.session_state.trained_voice = "— None —"
        
        st.selectbox(
            "Trained Voice",
            trained_options,
            key="trained_voice",
            disabled=not st.session_state.vb_trained_on,
            on_change=autosave,
        )
        
        st.slider(
            "Voice Intensity",
            0.0, 1.0,
            key="trained_intensity",
            disabled=not st.session_state.vb_trained_on,
            on_change=autosave,
        )
        
        # Voice Vault training (nested expander)
        with st.expander("🧬 Train Voice Vault", expanded=False):
            st.caption("Add samples to voice vault")
            
            existing_voices = [v for v in (st.session_state.voices or {}).keys()]
            existing_voices = sorted(existing_voices, key=lambda x: (x not in ("Voice A", "Voice B"), x))
            if not existing_voices:
                existing_voices = ["Voice A", "Voice B"]
            
            vault_voice = st.selectbox("Vault voice", existing_voices, key="vault_voice_sel")
            lane = st.selectbox("Lane", LANES, key="vault_lane_sel")
            sample = st.text_area("Sample", key="vault_sample_text", height=140, placeholder="Paste voice sample...")
            
            if st.button("Add Sample", key="vault_add_sample", use_container_width=True):
                if add_voice_sample(vault_voice, lane, sample):
                    st.session_state.ui_notice = f"✅ Added to {vault_voice}"
                    queue_action("__VAULT_CLEAR_SAMPLE__")
                    autosave()
                    st.rerun()
    
    # Tab 4: Match My Style (One-Shot)
    with vb_tabs[4]:
        st.checkbox("Enable Match My Style", key="vb_match_on", on_change=autosave)
        
        st.text_area(
            "Style Example",
            key="voice_sample",
            height=300,
            max_chars=15000,
            disabled=not st.session_state.vb_match_on,
            on_change=autosave,
            placeholder="Paste your best writing (up to 2000 words)...",
        )
        
        if st.button("🔍 Analyze", key="analyze_style_btn", disabled=not st.session_state.vb_match_on):
            text = (st.session_state.voice_sample or "").strip()
            if text:
                samples = analyze_style_samples(text)
                st.session_state.analyzed_style_samples = samples
                st.session_state.ui_notice = f"✅ Found {len(samples)} samples"
            st.rerun()
        
        st.slider(
            "Match Intensity", 
            0.0, 1.0, 
            key="match_intensity", 
            disabled=not st.session_state.vb_match_on, 
            on_change=autosave,
        )
    
    # Tab 5: Technical Controls (POV/Tense)
    with vb_tabs[5]:
        st.checkbox("Enable Technical Controls", key="vb_technical_on", on_change=autosave)
        
        col_tech1, col_tech2 = st.columns(2)
        with col_tech1:
            st.selectbox(
                "POV", 
                ["First", "Close Third", "Omniscient"], 
                key="pov",
                disabled=not st.session_state.vb_technical_on,
                on_change=autosave,
            )
        with col_tech2:
            st.selectbox(
                "Tense", 
                ["Past", "Present"], 
                key="tense",
                disabled=not st.session_state.vb_technical_on,
                on_change=autosave,
            )
        
        st.slider(
            "Technical Enforcement",
            0.0, 1.0,
            key="technical_intensity",
            disabled=not st.session_state.vb_technical_on,
            on_change=autosave,
        )


# ============================================================
# SAFETY NET SAVE EVERY RERUN
# ============================================================
save_all_to_disk()
