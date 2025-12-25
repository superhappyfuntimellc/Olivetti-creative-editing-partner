# Olivetti Creative Editing Partner

## Architecture Overview

Olivetti has been refactored from a monolithic prototype into a **production-grade modular system** while maintaining backward compatibility and single-file deployment.

### Module Structure

```
superhappyfuntimellc/
├── app.py                  # Main orchestrator (UI + integration)
├── voice_bible.py         # AI brief construction & settings
├── voice_vault.py         # Semantic voice storage & retrieval
├── style_banks.py         # Exemplar-based style training
├── story_bible.py         # Canon management & project model
├── ai_gateway.py          # Unified OpenAI interface
├── config.py              # Configuration management
├── performance.py         # Monitoring, caching, rate limiting
├── analytics.py           # Usage tracking & insights
└── prompts.py             # (Legacy) Prompt templates
```

### Core Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Backward Compatibility**: All existing functionality preserved
3. **Optional Dependencies**: Modules gracefully degrade if imports fail
4. **Production-Ready**: Error handling, logging, validation, caching
5. **Single-File Option**: Can still run as monolith by keeping all code in app.py

---

## Module Responsibilities

### `voice_bible.py` - Intelligent Author Engine

**Purpose**: Unified AI brief construction that combines all Voice Bible controls

**Key Functions**:
- `build_partner_brief(action, lane)` - Assembles complete 500+ line system prompt
- `temperature_from_intensity(x)` - Maps AI Intensity to OpenAI temperature
- `get_voice_bible_summary()` - Status display for UI
- `engine_style_directive(style)` - Generates prose-level style instructions

**Voice Bible Controls**:
1. **AI Intensity**: 0.0-1.0 slider → temperature (0.1-1.1)
2. **Writing Style**: NARRATIVE | DESCRIPTIVE | EMOTIONAL | LYRICAL
3. **Genre Influence**: Literary, Commercial, Thriller, Romance, Fantasy, SciFi
4. **Trained Voice**: Semantic retrieval from Voice Vault
5. **Style Banks**: Exemplar-based learning
6. **Match My Style**: One-shot adaptation to user sample
7. **Voice Lock**: Hard constraints (mandatory rules)
8. **Technical Controls**: POV/Tense enforcement

**Integration**: All AI actions route through `build_partner_brief()` → `call_openai()`

---

### `voice_vault.py` - Semantic Voice Storage

**Purpose**: Store and retrieve writing samples using semantic vector search

**Key Functions**:
- `add_voice_sample(voice, lane, text)` - Add training sample
- `retrieve_mixed_exemplars(voice, lane, query)` - Semantic retrieval with lane mixing
- `get_voice_vault_stats(voice)` - Per-lane sample counts
- `create_voice()`, `delete_voice()` - Voice management

**Features**:
- Per-voice, per-lane storage (Dialogue, Narration, Interiority, Action)
- Lightweight trigram-based vectors (no external dependencies)
- LRU cache for vector computations
- Mixed lane retrieval (60% exact, 20% Narration, 10% Interiority, 10% other)

**Storage**: `st.session_state.voice_vault[voice_name][lane] = [samples...]`

---

### `style_banks.py` - Exemplar-Based Training

**Purpose**: Store style exemplars and retrieve similar samples for AI guidance

**Key Functions**:
- `add_style_exemplar(bank, lane, text)` - Add exemplar
- `retrieve_style_exemplars(bank, lane, query, k)` - Top-k semantic matches
- `create_style_bank()`, `delete_style_bank()` - Bank management

**Features**:
- Similar to Voice Vault but focused on stylistic patterns
- Semantic vector matching using cosine similarity
- Per-lane exemplar storage

**Storage**: `st.session_state.style_banks[bank_name][lane] = [exemplars...]`

---

### `story_bible.py` - Canon Management

**Purpose**: Manage story world, characters, outline, and project structure

**Key Functions**:
- `get_story_bible_text()` - Assemble canon context for AI briefs
- `update_story_bible_section(key, content)` - Update synopsis/world/characters/etc
- `create_project(title, bay)` - Create new project
- `list_projects_in_bay(bay)` - Get projects in NEW/ROUGH/EDIT/FINAL
- `story_bible_markdown(title, sb, meta)` - Export to markdown

**Story Bible Sections**:
1. Synopsis
2. Genre & Style Notes
3. World
4. Characters
5. Outline

**Features**:
- Content fingerprinting for change detection
- Multi-bay project system (NEW → ROUGH → EDIT → FINAL)
- Workspace mode vs. project mode

**Storage**: `st.session_state.projects[proj_id]["story_bible"]`

---

### `ai_gateway.py` - Unified OpenAI Interface

**Purpose**: Single gateway for all AI calls with production safeguards

**Key Function**:
- `call_openai(system_brief, user_task, text, temp?)` - Make AI request

**Features**:
1. **Rate Limiting**: Check rate limiter before each call
2. **Input Validation**: Max 100k chars for briefs, 10k for tasks
3. **Retry Logic**: 3 attempts with exponential backoff
4. **Error Classification**: Rate limit / auth / timeout / general
5. **Performance Tracking**: Log response times and token usage
6. **Temperature Override**: Use AI Intensity or explicit value

**Error Handling**:
- Raises `APIError` with classified error messages
- Don't retry on rate limits (429) or auth failures (401)
- Retry on timeouts and transient errors

**Integration**: ALL AI actions route through this gateway

---

### `config.py` - Configuration Management

**Purpose**: Centralized settings with environment variable support

**Key Features**:
- OpenAI API key and model configuration
- Storage paths and file limits
- Rate limiting settings (default: 10 calls/min)
- Logging configuration (olivetti.log with rotation)
- Feature flags (voice vault, style banks, analytics)
- Performance settings (cache TTL, monitoring)

**Usage**:
```python
from config import Config
cfg = Config()
print(cfg.OPENAI_MODEL)  # "gpt-4o-mini"
cfg.validate()  # Check configuration
```

---

### `performance.py` - Performance Layer

**Purpose**: Monitoring, caching, and rate limiting

**Components**:

1. **PerformanceMonitor**:
   - Track AI call latencies
   - Cache hit/miss ratios
   - Autosave frequency
   - Export statistics

2. **RateLimiter**:
   - Sliding window rate limiting
   - Configurable calls per minute
   - Wait time calculation

3. **Decorators**:
   - `@cache_result(ttl_seconds)` - Time-based caching
   - `@timed_execution` - Slow operation detection

**Usage**:
```python
perf_monitor = PerformanceMonitor()
rate_limiter = RateLimiter(max_calls_per_minute=10)

can_proceed, wait_time = rate_limiter.check_rate_limit()
```

---

### `analytics.py` - Usage Tracking

**Purpose**: Privacy-focused analytics for insights and debugging

**Components**:

1. **UsageAnalytics**:
   - Session-level event tracking
   - Writing action statistics (Write, Rewrite, Expand, Trim)
   - Word count changes
   - Export to JSON

2. **ProjectAnalytics**:
   - Project-level metrics (word count, edit sessions)
   - Cross-project analysis
   - Trend identification

**Events Tracked**:
- `write`, `rewrite`, `expand`, `trim` with metadata:
  - word_count
  - words_changed / words_added
  - lane (Dialogue/Narration/Interiority/Action)
  - use_ai (boolean)

**Privacy**: No text content stored, only metadata

---

## Data Flow

### Complete AI Generation Pipeline

```
User Action (e.g., "Write")
    ↓
partner_action(action="Write")
    ↓
build_partner_brief(action="Write", lane="Narration")  [voice_bible.py]
    ├→ AI Intensity → temperature_from_intensity()
    ├→ Writing Style → engine_style_directive()
    ├→ Genre Influence → genre_notes
    ├→ Voice Vault → retrieve_mixed_exemplars()  [voice_vault.py]
    ├→ Style Banks → retrieve_style_exemplars()  [style_banks.py]
    ├→ Match My Style → analyzed samples
    ├→ Voice Lock → hard constraints
    ├→ Technical Controls → POV/Tense
    └→ Story Bible → get_story_bible_text()  [story_bible.py]
    ↓
call_openai(brief, task, text)  [ai_gateway.py]
    ├→ Rate limit check  [performance.py]
    ├→ Input validation
    ├→ OpenAI API call with retries
    └→ Performance tracking
    ↓
AI Response → Apply to draft
    ↓
Analytics tracking  [analytics.py]
    ↓
Autosave with rotating backups
```

---

## Production Features

### ✅ Completed Upgrades

1. **Error Handling & Logging**
   - Custom exception hierarchy (`OlivettiError`, `APIError`, `ValidationError`)
   - `@safe_execute` decorator with fallback values
   - Rotating log file (`olivetti.log`, 5MB × 3 backups)

2. **Data Validation**
   - `validate_text_input()` with length limits
   - `validate_dict()` for structured data
   - File upload size limits (10MB)

3. **Performance Optimizations**
   - `@lru_cache(maxsize=1024)` for vector computations
   - `PerformanceMonitor` tracking response times
   - `@cache_result` decorator for expensive operations

4. **Configuration Management**
   - `Config` class with environment variables
   - Centralized settings with validation
   - Feature flags for optional components

5. **Backup/Recovery**
   - Rotating 5-level backups (`.bak1` through `.bak5`)
   - Resilient load trying all backup files
   - Atomic write with temp files

6. **Rate Limiting**
   - `RateLimiter` with sliding window
   - Pre-call checks preventing 429 errors
   - Configurable limits (default: 10/min)

7. **Analytics & Tracking**
   - Session-level usage statistics
   - Project-level insights
   - Event metadata (word counts, lane, AI usage)

8. **Modular Architecture**
   - 8 focused modules with clear responsibilities
   - Backward compatible with monolithic deployment
   - Optional dependencies with graceful degradation

---

## Usage Examples

### Adding a Voice Sample

```python
from voice_vault import add_voice_sample

success = add_voice_sample(
    voice_name="Hemingway",
    lane="Narration",
    sample_text="The sun also rises. It was a fine morning..."
)
```

### Retrieving Style Exemplars

```python
from style_banks import retrieve_style_exemplars

exemplars = retrieve_style_exemplars(
    style_bank="Literary Fiction",
    lane="Interiority",
    query="She felt the weight of silence...",
    k=2
)
```

### Building an AI Brief

```python
from voice_bible import build_partner_brief

brief = build_partner_brief(
    action_name="Write",
    lane="Dialogue"
)
# Returns 500+ line system prompt with all Voice Bible settings
```

### Making an AI Call

```python
from ai_gateway import call_openai

result = call_openai(
    system_brief=brief,
    user_task="Write 200 words of tense dialogue",
    text="[Current draft text...]",
    temperature=0.8  # Optional override
)
```

---

## Migration Notes

### Importing from New Modules

**Old** (monolithic):
```python
# Everything in app.py
from app import build_partner_brief, call_openai
```

**New** (modular):
```python
from voice_bible import build_partner_brief
from ai_gateway import call_openai
from voice_vault import add_voice_sample, retrieve_mixed_exemplars
from style_banks import retrieve_style_exemplars
from story_bible import get_story_bible_text, create_project
```

### Backward Compatibility

All functions remain accessible from `app.py` via re-exports:

```python
# Still works for backward compatibility
from app import build_partner_brief, call_openai
```

### Single-File Deployment

To deploy as single file, simply keep all code in `app.py`:

```bash
# Copy module contents into app.py sections
cat voice_bible.py >> app.py
cat voice_vault.py >> app.py
# etc.
```

---

## Testing

### Running the App

```bash
streamlit run app.py
```

### Checking Logs

```bash
tail -f olivetti.log
```

### Performance Stats

```python
# In Streamlit app
if hasattr(st.session_state, 'perf_monitor'):
    stats = st.session_state.perf_monitor.get_stats()
    st.write(stats)
```

### Analytics Export

```python
# In Streamlit app
if hasattr(st.session_state, 'analytics'):
    data = st.session_state.analytics.export_analytics()
    # Save to JSON
```

---

## Future Enhancements

### Potential Improvements

1. **Async AI Calls**: Use `asyncio` for parallel generation
2. **Vector Database**: Replace trigrams with embeddings (e.g., sentence-transformers)
3. **Cloud Storage**: S3/GCS for project persistence
4. **Collaboration**: Multi-user editing with conflict resolution
5. **A/B Testing**: Compare Voice Bible configurations
6. **Cost Tracking**: Token usage and cost estimation
7. **Undo/Redo**: Full edit history with branching
8. **Export Formats**: PDF, EPUB, LaTeX

### Plugin Architecture

Consider adding plugin system for:
- Custom lane types
- Alternative AI providers (Anthropic, Cohere)
- Additional training methods
- Export templates

---

## Troubleshooting

### Common Issues

**Import errors**:
```
ModuleNotFoundError: No module named 'voice_bible'
```
→ Ensure all `.py` files are in same directory as `app.py`

**API errors**:
```
APIError: OPENAI_API_KEY not configured
```
→ Set environment variable: `export OPENAI_API_KEY=sk-...`

**Rate limiting**:
```
APIError: Rate limit exceeded. Wait 30s before next call.
```
→ Increase `max_calls_per_minute` in config or wait

**Performance issues**:
- Check `olivetti.log` for slow operations
- Increase cache size: `@lru_cache(maxsize=2048)`
- Disable analytics if too slow

---

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Add error handling with `@safe_execute`

### Testing Checklist

- [ ] Run `streamlit run app.py` without errors
- [ ] Test all Voice Bible controls
- [ ] Verify autosave and backup recovery
- [ ] Check `olivetti.log` for errors
- [ ] Validate analytics tracking
- [ ] Test import/export

### Pull Request Template

```markdown
## Summary
Brief description of changes

## Modules Affected
- [ ] voice_bible.py
- [ ] voice_vault.py
- [ ] app.py

## Testing
- [ ] Manual testing completed
- [ ] Backward compatibility verified
- [ ] No breaking changes

## Performance Impact
Expected impact on response time / memory
```

---

## License

[Your License Here]

## Credits

Built with ❤️ using Streamlit and OpenAI
