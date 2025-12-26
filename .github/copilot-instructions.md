# Olivetti Creative Editing Partner - AI Agent Instructions

## Architecture Overview
Olivetti is a modular Streamlit-based AI creative writing assistant. Core modules: `app.py` (UI orchestrator), `voice_bible.py` (AI brief construction), `voice_vault.py` (semantic voice storage), `style_banks.py` (exemplar training), `story_bible.py` (canon management), `ai_gateway.py` (OpenAI interface), `config.py`, `performance.py`, `analytics.py`.

**Key principle**: All AI actions route through `build_partner_brief()` → `call_openai()` for unified voice control.

## Development Commands
```bash
streamlit run app.py  # Start development server
```
No test suite currently exists. Manually verify UI changes via browser.

## Code Patterns

### Error Handling
Use `@safe_execute` decorator for functions that may fail:
```python
@safe_execute("operation_name", fallback_value=None, show_error=True)
def my_function():
    # Your code here
```
All OpenAI calls include retry logic (see `ai_gateway.py`).

### State Management
Everything in `st.session_state`. Key structures:
- `st.session_state.voice_vault[voice_name][lane]` - Voice samples with vectors
- `st.session_state.style_banks[bank_name][lane]` - Style exemplars
- `st.session_state.projects[bay_num]` - Multi-bay project system
- `st.session_state.ai_intensity` - Controls OpenAI temperature (0.0-1.0)

### AI Integration Pattern
1. Build brief: `brief = build_partner_brief(action, lane)` (in `voice_bible.py`)
2. Call API: `result = call_openai(brief, task, text)` (in `ai_gateway.py`)
3. Map intensity: `temperature_from_intensity(x)` converts 0.0-1.0 → 0.3-1.2

### Semantic Search
Both Voice Vault and Style Banks use lightweight trigram-based vectors (`_simple_vec()` or `_hash_vec()`). Retrieval uses cosine similarity with lane mixing (60% exact lane, 20% Narration, 20% other).

### Optional Dependencies
Use feature flags for optional packages (pattern in lines 120-145 of `app.py`):
```python
try:
    from some_package import SomeClass
    FEATURE_AVAILABLE = True
except ImportError:
    FEATURE_AVAILABLE = False
```
Then check `if FEATURE_AVAILABLE:` before using features. Applied to: DOCX export, EPUB export, gTTS audio, and other optional features.

## UI Conventions
- Olivetti-inspired monospace design (IBM Plex Mono)
- Four narrative lanes: Dialogue, Narration, Interiority, Action
- Voice Bible controls in sidebar (AI Intensity, Style, Genre, etc.)
- Multi-bay project system (switchable tabs at top)

## Configuration
All config in `config.py` via environment variables. Defaults work out-of-box. API key from `OPENAI_API_KEY` env or secrets.toml.

## File Organization
- Documentation: `ARCHITECTURE.md`, `QUICK_START.md`, `MIGRATION_COMPLETE.md`, `PRODUCTION_COMPLETE.md`
- Main UI: `app.py` (5345 lines, orchestration only)
- Core modules: 8 focused files (200-400 lines each)
- Auto-save: `autosave/` directory with rotating `.bak1` through `.bak5` backups
