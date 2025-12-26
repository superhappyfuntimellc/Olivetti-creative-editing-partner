# Olivetti Creative Editing Partner - AI Coding Guidelines

## Architecture Overview

Olivetti is a modular Streamlit app for AI-powered creative writing. The system uses a "spiderweb" architecture where all AI features route through a unified Voice Bible system.

### Core Module Pattern (Lines 240-306 in app.py)

```python
# Optional imports with graceful degradation
try:
    from voice_bible import build_partner_brief
    HAS_VOICE_BIBLE_MODULE = True
except ImportError:
    HAS_VOICE_BIBLE_MODULE = False
    # Falls back to inline implementation
```

**Key modules**: `voice_bible.py` (AI briefs), `voice_vault.py` (semantic storage), `style_banks.py` (exemplars), `story_bible.py` (canon), `ai_gateway.py` (OpenAI interface), `config.py`, `performance.py`, `analytics.py`

## Critical Workflows

### Setup & Dependencies
```bash
pip install -r requirements.txt                    # Install all dependencies
streamlit run app.py                               # Start the app (port 8501)
```

**API Key Setup**: Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxx"
```

### Startup Validation (Lines 1097-1160 in app.py)
The app includes `check_startup_requirements()` that validates:
1. OpenAI SDK installation
2. API key configuration (detects placeholder "your-api-key-here")
3. Shows persistent error/warning messages (not fleeting)

## Project-Specific Conventions

### 1. AI Generation Flow
**All AI actions** → `build_partner_brief(action, lane)` → `call_openai(brief, task, text)` → OpenAI API

The Voice Bible controls (AI Intensity, Writing Style, Genre, etc.) are assembled into a 500+ line system prompt by `build_partner_brief()`.

### 2. Multi-Bay System
Projects flow through 4 bays: `NEW` → `ROUGH` → `EDIT` → `FINAL`. State is in `st.session_state.active_bay`.

### 3. Lane-Based Context Detection
Writing is categorized into lanes: `Dialogue`, `Narration`, `Interiority`, `Action`. The `current_lane_from_draft()` function detects context automatically.

### 4. Error Handling Pattern
```python
class OlivettiError(Exception): pass
class AIServiceError(OlivettiError): pass
class DataValidationError(OlivettiError): pass
class StorageError(OlivettiError): pass

@safe_execute(func_name="operation", fallback_value=None, show_error=True)
def operation():
    # Function with automatic error handling and UI feedback
```

### 5. Autosave Architecture
- 5-level rotating backups: `.bak1` through `.bak5`
- State persists in `autosave/olivetti_state.json`
- Never delete autosave files without explicit user request

## Integration Points

### OpenAI API
- Model: `gpt-4o-mini` (configurable via `OPENAI_MODEL` env var or secrets)
- Temperature mapping: AI Intensity (0.0-1.0) → Temperature (0.3-1.2) via `temperature_from_intensity()`
- Rate limiting: 10 calls/min default (see `performance.py`)

### Session State Keys
Critical state: `project_id`, `active_bay`, `main_text`, `ai_intensity`, `voice_bible` (dict of controls), `voice_vault` (nested dict), `style_banks`, `story_bible`

## Key Files

- **app.py** (5000+ lines): Main orchestrator, UI, inline fallback implementations
- **ARCHITECTURE.md**: Complete module guide with examples
- **SETUP_API_KEY.md**: User-facing API key setup guide (reference for error messages)
- **requirements.txt**: Pin versions exactly as specified (openai>=2.0.0)

## Common Modifications

### Adding New AI Actions
1. Create system prompt in `build_partner_brief()` or separate function
2. Call `call_openai(brief, task, text)` with Voice Bible controls
3. Handle response and update `st.session_state.main_text`
4. Trigger `autosave()` after modification

### Adding New Voice Bible Controls
1. Add slider/selectbox in UI section (~line 4800+)
2. Store in `st.session_state.voice_bible[control_name]`
3. Reference in `build_partner_brief()` to include in system prompt
4. Update `_get_voice_bible_summary()` for status display

## Security & Data Protection

- **Never commit** `.streamlit/secrets.toml` (in .gitignore)
- Validate all text inputs via `validate_text_input(text, field_name, max_length, min_length)`
- API keys checked via `has_openai_key()` before operations
- File uploads limited to `MAX_UPLOAD_BYTES` (50MB default)

## Documentation Standards

- Doc existing in ARCHITECTURE.md, SETUP_API_KEY.md, QUICK_START.md
- Use emoji headers for visual scanning (🔑, ✅, ⚠️, 🚀)
- Code examples in markdown for key patterns
- Keep README.md updated with troubleshooting section
