import os
import re
import json
import math
import hashlib
import streamlit as st
from datetime import datetime
from typing import Dict, List, Tuple

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

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
    div[data-testid="stTextArea"] textarea {
      font-size: 18px !important;
      line-height: 1.65 !important;
      padding: 18px !important;
      resize: vertical !important;
      min-height: 520px !important;
    }
    button[kind="secondary"], button[kind="primary"] {
      font-size: 16px !important;
      padding: 0.6rem 0.9rem !important;
    }
    label, .stSelectbox label, .stSlider label {
      font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# STORAGE (My Voice Vault)
# ============================================================
APP_DIR = os.path.join(os.getcwd(), ".olivetti")
VOICES_PATH = os.path.join(APP_DIR, "voices.json")

def _ensure_storage():
    os.makedirs(APP_DIR, exist_ok=True)
    if not os.path.exists(VOICES_PATH):
        with open(VOICES_PATH, "w", encoding="utf-8") as f:
            json.dump({"voices": {}}, f)

def load_voices() -> Dict[str, dict]:
    _ensure_storage()
    with open(VOICES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("voices", {})

def save_voices(voices: Dict[str, dict]):
    _ensure_storage()
    with open(VOICES_PATH, "w", encoding="utf-8") as f:
        json.dump({"voices": voices}, f, ensure_ascii=False, indent=2)

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

        # Partner engine
        "stage": "Rough",
        "last_action": "—",
        "revisions": [],

        # My Voice runtime cache
        "voice_status": "—",
        "voices_cache": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
st.session_state.focus_mode = False  # free writing always

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")

# ============================================================
# REVISION VAULT
# ============================================================
def push_revision(action_name: str):
    snap = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_name,
        "text": st.session_state.main_text,
    }
    st.session_state.revisions.append(snap)
    if len(st.session_state.revisions) > 50:
        st.session_state.revisions = st.session_state.revisions[-50:]

def set_last_action(action_name: str):
    st.session_state.last_action = action_name

# ============================================================
# MY VOICE — Lightweight fingerprint + retrieval (works without OpenAI)
# ============================================================
WORD_RE = re.compile(r"[A-Za-z']+")
def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or "")]

def _hash_vec(text: str, dims: int = 512) -> List[float]:
    """
    Cheap embedding: hashed bag-of-words + log-scaling.
    Deterministic, no external deps. Good enough for local retrieval.
    """
    vec = [0.0] * dims
    toks = _tokenize(text)
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        idx = h % dims
        vec[idx] += 1.0
    # log scale
    for i, v in enumerate(vec):
        if v > 0:
            vec[i] = 1.0 + math.log(v)
    return vec

def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def _fingerprint(text: str) -> Dict[str, float]:
    """
    Simple stylistic fingerprint for prompt anchoring.
    """
    t = (text or "").strip()
    if not t:
        return {"avg_sentence_len": 0, "comma_rate": 0, "dash_rate": 0, "dialogue_rate": 0}

    sentences = re.split(r"(?<=[.!?])\s+", t)
    words = _tokenize(t)
    avg_sentence_len = (len(words) / max(1, len(sentences)))

    comma_rate = t.count(",") / max(1, len(words))
    dash_rate = (t.count("—") + t.count("--")) / max(1, len(words))
    dialogue_rate = t.count('"') / max(1, len(t))  # crude signal

    return {
        "avg_sentence_len": round(avg_sentence_len, 2),
        "comma_rate": round(comma_rate, 4),
        "dash_rate": round(dash_rate, 4),
        "dialogue_rate": round(dialogue_rate, 6),
    }

def _normalize_sample(sample: str) -> str:
    s = (sample or "").strip()
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def voice_save(name: str, sample: str) -> str:
    name = (name or "").strip()
    sample = _normalize_sample(sample)
    if not name:
        return "Voice name missing."
    if len(sample) < 200:
        return "Paste at least ~200 characters of your writing before saving."
    voices = load_voices()
    v = voices.get(name, {"samples": []})
    v["samples"].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": sample,
        "fp": _fingerprint(sample),
        "vec": _hash_vec(sample),
    })
    # keep last 200 samples per voice
    if len(v["samples"]) > 200:
        v["samples"] = v["samples"][-200:]
    voices[name] = v
    save_voices(voices)
    return f"Saved sample to voice: {name}"

def voice_delete(name: str) -> str:
    voices = load_voices()
    if name in voices:
        del voices[name]
        save_voices(voices)
        return f"Deleted voice: {name}"
    return "Voice not found."

def voice_list() -> List[str]:
    voices = load_voices()
    return sorted(list(voices.keys()))

def voice_retrieve(name: str, query_text: str, k: int = 3) -> Tuple[List[str], Dict[str, float]]:
    voices = load_voices()
    v = voices.get(name)
    if not v or not v.get("samples"):
        return [], {}
    qv = _hash_vec(query_text)
    scored = []
    for s in v["samples"]:
        sv = s.get("vec") or []
        scored.append((_cosine(qv, sv), s))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [item[1]["text"] for item in scored[:k] if item[0] > 0.0]
    # aggregate fingerprint (rough average)
    fps = [item[1].get("fp", {}) for item in scored[: min(10, len(scored))]]
    if not fps:
        return top, {}
    agg = {}
    keys = fps[0].keys()
    for key in keys:
        vals = [fp.get(key, 0) for fp in fps]
        agg[key] = round(sum(vals) / max(1, len(vals)), 4)
    return top, agg

# ============================================================
# COMMANDS in Style Example (no UI changes)
# ============================================================
CMD_SAVE = re.compile(r"^\s*/savevoice\s+(.+)$", re.IGNORECASE)
CMD_DELETE = re.compile(r"^\s*/deletevoice\s+(.+)$", re.IGNORECASE)
CMD_LIST = re.compile(r"^\s*/listvoices\s*$", re.IGNORECASE)

def handle_voice_commands():
    """
    If the Style Example begins with a command, execute it and clear the box.
    This keeps UI locked: no new buttons, no new panels.
    """
    raw = st.session_state.voice_sample or ""
    first_line = raw.strip().splitlines()[0] if raw.strip() else ""
    if not first_line:
        return

    m = CMD_SAVE.match(first_line)
    if m:
        name = m.group(1).strip()
        # everything after first line is the sample
        sample = "\n".join(raw.splitlines()[1:]).strip()
        st.session_state.voice_status = voice_save(name, sample)
        st.session_state.voice_sample = ""
        st.session_state.voices_cache = None
        return

    m = CMD_DELETE.match(first_line)
    if m:
        name = m.group(1).strip()
        st.session_state.voice_status = voice_delete(name)
        st.session_state.voice_sample = ""
        st.session_state.voices_cache = None
        return

    if CMD_LIST.match(first_line):
        names = voice_list()
        st.session_state.voice_status = "Voices: " + (", ".join(names) if names else "— none —")
        st.session_state.voice_sample = ""
        return

# ============================================================
# PARTNER BRIEF (Story Bible + Voice Bible + My Voice Retrieval)
# ============================================================
def build_partner_brief(action_name: str) -> str:
    # Story Bible
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

    # Voice Bible controls
    vb_lines = []
    if st.session_state.vb_style_on:
        vb_lines.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb_lines.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_match_on and st.session_state.voice_sample.strip():
        vb_lines.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and st.session_state.voice_lock_prompt.strip():
        vb_lines.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb_lines).strip() if vb_lines else "— None enabled —"

    # Trained Voice retrieval (your “My Voice”)
    exemplars = []
    fp = {}
    trained_name = st.session_state.trained_voice
    if st.session_state.vb_trained_on and trained_name and trained_name != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]  # last chunk of current draft
        exemplars, fp = voice_retrieve(trained_name, ctx if ctx.strip() else st.session_state.synopsis, k=3)

    # Dominance rules (explicit, enforced)
    dominance = f"""
DOMINANCE RULES:
- If Voice Lock is ON: obey it as a hard constraint.
- If Trained Voice is ON: mimic the author's fingerprint and exemplar patterns; do not drift.
- Match Sample affects micro-style and texture; do not change plot facts.
- Genre/Style influence structure/tropes, but do not overwrite the author's voice.
""".strip()

    stage = st.session_state.stage
    pov = st.session_state.pov
    tense = st.session_state.tense

    exemplar_block = "— None —"
    if exemplars:
        exemplar_block = "\n\n---\n\n".join(exemplars[:3])

    fp_block = "— None —"
    if fp:
        fp_block = json.dumps(fp, ensure_ascii=False)

    brief = f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
This is professional production. Produce usable prose and usable edits.

ABSOLUTE RULES:
- Never mention UI. Never explain your process.
- Preserve meaning and intent. No generic filler.
- Avoid clichés unless the author’s voice clearly uses them.
- Be specific, sensory, and controlled.

WORKING MODE: {stage}
POV: {pov}
TENSE: {tense}

{dominance}

VOICE CONTROLS:
{voice_controls}

TRAINED VOICE:
Name: {trained_name}
Fingerprint (guide): {fp_block}
Exemplars (mimic patterns, not content):
{exemplar_block}

STORY BIBLE (canon/constraints):
{story_bible if story_bible else "— None provided —"}

ACTION: {action_name}
""".strip()
    return brief

# ============================================================
# OPTIONAL AI CALL
# ============================================================
def _call_openai(system_brief: str, user_task: str, text: str) -> str:
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
# LOCAL COPYEDIT (fallback still pro)
# ============================================================
def _local_cleanup(text: str) -> str:
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

def _last_sentence(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", t)
    return parts[-1].strip() if parts else t

# ============================================================
# PARTNER ACTIONS (wired to existing buttons)
# ============================================================
def partner_action(action: str):
    text = st.session_state.main_text or ""
    push_revision(action)

    # Handle voice commands if user is using Style Example as command line
    handle_voice_commands()

    # If no AI configured, still deliver something useful
    use_ai = bool(OPENAI_API_KEY)

    brief = build_partner_brief(action)

    def apply_result(result: str, mode: str = "replace"):
        if not result or not result.strip():
            return
        if mode == "append" and (st.session_state.main_text or "").strip():
            st.session_state.main_text = (st.session_state.main_text.rstrip() + "\n\n" + result.strip()).strip()
        else:
            st.session_state.main_text = result.strip()
        autosave()
        set_last_action(action)

    if action == "Write":
        if use_ai:
            task = "Continue the draft. Add 1–3 paragraphs. No recap. No explanation. Just prose."
            out = _call_openai(brief, task, text if text.strip() else "Start the opening.")
            apply_result(out, mode="append" if text.strip() else "replace")
        else:
            # safe, non-toy fallback: do nothing destructive
            apply_result(text)
        return

    if action == "Rewrite":
        if use_ai:
            task = "Rewrite the final paragraph for professional quality. Preserve meaning and voice. Return full text."
            out = _call_openai(brief, task, text)
            apply_result(out)
        else:
            apply_result(_local_cleanup(text))
        return

    if action == "Expand":
        if use_ai:
            task = "Expand the final paragraph with concrete detail, subtext, and precision. Return full text."
            out = _call_openai(brief, task, text)
            apply_result(out)
        else:
            apply_result(text)
        return

    if action == "Rephrase":
        sent = _last_sentence(text)
        if use_ai:
            task = "Rephrase the final sentence 3 ways, pick strongest ONE. Return full text with that final sentence replaced."
            out = _call_openai(brief, task, text)
            apply_result(out)
        else:
            apply_result(text)
        return

    if action == "Describe":
        if use_ai:
            task = "Add vivid, specific description without changing events. Return full text."
            out = _call_openai(brief, task, text)
            apply_result(out)
        else:
            apply_result(text)
        return

    if action in ("Spell", "Grammar"):
        cleaned = _local_cleanup(text)
        if use_ai:
            task = "Copyedit: spelling/grammar/punctuation; preserve voice; do not change meaning. Return full text."
            out = _call_openai(brief, task, cleaned)
            apply_result(out if out else cleaned)
        else:
            apply_result(cleaned)
        return

    # Find / Synonym / Sentence: intentionally inert until you define behavior
    apply_result(text)

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])

    if cols[0].button("🆕 New", key="new_project"):
        push_revision("New")
        st.session_state.main_text = ""
        autosave()
        set_last_action("New")

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
            <br/>Voice: {st.session_state.voice_status}
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
# CENTER — WRITING DESK
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    st.text_area("", key="main_text", height=650, on_change=autosave)

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

    # 3. Trained Voices (auto-loaded from vault)
    st.checkbox("Enable Trained Voice", key="vb_trained_on")

    if st.session_state.voices_cache is None:
        st.session_state.voices_cache = voice_list()

    trained_options = ["— None —"] + (st.session_state.voices_cache or [])
    st.selectbox(
        "Trained Voice",
        trained_options,
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on
    )
    st.slider("Trained Voice Intensity", 0.0, 1.0, key="trained_intensity", disabled=not st.session_state.vb_trained_on)

    st.divider()

    # 4. Match My Style (also serves as command console for saving voices)
    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on,
        help="Commands: /savevoice Name (first line), /listvoices, /deletevoice Name"
    )
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity", disabled=not st.session_state.vb_match_on)

    st.divider()

    # 5. Voice Lock
    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on")
    st.text_area("Voice Lock Prompt", key="voice_lock_prompt", height=80, disabled=not st.session_state.vb_lock_on)
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity", disabled=not st.session_state.vb_lock_on)

    st.divider()

    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov")
    st.selectbox("Tense", ["Past", "Present"], key="tense")

    st.button("🔒 Focus Mode", disabled=True)

# ============================================================
# FOCUS MODE — PERMANENTLY DISABLED
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
