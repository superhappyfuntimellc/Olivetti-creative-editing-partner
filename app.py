import os
import re
import math
import hashlib
import streamlit as st
from datetime import datetime
from typing import List

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

# Streamlit Cloud Secrets preferred; env var fallback
DEFAULT_MODEL = "gpt-4.1-mini"
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # type: ignore[attr-defined]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)  # type: ignore[attr-defined]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

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
    /* Writing desk: pro ergonomics */
    div[data-testid="stTextArea"] textarea {
      font-size: 18px !important;
      line-height: 1.65 !important;
      padding: 18px !important;
      resize: vertical !important;   /* central writing window expandable */
      min-height: 520px !important;
    }

    /* Buttons: bigger targets */
    button[kind="secondary"], button[kind="primary"] {
      font-size: 16px !important;
      padding: 0.6rem 0.9rem !important;
    }

    /* Labels: readable */
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

        # Production mode (wired to existing top buttons)
        "stage": "Rough",     # Rough | Edit | Final
        "last_action": "—",

        # Safety: non-destructive history
        "revisions": [],      # list[{ts, action, text}]
        "redo_stack": [],     # list[{ts, action, text}]

        # Temporary session “My Voice”
        "voiceA_snips": [],   # list[str]
        "voiceB_snips": [],   # list[str]
        "voice_status": "—",

        # Throttles
        "last_captured_hash": "",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Free writing always: permanently disable hard focus behavior (button stays visible)
st.session_state.focus_mode = False

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    capture_voice_snippet_from_draft()

# ============================================================
# REVISION VAULT (non-destructive)
# ============================================================
def push_revision(action_name: str):
    snap = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_name,
        "text": st.session_state.main_text,
    }
    st.session_state.revisions.append(snap)
    if len(st.session_state.revisions) > 80:
        st.session_state.revisions = st.session_state.revisions[-80:]
    st.session_state.redo_stack = []

def undo_last():
    if not st.session_state.revisions:
        st.session_state.voice_status = "Undo: nothing to undo."
        return
    current = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": "redo_point",
        "text": st.session_state.main_text,
    }
    st.session_state.redo_stack.append(current)
    snap = st.session_state.revisions.pop()
    st.session_state.main_text = snap["text"]
    st.session_state.last_action = "Undo"
    autosave()
    st.session_state.voice_status = f"Undo: restored {snap['action']} @ {snap['ts']}"

def redo_last():
    if not st.session_state.redo_stack:
        st.session_state.voice_status = "Redo: nothing to redo."
        return
    push_revision("redo_point")
    snap = st.session_state.redo_stack.pop()
    st.session_state.main_text = snap["text"]
    st.session_state.last_action = "Redo"
    autosave()
    st.session_state.voice_status = "Redo: restored."

# ============================================================
# COMMANDS (no new UI) — typed into Story Bible Junk Drawer
# ============================================================
CMD_UNDO = re.compile(r"^\s*/undo\s*$", re.IGNORECASE)
CMD_REDO = re.compile(r"^\s*/redo\s*$", re.IGNORECASE)
CMD_STATUS = re.compile(r"^\s*/status\s*$", re.IGNORECASE)
CMD_CLEAR = re.compile(r"^\s*/clear\s*$", re.IGNORECASE)

def handle_junk_commands():
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return
    if CMD_UNDO.match(raw):
        undo_last()
        st.session_state.junk = ""
        return
    if CMD_REDO.match(raw):
        redo_last()
        st.session_state.junk = ""
        return
    if CMD_STATUS.match(raw):
        a = len(st.session_state.voiceA_snips)
        b = len(st.session_state.voiceB_snips)
        st.session_state.voice_status = f"Status: A={a} samples, B={b} samples. Revisions={len(st.session_state.revisions)}."
        st.session_state.junk = ""
        return
    if CMD_CLEAR.match(raw):
        st.session_state.junk = ""
        st.session_state.voice_status = "Cleared."
        return

# Run command handler each rerun (keeps it “OS-like” without UI changes)
handle_junk_commands()

# ============================================================
# TEMP “MY VOICE” — Session-only training + retrieval
# ============================================================
WORD_RE = re.compile(r"[A-Za-z']+")

def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or "")]

def _hash_vec(text: str, dims: int = 512) -> List[float]:
    vec = [0.0] * dims
    toks = _tokenize(text)
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        vec[h % dims] += 1.0
    for i, v in enumerate(vec):
        if v > 0:
            vec[i] = 1.0 + math.log(v)
    return vec

def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def _split_paragraphs(text: str) -> List[str]:
    t = (text or "").strip()
    if not t:
        return []
    return re.split(r"\n\s*\n", t, flags=re.MULTILINE)

def capture_voice_snippet_from_draft():
    """
    Learns passively DURING the session (temporary memory).
    Captures the latest paragraph occasionally while Trained Voice is ON.
    """
    if not st.session_state.vb_trained_on:
        return
    tv = st.session_state.trained_voice
    if tv not in ("Voice A", "Voice B"):
        return

    paras = _split_paragraphs(st.session_state.main_text or "")
    if not paras:
        return
    last = paras[-1].strip()
    if len(last) < 240:
        return

    h = hashlib.md5(last.encode("utf-8")).hexdigest()
    if h == st.session_state.last_captured_hash:
        return
    st.session_state.last_captured_hash = h

    if tv == "Voice A":
        st.session_state.voiceA_snips.append(last)
        if len(st.session_state.voiceA_snips) > 120:
            st.session_state.voiceA_snips = st.session_state.voiceA_snips[-120:]
    else:
        st.session_state.voiceB_snips.append(last)
        if len(st.session_state.voiceB_snips) > 120:
            st.session_state.voiceB_snips = st.session_state.voiceB_snips[-120:]

    st.session_state.voice_status = f"Trained {tv}: +1 paragraph"

def retrieve_voice_exemplars(query_text: str, voice: str, k: int = 3) -> List[str]:
    pool = st.session_state.voiceA_snips if voice == "Voice A" else st.session_state.voiceB_snips
    if not pool:
        return []
    qv = _hash_vec(query_text)
    scored = []
    for s in pool[-80:]:
        scored.append((_cosine(qv, _hash_vec(s)), s))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for score, s in scored[:k] if score > 0.0]
    return top[:k]

# ============================================================
# STORY BIBLE AS CANON + IDEA BANK (MANDATORY INJECTION)
# ============================================================
def _story_bible_text() -> str:
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
    return "\n\n".join(sb).strip() if sb else "— None provided —"

def build_partner_brief(action_name: str) -> str:
    story_bible = _story_bible_text()

    idea_directive = """
STORY BIBLE USAGE (MANDATORY):
- Treat Story Bible as CANON and as an IDEA BANK.
- When generating NEW material, you MUST pull at least 2 concrete specifics from the Story Bible
  (character detail, world element, outline beat, relationship, rule, setting detail).
- Do not contradict canon. Prefer Story Bible specificity over generic invention.
""".strip()

    dominance = """
DOMINANCE RULES (do not violate):
- If Voice Lock is ON: it is a hard constraint.
- If Trained Voice is ON: mimic the author’s cadence and sentence habits from exemplars; do not drift.
- Match My Style affects micro-style texture; do not change story facts.
- Genre influence shapes structure/tropes but must not override the author’s voice.
""".strip()

    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_match_on and st.session_state.voice_sample.strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and st.session_state.voice_lock_prompt.strip():
        vb.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    exemplars = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv in ("Voice A", "Voice B"):
        ctx = (st.session_state.main_text or "")[-2500:]
        exemplars = retrieve_voice_exemplars(ctx if ctx.strip() else st.session_state.synopsis, tv, k=3)
    ex_block = "— None —"
    if exemplars:
        ex_block = "\n\n---\n\n".join(exemplars)

    stage = st.session_state.stage
    pov = st.session_state.pov
    tense = st.session_state.tense

    return f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
This is professional production. Be assertive and decisive when executing a tool.

ABSOLUTE RULES:
- Do not mention UI. Do not explain process. Output only usable writing or usable edits.
- Preserve meaning and intent. Avoid filler. Avoid generic phrasing.
- Do not overwrite facts from Story Bible.

WORKING MODE: {stage}
POV: {pov}
TENSE: {tense}

{idea_directive}

{dominance}

VOICE CONTROLS:
{voice_controls}

TRAINED VOICE EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE (canon/constraints + idea bank):
{story_bible}

ACTION: {action_name}
""".strip()

# ============================================================
# OPTIONAL OPENAI CALL (safe; won’t crash if missing)
# ============================================================
def call_openai(system_brief: str, user_task: str, text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. Add to requirements.txt: openai") from e

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_brief},
            {"role": "user", "content": f"{user_task}\n\nDRAFT:\n{text.strip()}"},
        ],
        temperature=0.75 if st.session_state.stage == "Rough" else 0.3,
    )
    return (resp.choices[0].message.content or "").strip()

# ============================================================
# LOCAL COPYEDIT (fallback still pro)
# ============================================================
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

# ============================================================
# PARTNER ACTIONS (wired to existing buttons)
# ============================================================
def partner_action(action: str):
    text = st.session_state.main_text or ""
    push_revision(action)

    brief = build_partner_brief(action)
    use_ai = bool(OPENAI_API_KEY)

    def apply_replace(result: str):
        if result and result.strip():
            st.session_state.main_text = result.strip()
            autosave()
            st.session_state.last_action = action

    def apply_append(result: str):
        if result and result.strip():
            if (st.session_state.main_text or "").strip():
                st.session_state.main_text = (st.session_state.main_text.rstrip() + "\n\n" + result.strip()).strip()
            else:
                st.session_state.main_text = result.strip()
            autosave()
            st.session_state.last_action = action

    # Assertive tool behavior (Sudowrite ×100, but obedient)
    try:
        if action == "Write":
            if use_ai:
                task = (
                    "Continue decisively. Add 1–3 paragraphs that advance the scene. "
                    "MANDATORY: incorporate at least 2 Story Bible specifics. "
                    "No recap. No planning. No explanation. Just prose."
                )
                out = call_openai(brief, task, text if text.strip() else "Start the opening.")
                apply_append(out)
            else:
                apply_replace(text)
            return

        if action == "Rewrite":
            if use_ai:
                task = (
                    "Rewrite for professional quality. Tighten, sharpen, commit. "
                    "Preserve meaning and voice. Preserve Story Bible canon. Return full revised text."
                )
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(local_cleanup(text))
            return

        if action == "Expand":
            if use_ai:
                task = (
                    "Expand with meaningful depth: concrete detail, specificity, subtext. "
                    "No padding. Preserve canon. Return full revised text."
                )
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Rephrase":
            if use_ai:
                task = (
                    "Replace the final sentence with a stronger one (same meaning). "
                    "Preserve voice and canon. Return full text with that change applied."
                )
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Describe":
            if use_ai:
                task = (
                    "Add vivid description with control: sharpen nouns/verbs, add sensory detail, keep pace. "
                    "Preserve canon. Return full revised text."
                )
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = (
                    "Production copyedit: spelling/grammar/punctuation. Preserve voice and meaning. "
                    "Do not flatten style. Preserve canon. Return full revised text."
                )
                out = call_openai(brief, task, cleaned)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
            return

        # Find / Synonym / Sentence stay present (no removal) — intentionally inert for now
        apply_replace(text)

    except Exception as e:
        # No UI changes: report via existing status line
        st.session_state.voice_status = f"Engine: {str(e)}"
        apply_replace(text)

# ============================================================
# TOP BAR (EXACT BUTTONS KEPT)
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])

    if cols[0].button("🆕 New", key="new_project"):
        push_revision("New")
        st.session_state.main_text = ""
        autosave()
        st.session_state.last_action = "New"

    if cols[1].button("✏️ Rough", key="rough"):
        st.session_state.stage = "Rough"
        st.session_state.last_action = "Stage: Rough"
    if cols[2].button("🛠 Edit", key="edit"):
        st.session_state.stage = "Edit"
        st.session_state.last_action = "Stage: Edit"
    if cols[3].button("✅ Final", key="final"):
        st.session_state.stage = "Final"
        st.session_state.last_action = "Stage: Final"

    cols[4].markdown(
        f"""
        <div style='text-align:right;font-size:12px;'>
            Stage: <b>{st.session_state.stage}</b>
            &nbsp;•&nbsp; Last: {st.session_state.last_action}
            &nbsp;•&nbsp; Autosave: {st.session_state.autosave_time or '—'}
            <br/>Voice: {st.session_state.voice_status}
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ============================================================
# LOCKED LAYOUT (EXACT RATIOS KEPT)
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE (EXACT FEATURES KEPT)
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    with st.expander("🗃 Junk Drawer"):
        st.text_area("", key="junk", height=80)
        # Commands (type exactly):
        # /undo  /redo  /status  /clear

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

    st.text_area("", key="main_text", height=650, on_change=autosave)

    # Bottom bar — writing (EXACT BUTTONS KEPT; powered)
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

    # Bottom bar — editing (EXACT BUTTONS KEPT; Spell/Grammar powered)
    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell"):
        partner_action("Spell")
    if b2[1].button("Grammar", key="btn_grammar"):
        partner_action("Grammar")
    b2[2].button("Find", key="btn_find")
    b2[3].button("Synonym", key="btn_synonym")
    b2[4].button("Sentence", key="btn_sentence")

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
    st.slider("Style Intensity", 0.0, 1.0, key="style_intensity", disabled=not st.session_state.vb_style_on)

    st.divider()

    # 2. Genre
    st.checkbox("Enable Genre Influence", key="vb_genre_on")
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on
    )
    st.slider("Genre Intensity", 0.0, 1.0, key="genre_intensity", disabled=not st.session_state.vb_genre_on)

    st.divider()

    # 3. Trained Voices (EXACT OPTIONS KEPT)
    st.checkbox("Enable Trained Voice", key="vb_trained_on")
    st.selectbox(
        "Trained Voice",
        ["— None —", "Voice A", "Voice B"],
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on
    )
    st.slider("Trained Voice Intensity", 0.0, 1.0, key="trained_intensity", disabled=not st.session_state.vb_trained_on)

    st.divider()

    # 4. Match My Style
    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area("Style Example", key="voice_sample", height=100, disabled=not st.session_state.vb_match_on)
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity", disabled=not st.session_state.vb_match_on)

    st.divider()

    # 5. Voice Lock
    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on")
    st.text_area("Voice Lock Prompt", key="voice_lock_prompt", height=80, disabled=not st.session_state.vb_lock_on)
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity", disabled=not st.session_state.vb_lock_on)

    st.divider()

    # POV / Tense
    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov")
    st.selectbox("Tense", ["Past", "Present"], key="tense")

    # Focus Mode stays visible, but does nothing (free writing always)
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
