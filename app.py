import os
import re
import streamlit as st
from datetime import datetime

# ============================================================
# ENV / METADATA HYGIENE (prevents "undefined" app-id artifacts)
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

# Optional: set your model + key via Streamlit Secrets or env vars
# In Streamlit Cloud: Settings -> Secrets -> OPENAI_API_KEY="..."
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # change if you want

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti Desk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# AUTHOR-GRADE SCALE (BIGGER / BETTER) — NO LAYOUT CHANGES
# ============================================================
st.markdown(
    """
    <style>
    /* Writing desk typography + comfort */
    div[data-testid="stTextArea"] textarea {
      font-size: 18px !important;
      line-height: 1.65 !important;
      padding: 18px !important;
      resize: vertical !important;   /* central writing window expandable */
      min-height: 520px !important;
    }

    /* Button ergonomics */
    button[kind="secondary"], button[kind="primary"] {
      font-size: 16px !important;
      padding: 0.6rem 0.9rem !important;
    }

    /* Control labels readability */
    label, .stSelectbox label, .stSlider label {
      font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# SESSION STATE INIT
# ============================================================
def init_state():
    defaults = {
        # Main writing
        "main_text": "",
        "autosave_time": None,

        # Story Bible
        "junk": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",

        # Voice Bible — toggles
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_lock_on": False,

        # Voice Bible — selections
        "writing_style": "Neutral",
        "genre": "Literary",
        "trained_voice": "— None —",
        "voice_sample": "",
        "voice_lock_prompt": "",

        # Voice Bible — intensities
        "style_intensity": 0.6,
        "genre_intensity": 0.6,
        "trained_intensity": 0.7,
        "match_intensity": 0.8,
        "lock_intensity": 1.0,

        # POV / Tense
        "pov": "Close Third",
        "tense": "Past",

        # UI
        "focus_mode": False,

        # Partner engine state
        "stage": "Rough",          # Rough | Edit | Final
        "last_action": "—",
        "revisions": [],           # list of dicts: {ts, action, text}
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Free writing always: permanently disable hard focus behavior
st.session_state.focus_mode = False

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")

# ============================================================
# REVISION VAULT (non-destructive)
# ============================================================
def push_revision(action_name: str):
    """Store snapshot BEFORE applying a transformation."""
    snap = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_name,
        "text": st.session_state.main_text,
    }
    st.session_state.revisions.append(snap)
    # Keep last 50 snapshots
    if len(st.session_state.revisions) > 50:
        st.session_state.revisions = st.session_state.revisions[-50:]

def set_last_action(action_name: str):
    st.session_state.last_action = action_name

# ============================================================
# PARTNER CORE — Context Assembly (Story Bible + Voice Bible)
# ============================================================
def build_partner_brief() -> str:
    """Builds authoritative instruction set. No UI changes."""
    sb = []
    if st.session_state.synopsis.strip():
        sb.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if st.session_state.genre_style_notes.strip():
        sb.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if st.session_state.world.strip():
        sb.append(f"WORLD:\n{st.session_state.world.strip()}")
    if st.session_state.characters.strip():
        sb.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if st.session_state.outline.strip():
        sb.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
    story_bible = "\n\n".join(sb).strip()

    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice != "— None —":
        vb.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {st.session_state.trained_intensity:.2f})")
    if st.session_state.vb_match_on and st.session_state.voice_sample.strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and st.session_state.voice_lock_prompt.strip():
        vb.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_bible = "\n\n".join(vb).strip()

    stage = st.session_state.stage
    pov = st.session_state.pov
    tense = st.session_state.tense

    brief = f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
This is professional production work. Be decisive, specific, and useful.

ABSOLUTE RULES:
- Never change UI. Never mention UI.
- Never output meta-commentary.
- Do not remove meaning or voice.
- Avoid clichés unless the author’s Voice Bible explicitly demands them.
- When editing, preserve intent and specificity. Tighten, don't sterilize.

WORKING MODE: {stage}
POV: {pov}
TENSE: {tense}

VOICE BIBLE (controls):
{voice_bible if voice_bible else "— None enabled —"}

STORY BIBLE (canon/constraints):
{story_bible if story_bible else "— None provided —"}
""".strip()
    return brief

# ============================================================
# PARTNER CORE — Text Utilities (for local fallback)
# ============================================================
def _split_paragraphs(text: str):
    # Keep paragraph breaks
    return re.split(r"\n\s*\n", text.strip(), flags=re.MULTILINE) if text.strip() else []

def _join_paragraphs(paras):
    return ("\n\n".join([p.strip() for p in paras if p is not None])).strip()

def _last_sentence(text: str) -> str:
    t = text.strip()
    if not t:
        return ""
    # crude sentence split that respects common punctuation
    parts = re.split(r"(?<=[.!?])\s+", t)
    return parts[-1].strip() if parts else t

def _local_cleanup(text: str) -> str:
    """Professional mechanical cleanup: spacing, quotes, dashes, repeated whitespace."""
    t = text

    # Normalize line endings
    t = t.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse trailing spaces
    t = re.sub(r"[ \t]+\n", "\n", t)

    # Collapse excessive blank lines (keep max 2)
    t = re.sub(r"\n{4,}", "\n\n\n", t)

    # Smart-ish punctuation spacing
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,.;:!?])([A-Za-z0-9])", r"\1 \2", t)

    # Convert triple dots to ellipsis
    t = re.sub(r"\.\.\.", "…", t)

    # Normalize dashes (space em dash)
    t = re.sub(r"\s*--\s*", " — ", t)

    # Tighten multiple spaces
    t = re.sub(r"[ \t]{2,}", " ", t)

    return t.strip()

def _local_rephrase_sentence(sentence: str) -> str:
    """Lightweight rephrase: tighten filler and strengthen verbs (heuristic)."""
    s = sentence.strip()
    if not s:
        return s
    # Remove some common weak openers/fillers (conservative)
    s = re.sub(r"^(Just|Really|Basically|Actually|Suddenly|Very)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(seems to|started to|began to)\b", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(very)\b\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

# ============================================================
# PARTNER CORE — OpenAI (optional)
# ============================================================
def _call_openai(system_brief: str, user_task: str, text: str) -> str:
    """
    Optional AI partner. If OPENAI_API_KEY isn't set, we won't call this.
    Uses the official OpenAI Python SDK if available; otherwise raises.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. Add to requirements.txt: openai") from e

    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [
        {"role": "system", "content": system_brief},
        {"role": "user", "content": f"{user_task}\n\nDRAFT:\n{text.strip()}"},
    ]

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7 if st.session_state.stage == "Rough" else 0.3,
    )
    return (resp.choices[0].message.content or "").strip()

# ============================================================
# PARTNER CORE — Actions (wired to existing buttons)
# ============================================================
def partner_action(action: str):
    """
    Applies action to main_text.
    Non-destructive: stores previous snapshot first.
    """
    text = st.session_state.main_text or ""
    brief = build_partner_brief()

    # Authoritative tasks per stage
    stage = st.session_state.stage

    # If no AI key/sdk, do local fallback for certain actions.
    use_ai = bool(OPENAI_API_KEY)

    def apply_result(result: str):
        if result and result.strip():
            st.session_state.main_text = result.strip()
            autosave()
            set_last_action(action)

    # Always snapshot before change
    push_revision(action)

    # --- WRITE (continue or start) ---
    if action == "Write":
        if use_ai:
            task = (
                "Continue the draft in the same voice and momentum. "
                "Add 1–3 paragraphs. Do not recap. Do not explain. Just produce prose."
            )
            out = _call_openai(brief, task, text if text.strip() else "Start the opening.")
            # Append to preserve what already exists
            if text.strip():
                apply_result((text.rstrip() + "\n\n" + out).strip())
            else:
                apply_result(out)
        else:
            # Local fallback: do nothing destructive; nudge user with a clean starter line
            if not text.strip():
                apply_result("—")
            else:
                apply_result(text)
        return

    # --- REWRITE (tighten last paragraph; preserve meaning) ---
    if action == "Rewrite":
        paras = _split_paragraphs(text)
        if not paras:
            return
        if use_ai:
            target = paras[-1]
            task = (
                f"Rewrite ONLY the final paragraph for {stage.lower()} quality. "
                "Preserve intent, facts, and voice. Improve clarity, rhythm, and specificity. "
                "Return ONLY the rewritten paragraph."
            )
            out = _call_openai(brief, task, target)
            paras[-1] = out if out else target
            apply_result(_join_paragraphs(paras))
        else:
            # Local fallback: mechanical cleanup on last paragraph
            paras[-1] = _local_cleanup(paras[-1])
            apply_result(_join_paragraphs(paras))
        return

    # --- EXPAND (deepen last paragraph with detail) ---
    if action == "Expand":
        paras = _split_paragraphs(text)
        if not paras:
            return
        if use_ai:
            target = paras[-1]
            task = (
                "Expand the final paragraph with concrete sensory detail, subtext, and precision. "
                "Do NOT bloat. Add 2–6 sentences. Preserve voice. Return ONLY the expanded paragraph."
            )
            out = _call_openai(brief, task, target)
            paras[-1] = out if out else target
            apply_result(_join_paragraphs(paras))
        else:
            apply_result(text)  # safe no-op if no AI
        return

    # --- REPHRASE (rewrite last sentence; keep meaning) ---
    if action == "Rephrase":
        if not text.strip():
            return
        if use_ai:
            sent = _last_sentence(text)
            task = (
                "Rephrase the final sentence 3 different ways, all faithful to meaning and voice. "
                "Pick the strongest ONE and return ONLY that final chosen sentence."
            )
            out = _call_openai(brief, task, sent)
            if out:
                # Replace only the final sentence (approx)
                new_text = re.sub(re.escape(sent) + r"\s*$", out.strip(), text.strip(), flags=re.DOTALL)
                apply_result(new_text)
        else:
            sent = _last_sentence(text)
            repl = _local_rephrase_sentence(sent)
            if repl and repl != sent:
                new_text = re.sub(re.escape(sent) + r"\s*$", repl, text.strip(), flags=re.DOTALL)
                apply_result(new_text)
        return

    # --- DESCRIBE (add descriptive pass to last paragraph) ---
    if action == "Describe":
        paras = _split_paragraphs(text)
        if not paras:
            return
        if use_ai:
            target = paras[-1]
            task = (
                "Add vivid, specific description to the final paragraph without changing events. "
                "Sharpen nouns and verbs. Avoid purple prose unless Voice Bible demands it. "
                "Return ONLY the revised paragraph."
            )
            out = _call_openai(brief, task, target)
            paras[-1] = out if out else target
            apply_result(_join_paragraphs(paras))
        else:
            apply_result(text)
        return

    # --- SPELL / GRAMMAR (professional cleanup passes) ---
    if action in ("Spell", "Grammar"):
        # Local cleanup always runs; AI optionally improves beyond mechanics
        cleaned = _local_cleanup(text)
        if use_ai:
            task = (
                "Perform a professional copyedit pass: fix spelling/grammar/punctuation, "
                "remove clutter, preserve voice. Do not change meaning. Return the full revised text."
            )
            out = _call_openai(brief, task, cleaned)
            apply_result(out if out else cleaned)
        else:
            apply_result(cleaned)
        return

    # --- FIND / SYNONYM / SENTENCE (placeholders that do not alter text) ---
    # These are kept inert intentionally until you decide their exact behavior.
    apply_result(text)

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])

    # "New" clears writing only (non-destructive snapshot first)
    if cols[0].button("🆕 New", key="new_project"):
        push_revision("New")
        st.session_state.main_text = ""
        autosave()
        set_last_action("New")

    # Stage controls (wired to your existing buttons)
    if cols[1].button("✏️ Rough", key="rough"):
        st.session_state.stage = "Rough"
        set_last_action("Stage: Rough")
    if cols[2].button("🛠 Edit", key="edit"):
        st.session_state.stage = "Edit"
        set_last_action("Stage: Edit")
    if cols[3].button("✅ Final", key="final"):
        st.session_state.stage = "Final"
        set_last_action("Stage: Final")

    cols[4].markdown(
        f"""
        <div style='text-align:right;font-size:12px;'>
            Stage: <b>{st.session_state.stage}</b>
            &nbsp;•&nbsp; Last: {st.session_state.last_action}
            &nbsp;•&nbsp; Autosave: {st.session_state.autosave_time or '—'}
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ============================================================
# LOCKED LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    with st.expander("🗃 Junk Drawer"):
        st.text_area("", key="junk", height=80)

    with st.expander("📝 Synopsis"):
        st.text_area("", key="synopsis", height=100)

    with st.expander("🎭 Genre / Style Notes"):
        st.text_area("", key="genre_style_notes", height=80)

    with st.expander("🌍 World Elements"):
        st.text_area("", key="world", height=100)

    with st.expander("👤 Characters"):
        st.text_area("", key="characters", height=120)

    with st.expander("🧱 Outline"):
        st.text_area("", key="outline", height=160)

# ============================================================
# CENTER — WRITING DESK (ALWAYS ON)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    st.text_area(
        "",
        key="main_text",
        height=650,
        on_change=autosave
    )

    # Bottom bar — writing (wired)
    b1 = st.columns(5)
    if b1[0].button("Write", key="btn_write"):
        partner_action("Write")
    if b1[1].button("Rewrite", key="btn_rewrite"):
        partner_action("Rewrite")
    if b1[2].button("Expand", key="btn_expand"):
        partner_action("Expand")
    if b1[3].button("Rephrase", key="btn_rephrase"):
        partner_action("Rephrase")
    if b1[4].button("Describe", key="btn_describe"):
        partner_action("Describe")

    # Bottom bar — editing (wired)
    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell"):
        partner_action("Spell")
    if b2[1].button("Grammar", key="btn_grammar"):
        partner_action("Grammar")
    b2[2].button("Find", key="btn_find")        # intentionally inert for now
    b2[3].button("Synonym", key="btn_synonym")  # intentionally inert for now
    b2[4].button("Sentence", key="btn_sentence")# intentionally inert for now

# ============================================================
# RIGHT — VOICE BIBLE (TOP → BOTTOM, EXACT)
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    # 1. Writing Style
    st.checkbox("Enable Writing Style", key="vb_style_on")
    st.selectbox(
        "Writing Style",
        ["Neutral", "Minimal", "Expressive", "Hardboiled", "Poetic"],
        key="writing_style",
        disabled=not st.session_state.vb_style_on
    )
    st.slider(
        "Style Intensity",
        0.0, 1.0,
        key="style_intensity",
        disabled=not st.session_state.vb_style_on
    )

    st.divider()

    # 2. Genre
    st.checkbox("Enable Genre Influence", key="vb_genre_on")
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on
    )
    st.slider(
        "Genre Intensity",
        0.0, 1.0,
        key="genre_intensity",
        disabled=not st.session_state.vb_genre_on
    )

    st.divider()

    # 3. Trained Voices
    st.checkbox("Enable Trained Voice", key="vb_trained_on")
    st.selectbox(
        "Trained Voice",
        ["— None —", "Voice A", "Voice B"],
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on
    )
    st.slider(
        "Trained Voice Intensity",
        0.0, 1.0,
        key="trained_intensity",
        disabled=not st.session_state.vb_trained_on
    )

    st.divider()

    # 4. Match My Style
    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on
    )
    st.slider(
        "Match Intensity",
        0.0, 1.0,
        key="match_intensity",
        disabled=not st.session_state.vb_match_on
    )

    st.divider()

    # 5. Voice Lock
    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on")
    st.text_area(
        "Voice Lock Prompt",
        key="voice_lock_prompt",
        height=80,
        disabled=not st.session_state.vb_lock_on
    )
    st.slider(
        "Lock Strength",
        0.0, 1.0,
        key="lock_intensity",
        disabled=not st.session_state.vb_lock_on
    )

    st.divider()

    # POV / Tense
    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov")
    st.selectbox("Tense", ["Past", "Present"], key="tense")

    # Focus Mode stays visible, but it does nothing (free writing always)
    st.button("🔒 Focus Mode", disabled=True)

# ============================================================
# FOCUS MODE — HARD LOCK (PERMANENTLY DISABLED)
# ============================================================
if st.session_state.focus_mode:
    st.markdown(
        """
        <style>
        header, footer, aside, .stSidebar {display:none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.info("Focus Mode enabled. Refresh page to exit.")
