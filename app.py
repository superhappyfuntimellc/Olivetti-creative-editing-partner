import os
import re
import math
import hashlib
import streamlit as st
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

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
      resize: vertical !important;
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
LANES = ["Dialogue", "Narration", "Interiority", "Action"]

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

        # Status
        "voice_status": "—",

        # Tool output (shown inside existing Junk Drawer expander)
        "tool_output": "",

        # Throttles
        "last_captured_hash": "",

        # Session-only Voice Vault (distinct voices, selectable at will)
        # voices[name] = {"created_ts":..., "lanes": {"Dialogue":[sample...], ...}}
        "voices": {},
        "voices_seeded": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Free writing always: permanently disable hard focus behavior (button stays visible)
st.session_state.focus_mode = False

# ============================================================
# CORE UTILS
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

def _join_paragraphs(paras: List[str]) -> str:
    return ("\n\n".join([p.strip() for p in paras if p is not None])).strip()

# ============================================================
# LANE DETECTION (Dialogue / Narration / Interiority / Action)
# ============================================================
THOUGHT_WORDS = set([
    "think", "thought", "felt", "wondered", "realized", "remembered",
    "knew", "noticed", "decided", "hoped", "feared", "wanted", "imagined",
    "could", "should", "would"
])

ACTION_VERBS = set([
    "run","ran","walk","walked","grab","grabbed","push","pushed","pull","pulled",
    "slam","slammed","hit","struck","kick","kicked","turn","turned","spin","spun",
    "snap","snapped","dive","dived","duck","ducked","rush","rushed","lunge","lunged",
    "climb","climbed","drop","dropped","throw","threw","fire","fired","aim","aimed",
    "break","broke","shatter","shattered","step","stepped","move","moved","reach","reached"
])

def detect_lane(paragraph: str) -> str:
    p = (paragraph or "").strip()
    if not p:
        return "Narration"

    # Dialogue signals
    quote_count = p.count('"') + p.count("“") + p.count("”")
    has_dialogue_punct = ("—" in p[:2]) or (p.startswith("- ")) or (p.startswith("“")) or (p.startswith('"'))
    dialogue_score = 0.0
    if quote_count >= 2:
        dialogue_score += 2.5
    if has_dialogue_punct:
        dialogue_score += 1.5
    # Many short lines often indicate dialogue blocks
    if p.count("\n") >= 2:
        short_lines = sum(1 for ln in p.splitlines() if len(ln.strip()) <= 60)
        if short_lines >= 2:
            dialogue_score += 1.0

    # Interiority signals
    toks = _tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i","me","my","mine","myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1:
            interior_score += 2.2
        if "?" in p and thought_hits >= 1:
            interior_score += 0.6
        # italics markers (common in some drafts)
        if "*" in p or "_" in p:
            interior_score += 0.3

    # Action signals
    action_score = 0.0
    if toks:
        verb_hits = sum(1 for t in toks if t in ACTION_VERBS)
        # short, punchy sentences + verbs = action
        sent_count = max(1, len(re.split(r"[.!?]+", p)) - 1)
        avg_len = len(toks) / sent_count if sent_count else len(toks)
        if verb_hits >= 2:
            action_score += 1.6
        if avg_len <= 14 and verb_hits >= 1:
            action_score += 1.0
        if "!" in p:
            action_score += 0.3

    # Default narration if none dominates
    # Resolve by max score; require a little dominance
    scores = {
        "Dialogue": dialogue_score,
        "Interiority": interior_score,
        "Action": action_score,
        "Narration": 0.25,  # baseline
    }
    lane = max(scores.items(), key=lambda kv: kv[1])[0]
    # If all are weak, keep Narration
    if scores[lane] < 0.9:
        return "Narration"
    return lane

def current_lane_from_draft(text: str) -> str:
    paras = _split_paragraphs(text)
    if not paras:
        return "Narration"
    return detect_lane(paras[-1])

# ============================================================
# TEMP VOICE VAULT — seed default voices (keeps existing options)
# ============================================================
def seed_default_voices():
    if st.session_state.voices_seeded:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def make_voice():
        return {"created_ts": now, "lanes": {ln: [] for ln in LANES}}

    st.session_state.voices.setdefault("Voice A", make_voice())
    st.session_state.voices.setdefault("Voice B", make_voice())
    st.session_state.voices_seeded = True

seed_default_voices()

def ensure_voice(name: str):
    nm = (name or "").strip()
    if not nm:
        return
    if nm not in st.session_state.voices:
        st.session_state.voices[nm] = {"created_ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                       "lanes": {ln: [] for ln in LANES}}

def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in st.session_state.voices.keys() if k not in ("Voice A", "Voice B")])
    return base + customs

def _cap_lane_samples(voice_name: str, lane: str, cap: int = 160):
    v = st.session_state.voices.get(voice_name)
    if not v:
        return
    v["lanes"][lane] = v["lanes"][lane][-cap:]

def add_sample_to_voice_lane(voice_name: str, lane: str, sample_text: str) -> None:
    ensure_voice(voice_name)
    lane = lane if lane in LANES else "Narration"
    txt = _normalize_text(sample_text)
    if not txt:
        return
    st.session_state.voices[voice_name]["lanes"][lane].append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": txt,
        "vec": _hash_vec(txt),
    })
    _cap_lane_samples(voice_name, lane)

def import_samples_to_voice(voice_name: str, big_sample: str) -> Tuple[int, Dict[str, int]]:
    ensure_voice(voice_name)
    text = _normalize_text(big_sample)
    paras = _split_paragraphs(text)

    # Chunking: merge very short paras to make better exemplars
    merged: List[str] = []
    buf = ""
    for p in paras:
        if len(p) < 160:
            buf = (buf + "\n\n" + p).strip() if buf else p
            continue
        if buf:
            merged.append(buf.strip())
            buf = ""
        merged.append(p)
    if buf:
        merged.append(buf.strip())

    counts = {ln: 0 for ln in LANES}
    imported = 0
    for p in merged:
        if len(p) < 180:
            continue
        lane = detect_lane(p)
        add_sample_to_voice_lane(voice_name, lane, p)
        counts[lane] += 1
        imported += 1

    # keep voice light overall (across lanes)
    # (cap per lane already; this is just extra safety)
    for ln in LANES:
        _cap_lane_samples(voice_name, ln, cap=160)

    return imported, counts

def delete_voice(name: str) -> str:
    nm = (name or "").strip()
    if nm in ("Voice A", "Voice B"):
        # clear base voices instead of deleting
        for ln in LANES:
            st.session_state.voices[nm]["lanes"][ln] = []
        return f"Cleared samples for {nm}."
    if nm in st.session_state.voices:
        del st.session_state.voices[nm]
        return f"Deleted voice: {nm}"
    return "Voice not found."

def retrieve_exemplars(voice_name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    v = st.session_state.voices.get(voice_name)
    if not v:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = v["lanes"].get(lane, [])
    if not pool:
        return []
    qv = _hash_vec(query_text)
    scored = [(_cosine(qv, s.get("vec", [])), s.get("text", "")) for s in pool[-140:]]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [txt for score, txt in scored[:k] if score > 0.0 and txt]
    return top[:k]

def retrieve_mixed_exemplars(voice_name: str, lane: str, query_text: str) -> List[str]:
    # Lane-first exemplars + one narration fallback if needed
    lane_ex = retrieve_exemplars(voice_name, lane, query_text, k=2)
    if lane == "Narration":
        return lane_ex if lane_ex else retrieve_exemplars(voice_name, "Narration", query_text, k=3)

    nar_ex = retrieve_exemplars(voice_name, "Narration", query_text, k=1)
    out = lane_ex + [x for x in nar_ex if x not in lane_ex]
    return out[:3]

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

CMD_FIND = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_SYN = re.compile(r"^\s*/syn\s*:\s*(.+)$", re.IGNORECASE)
CMD_SENT = re.compile(r"^\s*/sentence\s*:\s*(.+)$", re.IGNORECASE)

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
        names = sorted(st.session_state.voices.keys())
        st.session_state.voice_status = f"Status: Voices={len(names)} • Revisions={len(st.session_state.revisions)}"
        st.session_state.tool_output = "VOICES:\n" + ("\n".join(names) if names else "— none —")
        st.session_state.junk = ""
        return
    if CMD_CLEAR.match(raw):
        st.session_state.junk = ""
        st.session_state.tool_output = ""
        st.session_state.voice_status = "Cleared."
        return

# Run handler every rerun (OS-like)
handle_junk_commands()

# ============================================================
# VOICE IMPORT COMMANDS (use existing Style Example box)
# ============================================================
CMD_SAVEVOICE = re.compile(r"^\s*/savevoice\s+(.+)$", re.IGNORECASE)
CMD_DELETEVOICE = re.compile(r"^\s*/deletevoice\s+(.+)$", re.IGNORECASE)
CMD_LISTVOICES = re.compile(r"^\s*/listvoices\s*$", re.IGNORECASE)

def handle_voice_sample_commands():
    """
    Use Voice Bible -> Style Example as the import channel.

    Create/import:
      First line: /savevoice Name
      Then paste 1–12 pages underneath (the system will split + lane-tag paragraphs).

    Manage:
      /listvoices
      /deletevoice Name
    """
    raw = st.session_state.voice_sample or ""
    if not raw.strip():
        return

    lines = raw.splitlines()
    first = lines[0].strip()

    if CMD_LISTVOICES.match(first):
        names = sorted(st.session_state.voices.keys())
        st.session_state.tool_output = "VOICES:\n" + ("\n".join(names) if names else "— none —")
        st.session_state.voice_status = "Listed voices."
        st.session_state.voice_sample = ""
        return

    m = CMD_DELETEVOICE.match(first)
    if m:
        name = m.group(1).strip()
        msg = delete_voice(name)
        st.session_state.voice_status = msg
        st.session_state.tool_output = msg
        st.session_state.voice_sample = ""
        return

    m = CMD_SAVEVOICE.match(first)
    if m:
        name = m.group(1).strip()
        sample = "\n".join(lines[1:]).strip()
        if len(sample) < 200:
            st.session_state.voice_status = "Paste at least ~200 characters under /savevoice Name."
            st.session_state.tool_output = st.session_state.voice_status
            st.session_state.voice_sample = ""
            return
        imported, counts = import_samples_to_voice(name, sample)
        msg = f"Imported → {name}: {imported} lane-tagged chunks | " + " • ".join([f"{k}={v}" for k, v in counts.items()])
        st.session_state.voice_status = msg
        st.session_state.tool_output = msg
        st.session_state.voice_sample = ""
        return

handle_voice_sample_commands()

# ============================================================
# “TRAINED VOICE” passive training from current draft (session-only)
# ============================================================
def capture_voice_snippet_from_draft():
    """
    If Trained Voice is ON and a voice is selected,
    it learns passively from your draft into the appropriate lane.
    """
    if not st.session_state.vb_trained_on:
        return
    tv = st.session_state.trained_voice
    if not tv or tv == "— None —":
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

    lane = detect_lane(last)
    add_sample_to_voice_lane(tv, lane, last)
    st.session_state.voice_status = f"Trained {tv} [{lane}]: +1 paragraph"

# ============================================================
# STORY BIBLE AS CANON + IDEA BANK (MANDATORY)
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

def build_partner_brief(action_name: str, lane: str) -> str:
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

    lane_directive = f"""
LANE (MODE) ENFORCEMENT:
- Current lane: {lane}
- If lane is Dialogue: prioritize spoken rhythm, subtext, interruptions, and clean beats.
- If lane is Interiority: prioritize thought texture, honesty, distance, and sentence music.
- If lane is Action: prioritize clarity, impact, momentum, and concrete motion.
- If lane is Narration: prioritize scene texture, specificity, pacing, and viewpoint control.
Keep the output in the same lane unless the draft naturally transitions.
""".strip()

    # Voice controls (existing toggles/sliders; nothing removed)
    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
        vb.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {st.session_state.trained_intensity:.2f})")
    if st.session_state.vb_match_on and st.session_state.voice_sample.strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and st.session_state.voice_lock_prompt.strip():
        vb.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    # Trained voice exemplars (lane-aware)
    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)

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

{lane_directive}

VOICE CONTROLS:
{voice_controls}

TRAINED VOICE EXEMPLARS (lane-aware; mimic patterns, not content):
{ex_block}

STORY BIBLE (canon/constraints + idea bank):
{story_bible}

ACTION: {action_name}
""".strip()

# ============================================================
# OPTIONAL OPENAI CALL (safe; won’t crash app)
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
# LOCAL COPYEDIT + LOCAL FIND (fallback)
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

def local_find(text: str, query: str, limit: int = 12) -> List[Tuple[int, str]]:
    q = (query or "").strip()
    if not q:
        return []
    lines = (text or "").splitlines()
    hits = []
    for i, line in enumerate(lines, start=1):
        if q.lower() in line.lower():
            snippet = line.strip()
            if len(snippet) > 140:
                snippet = snippet[:140] + "…"
            hits.append((i, snippet))
            if len(hits) >= limit:
                break
    return hits

def _read_query_from_junk(default: str = "") -> str:
    raw = (st.session_state.junk or "").strip()

    m = CMD_FIND.match(raw)
    if m:
        return m.group(1).strip()
    m = CMD_SYN.match(raw)
    if m:
        return m.group(1).strip()
    m = CMD_SENT.match(raw)
    if m:
        return m.group(1).strip()

    if raw and len(raw) <= 80 and not raw.startswith("/"):
        return raw.strip()

    return default

# ============================================================
# PARTNER ACTIONS (wired to ALL bottom bar buttons)
# ============================================================
def partner_action(action: str):
    text = st.session_state.main_text or ""
    push_revision(action)

    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)
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

    try:
        # === GENERATIVE WRITING TOOLS (Story Bible + Lane-aware Trained Voice) ===
        if action == "Write":
            if use_ai:
                task = (
                    f"Continue decisively in the current lane ({lane}). Add 1–3 paragraphs that advance the scene. "
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
                    f"Rewrite for professional quality in the current lane ({lane}). Tighten, sharpen, commit. "
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
                    f"Expand with meaningful depth in the current lane ({lane}): concrete detail, specificity, subtext. "
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
                    f"Replace the final sentence with a stronger one in the same lane ({lane}) (same meaning). "
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
                    f"Add vivid description with control in the current lane ({lane}): sharpen nouns/verbs, add sensory detail, keep pace. "
                    "Preserve canon. Return full revised text."
                )
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        # === TEXT CHECKING / EDITING TOOLS (project-aware) ===
        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = (
                    f"Production copyedit in the current lane ({lane}): spelling/grammar/punctuation. Preserve voice and meaning. "
                    "Do not flatten style. Preserve canon. Return full revised text."
                )
                out = call_openai(brief, task, cleaned)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
            return

        if action == "Find":
            query = _read_query_from_junk(default="")
            if not query:
                st.session_state.tool_output = "Find: enter /find: term (or type a short term) in Junk Drawer."
                st.session_state.voice_status = "Find: waiting for query."
                st.session_state.last_action = "Find"
                return
            hits = local_find(text, query)
            if hits:
                lines = "\n".join([f"Line {ln}: {snip}" for ln, snip in hits])
                st.session_state.tool_output = f"FIND: '{query}'\n\n{lines}"
                st.session_state.voice_status = f"Find: {len(hits)} hit(s)."
            else:
                st.session_state.tool_output = f"FIND: '{query}'\n\nNo hits in draft."
                st.session_state.voice_status = "Find: 0 hits."
            st.session_state.last_action = "Find"
            return

        if action == "Synonym":
            query = _read_query_from_junk(default="")
            if not query:
                st.session_state.tool_output = "Synonym: enter /syn: word (or type a short word) in Junk Drawer."
                st.session_state.voice_status = "Synonym: waiting for word."
                st.session_state.last_action = "Synonym"
                return
            if use_ai:
                task = (
                    f"Provide 12 strong replacements for: '{query}'. "
                    "Rank by fit for this project's voice and the current lane. "
                    "Avoid thesaurus weirdness. If nuance changes, label it."
                )
                out = call_openai(brief, task, query)
                st.session_state.tool_output = f"SYNONYMS FOR: '{query}'\n\n{out}"
                st.session_state.voice_status = "Synonym: generated."
            else:
                st.session_state.tool_output = f"SYNONYMS FOR: '{query}'\n\n(Enable OPENAI_API_KEY for synonym generation.)"
                st.session_state.voice_status = "Synonym: no AI key."
            st.session_state.last_action = "Synonym"
            return

        if action == "Sentence":
            directive = _read_query_from_junk(default="tighten")
            paras = _split_paragraphs(text)
            if not paras:
                st.session_state.tool_output = "Sentence: draft is empty."
                st.session_state.voice_status = "Sentence: nothing to edit."
                st.session_state.last_action = "Sentence"
                return
            if use_ai:
                task = (
                    f"Perform a sentence-level pass on the FINAL paragraph with directive: '{directive}'. "
                    f"Keep it in the same lane ({lane}). Be decisive. Preserve meaning, voice, and canon. "
                    "Improve rhythm, clarity, and force. Return ONLY the revised final paragraph."
                )
                out = call_openai(brief, task, paras[-1])
                if out and out.strip():
                    paras[-1] = out.strip()
                    apply_replace(_join_paragraphs(paras))
                    st.session_state.tool_output = f"SENTENCE PASS ({directive})\n\nRevised final paragraph."
                    st.session_state.voice_status = "Sentence: applied."
                else:
                    st.session_state.tool_output = "Sentence: no output returned."
                    st.session_state.voice_status = "Sentence: no change."
                st.session_state.last_action = "Sentence"
            else:
                paras[-1] = local_cleanup(paras[-1])
                apply_replace(_join_paragraphs(paras))
                st.session_state.tool_output = "Sentence: applied local cleanup (enable OPENAI_API_KEY for full sentence partner)."
                st.session_state.voice_status = "Sentence: local."
                st.session_state.last_action = "Sentence"
            return

        # No-op fallback
        apply_replace(text)

    except Exception as e:
        st.session_state.voice_status = f"Engine: {str(e)}"
        st.session_state.tool_output = f"ERROR:\n{str(e)}"
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
        st.text_area("Tool Output", key="tool_output", height=140, disabled=True)

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

    # Bottom bar — editing (EXACT BUTTONS KEPT; project-aware)
    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell"):
        partner_action("Spell")
    if b2[1].button("Grammar", key="btn_grammar"):
        partner_action("Grammar")
    if b2[2].button("Find", key="btn_find"):
        partner_action("Find")
    if b2[3].button("Synonym", key="btn_synonym"):
        partner_action("Synonym")
    if b2[4].button("Sentence", key="btn_sentence"):
        partner_action("Sentence")

# ============================================================
# RIGHT — VOICE BIBLE (TOP → BOTTOM, EXACT FEATURES KEPT)
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

    # 3. Trained Voices (selector upgraded: Voice A/B + imported voices)
    st.checkbox("Enable Trained Voice", key="vb_trained_on")
    trained_options = voice_names_for_selector()
    if st.session_state.trained_voice not in trained_options:
        st.session_state.trained_voice = "— None —"
    st.selectbox(
        "Trained Voice",
        trained_options,
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on
    )
    st.slider("Trained Voice Intensity", 0.0, 1.0, key="trained_intensity", disabled=not st.session_state.vb_trained_on)

    st.divider()

    # 4. Match My Style (also your “import channel” via commands)
    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on,
        help="Import a distinct voice (session-only): first line '/savevoice Name' then paste pages underneath. Also: /listvoices, /deletevoice Name"
    )
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
    st.info("Auto-Save All")
