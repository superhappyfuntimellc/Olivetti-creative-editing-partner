import os
import re
import math
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import streamlit as st

# ============================================================
# OLIVETTI DESK — One code to rule them all
# Story Bible > Start Project > Rough > Edit > Final
# Junk Drawer = Idea Bank (per context)
# Voice Bible controls the writing programs (every tab has on/off + intensity)
# Action Controls: every button has enable + intensity (lockable per project)
# ============================================================

# --- environment hygiene
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

DEFAULT_MODEL = "gpt-4.1-mini"
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # type: ignore[attr-defined]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)  # type: ignore[attr-defined]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

# --- page
st.set_page_config(page_title="Olivetti Desk", layout="wide", initial_sidebar_state="expanded")

# --- make the desk big + readable (professional)
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
    label, .stSelectbox label, .stSlider label { font-size: 14px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# CONSTANTS
# ============================================================
LANES = ["Dialogue", "Narration", "Interiority", "Action"]
GLOBAL_VOICE_PREFIX = "🌐 "
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]

ACTIONS_PRIMARY = ["Write", "Rewrite", "Expand", "Rephrase", "Describe"]
ACTIONS_SECONDARY = ["Spell", "Grammar", "Find", "Synonym", "Sentence"]
ALL_ACTIONS = ACTIONS_PRIMARY + ACTIONS_SECONDARY

AUTOSAVE_DIR = "autosave"
AUTOSAVE_PATH = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")

WORD_RE = re.compile(r"[A-Za-z']+")

IMPORT_MERGE_MODES = ["Append", "Replace"]

# ============================================================
# UTILS
# ============================================================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def clamp01(x: float) -> float:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    return max(0.0, min(1.0, v))

def normalize_text(s: str) -> str:
    t = (s or "").strip()
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()

def split_paragraphs(text: str) -> List[str]:
    t = normalize_text(text)
    if not t:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", t, flags=re.MULTILINE) if p.strip()]

def first_nonempty_line(s: str) -> str:
    for line in (s or "").splitlines():
        if line.strip():
            return line.strip()
    return ""

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or "")]

def hash_vec(text: str, dims: int = 512) -> List[float]:
    vec = [0.0] * dims
    toks = tokenize(text)
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        vec[h % dims] += 1.0
    for i, v in enumerate(vec):
        if v > 0:
            vec[i] = 1.0 + math.log(v)
    return vec

def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def safe_extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1]
            t = re.sub(r"^\s*json\s*\n", "", t.strip(), flags=re.IGNORECASE)
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    chunk = t[start:end+1]
    try:
        return json.loads(chunk)
    except Exception:
        try:
            chunk2 = chunk.replace("\u201c", '"').replace("\u201d", '"')
            return json.loads(chunk2)
        except Exception:
            return {}

# ============================================================
# LANE DETECTION (lightweight)
# ============================================================
THOUGHT_WORDS = {
    "think","thought","felt","wondered","realized","remembered","knew","noticed","decided",
    "hoped","feared","wanted","imagined","could","should","would"
}
ACTION_VERBS = {
    "run","ran","walk","walked","grab","grabbed","push","pushed","pull","pulled","slam","slammed",
    "hit","struck","kick","kicked","turn","turned","snap","snapped","dive","dived","duck","ducked",
    "rush","rushed","lunge","lunged","climb","climbed","drop","dropped","throw","threw","fire","fired",
    "aim","aimed","break","broke","shatter","shattered","step","stepped","move","moved","reach","reached"
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

    toks = tokenize(p)
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


def add_voice_samples(vault: Dict[str, Any], voice_key: str, raw_text: str,
                     auto_lane: bool = True, forced_lane: str = "Narration",
                     max_samples: int = 60, min_words: int = 8) -> int:
    """Add samples into a voice vault (project or global). Returns # added."""
    if not raw_text or not raw_text.strip():
        return 0
    voice_key = (voice_key or "").strip() or "Global Voice"
    if voice_key not in (vault or {}):
        vault[voice_key] = {"created_ts": now_ts(), "lanes": {ln: [] for ln in LANES}}
    vault[voice_key].setdefault("lanes", {ln: [] for ln in LANES})
    for ln in LANES:
        vault[voice_key]["lanes"].setdefault(ln, [])

    paras = split_paragraphs(raw_text)
    added = 0
    for p in paras:
        if len(tokenize(p)) < int(min_words):
            continue
        ln = detect_lane(p) if auto_lane else (forced_lane if forced_lane in LANES else "Narration")
        vault[voice_key]["lanes"][ln].append({"ts": now_ts(), "text": p.strip(), "vec": hash_vec(p)})
        added += 1
        if added >= int(max_samples):
            break

    # Cap memory per lane
    CAP = 250
    for ln in LANES:
        vault[voice_key]["lanes"][ln] = (vault[voice_key]["lanes"].get(ln, []) or [])[-CAP:]
    return added

def current_lane_from_draft(text: str) -> str:
    paras = split_paragraphs(text)
    if not paras:
        return "Narration"
    return detect_lane(paras[-1])

# ============================================================
# INTENSITY
# ============================================================
def intensity_profile(x: float) -> str:
    if x <= 0.25:
        return "LOW: conservative, literal, minimal invention, prioritize continuity and clarity."
    if x <= 0.60:
        return "MED: balanced creativity, stronger phrasing, controlled invention within canon."
    if x <= 0.85:
        return "HIGH: bolder choices, richer specificity; still obey canon and lane."
    return "MAX: aggressive originality and voice; still obey canon, no random derailments."

def temperature_from_intensity(x: float) -> float:
    x = clamp01(x)
    return 0.15 + (x * 0.95)

# ============================================================
# ACTION CONTROLS (per button)
# ============================================================
def default_action_controls() -> Dict[str, Any]:
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {"enabled": True, "use_global": True, "intensity": 0.75}
    return {"locked": False, "items": items}

def ac_key(action: str, field: str) -> str:
    return f"ac__{action}__{field}"

def init_action_control_scalars(ac: Dict[str, Any]) -> None:
    ac = ac or default_action_controls()
    st.session_state.ac_locked = bool(ac.get("locked", False))
    items = ac.get("items", {}) or {}
    for a in ALL_ACTIONS:
        it = items.get(a, {}) or {}
        st.session_state[ac_key(a, "enabled")] = bool(it.get("enabled", True))
        st.session_state[ac_key(a, "use_global")] = bool(it.get("use_global", True))
        st.session_state[ac_key(a, "intensity")] = clamp01(it.get("intensity", 0.75))

def action_controls_struct() -> Dict[str, Any]:
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {
            "enabled": bool(st.session_state.get(ac_key(a, "enabled"), True)),
            "use_global": bool(st.session_state.get(ac_key(a, "use_global"), True)),
            "intensity": clamp01(st.session_state.get(ac_key(a, "intensity"), 0.75)),
        }
    return {"locked": bool(st.session_state.get("ac_locked", False)), "items": items}

def effective_intensity_for_action(action: str) -> float:
    global_x = clamp01(st.session_state.get("ai_intensity", 0.75))
    use_global = bool(st.session_state.get(ac_key(action, "use_global"), True))
    return global_x if use_global else clamp01(st.session_state.get(ac_key(action, "intensity"), global_x))

def action_enabled(action: str) -> bool:
    return bool(st.session_state.get(ac_key(action, "enabled"), True))

# ============================================================
# IMPORT CONTROLS
# ============================================================
def default_import_controls() -> Dict[str, Any]:
    return {"use_ai": True, "use_global_intensity": True, "intensity": 0.65, "merge_mode": "Append"}

def import_controls_from_session() -> Dict[str, Any]:
    return {
        "use_ai": bool(st.session_state.get("import_use_ai", True)),
        "use_global_intensity": bool(st.session_state.get("import_use_global", True)),
        "intensity": clamp01(st.session_state.get("import_intensity", 0.65)),
        "merge_mode": st.session_state.get("import_merge_mode", "Append"),
    }

def apply_import_controls(ctrl: Dict[str, Any]) -> None:
    ctrl = ctrl or default_import_controls()
    st.session_state.import_use_ai = bool(ctrl.get("use_ai", True))
    st.session_state.import_use_global = bool(ctrl.get("use_global_intensity", True))
    st.session_state.import_intensity = clamp01(ctrl.get("intensity", 0.65))
    mm = ctrl.get("merge_mode", "Append")
    st.session_state.import_merge_mode = mm if mm in IMPORT_MERGE_MODES else "Append"

def effective_import_intensity() -> float:
    if bool(st.session_state.get("import_use_global", True)):
        return clamp01(st.session_state.get("ai_intensity", 0.75))
    return clamp01(st.session_state.get("import_intensity", 0.65))

# ============================================================
# PROJECT + WORKSPACE DATA MODEL
# ============================================================
def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {"Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
            "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}}}

def default_global_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {"Global Voice": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}}}

def is_global_voice(name: str) -> bool:
    return bool(name) and name.startswith(GLOBAL_VOICE_PREFIX)

def global_label(name: str) -> str:
    return f"{GLOBAL_VOICE_PREFIX}{name}"

def global_unlabel(name: str) -> str:
    return name[len(GLOBAL_VOICE_PREFIX):] if is_global_voice(name) else name

def default_voice_bible() -> Dict[str, Any]:
    return {
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_lock_on": False,

        "writing_style": "Neutral",
        "genre": "Literary",
        "trained_voice": "— None —",
        "voice_sample": "",
        "voice_lock_prompt": "",

        "style_intensity": 0.6,
        "genre_intensity": 0.6,
        "trained_intensity": 0.7,
        "match_intensity": 0.8,
        "lock_intensity": 1.0,

        "pov": "Close Third",
        "tense": "Past",

        "ai_intensity": 0.75,
    }

def default_workspace() -> Dict[str, Any]:
    return {
        "title": "",
        "draft": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "idea_bank": "",
        "voice_bible": default_voice_bible(),
        "action_controls": default_action_controls(),
        "import_controls": default_import_controls(),
        "imports_log": [],
        "voices": default_voice_vault(),
    }

def new_project_payload(title: str) -> Dict[str, Any]:
    ts = now_ts()
    title = title.strip() if title.strip() else "Untitled Project"
    return {
        "id": hashlib.md5(f"{title}|{ts}".encode("utf-8")).hexdigest()[:12],
        "title": title,
        "created_ts": ts,
        "updated_ts": ts,
        "bay": "NEW",
        "draft": "",
        "story_bible_id": hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12],
        "story_bible_created_ts": ts,
        "story_bible_locked_ts": None,  # stamped when "Start Project" happens
        "story_bible_lock_reason": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "idea_bank": "",
        "voice_bible": default_voice_bible(),
        "action_controls": default_action_controls(),
        "import_controls": default_import_controls(),
        "imports_log": [],
        "locks": {"story_bible_lock": True, "story_bible_edit_unlocked": False, "story_bible_last_unlock_ts": "", "voice_fingerprint_lock": True, "lane_lock": False, "forced_lane": "Narration"},
        "voices": default_voice_vault(),
    }

# ============================================================
# SESSION INIT
# ============================================================
def init_state():
    defaults = {
        "active_bay": "NEW",
        "projects": {},
        "active_project_by_bay": {b: None for b in BAYS},

        "workspace": default_workspace(),
        "workspace_title": "",
        "desk_workspace_title": "",  # (NEW) alias input for desk, synced to workspace_title
        "sb_unlock_toggle": False,  # Hard lock UI state

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
        "idea_bank_last": "",
        "tool_output": "",

        # Voice Bible scalars
        **default_voice_bible(),

        "locks": {"story_bible_lock": True, "story_bible_edit_unlocked": False, "story_bible_last_unlock_ts": "", "voice_fingerprint_lock": True, "lane_lock": False, "forced_lane": "Narration"},

        "voices": {},
        "voices_seeded": False,
        "global_voices": {},
        "global_voices_seeded": False,
        "global_voice_on": True,
        "global_voice": global_label("Global Voice"),
        "global_voice_strength": 0.9,
        "ac_locked": False,

        # Promote UI
        "promote_selected": [],
        "promote_target": "World",
        "promote_remove_from_ideas": False,

        # Import UI
        "import_paste": "",
        "import_use_ai": True,
        "import_use_global": True,
        "import_intensity": 0.65,
        "import_merge_mode": "Append",

        # Desk shortcuts
        "desk_new_project_title": "",
        "desk_copy_story_bible": True,
        "desk_copy_draft": False,
        "desk_copy_idea_bank": False,
        "desk_insert_section": "Synopsis",

        "last_saved_digest": "",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    for a in ALL_ACTIONS:
        st.session_state.setdefault(ac_key(a, "enabled"), True)
        st.session_state.setdefault(ac_key(a, "use_global"), True)
        st.session_state.setdefault(ac_key(a, "intensity"), 0.75)

init_state()

# ============================================================
# MODE HELPERS
# ============================================================
def in_workspace_mode() -> bool:
    return st.session_state.active_bay == "NEW" and not st.session_state.project_id

# ============================================================
# VOICE BIBLE <-> SESSION
# ============================================================
def vb_struct_from_session() -> Dict[str, Any]:
    return {
        "vb_style_on": bool(st.session_state.vb_style_on),
        "vb_genre_on": bool(st.session_state.vb_genre_on),
        "vb_trained_on": bool(st.session_state.vb_trained_on),
        "vb_match_on": bool(st.session_state.vb_match_on),
        "vb_lock_on": bool(st.session_state.vb_lock_on),

        "writing_style": st.session_state.writing_style,
        "genre": st.session_state.genre,
        "trained_voice": st.session_state.trained_voice,
        "voice_sample": st.session_state.voice_sample,
        "voice_lock_prompt": st.session_state.voice_lock_prompt,

        "style_intensity": float(st.session_state.style_intensity),
        "genre_intensity": float(st.session_state.genre_intensity),
        "trained_intensity": float(st.session_state.trained_intensity),
        "match_intensity": float(st.session_state.match_intensity),
        "lock_intensity": float(st.session_state.lock_intensity),

        "pov": st.session_state.pov,
        "tense": st.session_state.tense,

        "ai_intensity": float(st.session_state.ai_intensity),
    }

def vb_apply_to_session(vb: Dict[str, Any]) -> None:
    vb = vb or default_voice_bible()
    for k, v in vb.items():
        if k in st.session_state:
            st.session_state[k] = v

# ============================================================
# WORKSPACE <-> SESSION
# ============================================================
def save_workspace_from_session() -> None:
    w = st.session_state.workspace or default_workspace()
    w["title"] = st.session_state.workspace_title
    w["draft"] = st.session_state.main_text
    w["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    w["idea_bank"] = st.session_state.junk
    w["voice_bible"] = vb_struct_from_session()
    w["action_controls"] = action_controls_struct()
    w["import_controls"] = import_controls_from_session()
    w.setdefault("imports_log", [])
    w["voices"] = compact_voice_vault(st.session_state.voices)
    st.session_state.workspace = w

def load_workspace_into_session() -> None:
    w = st.session_state.workspace or default_workspace()
    sb = (w.get("story_bible", {}) or {})
    st.session_state.workspace_title = w.get("title", "") or ""
    st.session_state.desk_workspace_title = st.session_state.workspace_title
    st.session_state.main_text = w.get("draft", "") or ""
    st.session_state.synopsis = sb.get("synopsis", "") or ""
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "") or ""
    st.session_state.world = sb.get("world", "") or ""
    st.session_state.characters = sb.get("characters", "") or ""
    st.session_state.outline = sb.get("outline", "") or ""
    st.session_state.junk = w.get("idea_bank", "") or ""
    st.session_state.idea_bank_last = st.session_state.junk

    vb_apply_to_session(w.get("voice_bible", default_voice_bible()))
    init_action_control_scalars(w.get("action_controls", default_action_controls()))
    apply_import_controls(w.get("import_controls", default_import_controls()))

    st.session_state.voices = rebuild_vectors_in_voice_vault(w.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True

def reset_workspace_content(keep_templates: bool = True) -> None:
    w = st.session_state.workspace or default_workspace()
    vb = w.get("voice_bible", default_voice_bible())
    ac = w.get("action_controls", default_action_controls())
    ic = w.get("import_controls", default_import_controls())
    voices = w.get("voices", default_voice_vault())

    st.session_state.workspace = default_workspace()
    if keep_templates:
        st.session_state.workspace["voice_bible"] = vb
        st.session_state.workspace["action_controls"] = ac
        st.session_state.workspace["import_controls"] = ic
        st.session_state.workspace["voices"] = voices

    st.session_state.workspace_title = ""
    st.session_state.desk_workspace_title = ""
    if in_workspace_mode():
        load_workspace_into_session()

# ============================================================
# VOICE VAULT (store text + vectors)
# ============================================================
def rebuild_vectors_in_voice_vault(compact_voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (compact_voices or {}).items():
        created_ts = v.get("created_ts") or now_ts()
        lanes_in = v.get("lanes", {}) or {}
        lanes_out: Dict[str, Any] = {ln: [] for ln in LANES}
        for ln in LANES:
            samples = lanes_in.get(ln, []) or []
            for s in samples:
                txt = normalize_text(s.get("text", ""))
                if not txt:
                    continue
                lanes_out[ln].append({"ts": s.get("ts") or now_ts(), "text": txt, "vec": hash_vec(txt)})
        out[vname] = {"created_ts": created_ts, "lanes": lanes_out}
    return out

def compact_voice_vault(voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (voices or {}).items():
        lanes_out: Dict[str, Any] = {}
        for ln in LANES:
            samples = (v.get("lanes", {}) or {}).get(ln, []) or []
            lanes_out[ln] = [{"ts": s.get("ts"), "text": s.get("text", "")} for s in samples if s.get("text")]
        out[vname] = {"created_ts": v.get("created_ts"), "lanes": lanes_out}
    return out

def seed_default_voices():
    if st.session_state.voices_seeded:
        return
    st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
    st.session_state.voices_seeded = True

seed_default_voices()

def seed_default_global_voices():
    if st.session_state.global_voices_seeded:
        return
    st.session_state.global_voices = rebuild_vectors_in_voice_vault(default_global_voice_vault())
    st.session_state.global_voices_seeded = True
    if not st.session_state.global_voice:
        st.session_state.global_voice = global_label("Global Voice")

seed_default_global_voices()


def global_voice_names_for_selector() -> List[str]:
    # Stored without prefix internally; selector displays with prefix.
    return sorted([k for k in (st.session_state.global_voices or {}).keys()])

def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in (st.session_state.voices or {}).keys() if k not in ("Voice A", "Voice B")])
    globals_ = [global_label(n) for n in global_voice_names_for_selector()]
    return base + customs + globals_

def get_voice_vault(voice_name: str) -> Optional[Dict[str, Any]]:
    if is_global_voice(voice_name):
        return (st.session_state.global_voices or {}).get(global_unlabel(voice_name))
    return (st.session_state.voices or {}).get(voice_name)

def retrieve_exemplars(voice_name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    v = get_voice_vault(voice_name)
    if not v:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = (v.get("lanes", {}) or {}).get(lane, []) or []
    if not pool:
        return []
    qv = hash_vec(query_text)
    scored = [(cosine(qv, s.get("vec", [])), s.get("text", "")) for s in pool[-180:]]
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
# PROJECT <-> SESSION
# ============================================================
def load_project_into_session(pid: str) -> None:
    p = st.session_state.projects.get(pid)
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

    st.session_state.junk = p.get("idea_bank", "") or ""
    st.session_state.idea_bank_last = st.session_state.junk

    vb_apply_to_session(p.get("voice_bible", default_voice_bible()))
    locks = p.get("locks", {}) or {}
    if not isinstance(locks, dict):
        locks = {}
    # Hard lock defaults (older autosaves may not have these keys)
    locks.setdefault("story_bible_lock", True)
    locks.setdefault("story_bible_edit_unlocked", False)
    locks.setdefault("story_bible_last_unlock_ts", "")
    locks.setdefault("voice_fingerprint_lock", True)
    locks.setdefault("lane_lock", False)
    locks.setdefault("forced_lane", "Narration")
    st.session_state.locks = locks
    p["locks"] = locks
    # Sync the unlock toggle widget with project state
    st.session_state.sb_unlock_toggle = bool(locks.get("story_bible_edit_unlocked", False))

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True

    init_action_control_scalars(p.get("action_controls", default_action_controls()))
    apply_import_controls(p.get("import_controls", default_import_controls()))

def save_session_into_project() -> None:
    pid = st.session_state.project_id
    if not pid:
        return
    p = st.session_state.projects.get(pid)
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
    p["idea_bank"] = st.session_state.junk
    p["voice_bible"] = vb_struct_from_session()
    p["action_controls"] = action_controls_struct()
    p["import_controls"] = import_controls_from_session()
    p.setdefault("imports_log", [])
    p["locks"] = st.session_state.locks
    p["voices"] = compact_voice_vault(st.session_state.voices)

def list_projects_in_bay(bay: str) -> List[Tuple[str, str]]:
    items = []
    for pid, p in (st.session_state.projects or {}).items():
        if p.get("bay") == bay:
            items.append((pid, p.get("title", "Untitled")))
    items.sort(key=lambda x: x[1].lower())
    return items

def ensure_bay_has_active_project(bay: str) -> None:
    pid = st.session_state.active_project_by_bay.get(bay)
    if pid and pid in st.session_state.projects and st.session_state.projects[pid].get("bay") == bay:
        return
    items = list_projects_in_bay(bay)
    st.session_state.active_project_by_bay[bay] = items[0][0] if items else None

def switch_bay(target_bay: str) -> None:
    if in_workspace_mode():
        save_workspace_from_session()
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
            st.session_state.junk = ""
            st.session_state.idea_bank_last = ""
            st.session_state.tool_output = ""
            st.session_state.voice_status = f"{target_bay}: (empty)"
    st.session_state.last_action = f"Bay → {target_bay}"

def promote_project(pid: str, to_bay: str) -> None:
    p = st.session_state.projects.get(pid)
    if not p:
        return
    p["bay"] = to_bay
    p["updated_ts"] = now_ts()

def start_project_from_workspace() -> Optional[str]:
    if not in_workspace_mode():
        return None

    title = (st.session_state.workspace_title or "").strip()
    if not title:
        title = first_nonempty_line(st.session_state.synopsis) or f"New Project {now_ts()}"

    p = new_project_payload(title)
    p["bay"] = "NEW"

    # bind the workspace story bible + draft + ideas to the new project
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    p["idea_bank"] = st.session_state.junk
    p["voice_bible"] = vb_struct_from_session()
    p["action_controls"] = action_controls_struct()
    p["import_controls"] = import_controls_from_session()
    p["voices"] = compact_voice_vault(st.session_state.voices)

    # STAMP: Story Bible lock event (project-specific binding)
    p["story_bible_locked_ts"] = now_ts()
    p["story_bible_lock_reason"] = "Started from Story Bible workspace"

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    load_project_into_session(p["id"])
    st.session_state.voice_status = f"Started Project in NEW: {st.session_state.project_title}"
    st.session_state.last_action = "Start Project"

    reset_workspace_content(keep_templates=True)
    return p["id"]

def desk_create_new_project(title: str, copy_bible: bool, copy_draft: bool, copy_ideas: bool) -> Optional[str]:
    if in_workspace_mode():
        save_workspace_from_session()
    save_session_into_project()

    t = (title or "").strip()
    if not t:
        t = first_nonempty_line(st.session_state.synopsis) or f"New Project {now_ts()}"

    p = new_project_payload(t)
    p["bay"] = "NEW"

    if copy_bible:
        p["story_bible"] = {
            "synopsis": st.session_state.synopsis,
            "genre_style_notes": st.session_state.genre_style_notes,
            "world": st.session_state.world,
            "characters": st.session_state.characters,
            "outline": st.session_state.outline,
        }
    if copy_draft:
        p["draft"] = st.session_state.main_text or ""
    if copy_ideas:
        p["idea_bank"] = st.session_state.junk or ""

    p["voice_bible"] = vb_struct_from_session()
    p["action_controls"] = action_controls_struct()
    p["import_controls"] = import_controls_from_session()
    p["voices"] = compact_voice_vault(st.session_state.voices)

    # STAMP lock (because it binds a Story Bible snapshot if copied)
    if copy_bible:
        p["story_bible_locked_ts"] = now_ts()
        p["story_bible_lock_reason"] = "Created from desk (copied Story Bible)"
    else:
        p["story_bible_locked_ts"] = None
        p["story_bible_lock_reason"] = ""

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    switch_bay("NEW")
    load_project_into_session(p["id"])
    st.session_state.voice_status = f"New Project created: {st.session_state.project_title}"
    st.session_state.last_action = "Desk: New Project"
    return p["id"]

# ============================================================
# AUTOSAVE
# ============================================================
def payload() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-storybible-globalvoice-v1"},
        "workspace": st.session_state.workspace,
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "global": {
            "voices": compact_voice_vault(st.session_state.global_voices),
            "global_voice_on": bool(st.session_state.global_voice_on),
            "global_voice": st.session_state.global_voice,
            "global_voice_strength": float(st.session_state.global_voice_strength),
        },
        "projects": st.session_state.projects,
    }

def digest(pl: Dict[str, Any]) -> str:
    s = json.dumps(pl, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def save_all_to_disk(force: bool = False) -> None:
    try:
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        pl = payload()
        dig = digest(pl)
        if (not force) and dig == st.session_state.last_saved_digest:
            return
        with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(pl, f, ensure_ascii=False, indent=2)
        st.session_state.last_saved_digest = dig
    except Exception as e:
        st.session_state.voice_status = f"Autosave warning: {e}"

def load_all_from_disk() -> None:
    if not os.path.exists(AUTOSAVE_PATH):
        switch_bay("NEW")
        return
    try:
        with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
            pl = json.load(f)

        # ---- Global (cross-project) state ----
        g = pl.get("global", {})
        if isinstance(g, dict):
            gv = g.get("voices", {})
            if isinstance(gv, dict):
                st.session_state.global_voices = rebuild_vectors_in_voice_vault(gv)
                st.session_state.global_voices_seeded = True
            st.session_state.global_voice_on = bool(g.get("global_voice_on", True))
            gv_sel = g.get("global_voice", global_label("Global Voice"))
            st.session_state.global_voice = gv_sel if isinstance(gv_sel, str) else global_label("Global Voice")
            st.session_state.global_voice_strength = float(g.get("global_voice_strength", 0.9))

        # ---- Workspace ----
        ws = pl.get("workspace")
        if isinstance(ws, dict):
            st.session_state.workspace = ws
            st.session_state.workspace_title = ws.get("title", "") or ""
            st.session_state.desk_workspace_title = st.session_state.workspace_title

        # ---- Projects ----
        projs = pl.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = pl.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            for b in BAYS:
                apbb.setdefault(b, None)
            st.session_state.active_project_by_bay = apbb

        ab = pl.get("active_bay", "NEW")
        if ab not in BAYS:
            ab = "NEW"
        st.session_state.active_bay = ab

        ensure_bay_has_active_project(ab)
        pid = st.session_state.active_project_by_bay.get(ab)

        if pid:
            load_project_into_session(pid)
        else:
            switch_bay(ab)

        st.session_state.voice_status = f"Loaded autosave ({pl.get('meta', {}).get('saved_at','')})."
        st.session_state.last_saved_digest = digest(payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"
        switch_bay("NEW")




def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    save_all_to_disk()

if "did_load_autosave" not in st.session_state:
    st.session_state.did_load_autosave = True
    load_all_from_disk()

# ============================================================
# AI BRIEF
# ============================================================
def story_bible_text() -> str:
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

def build_partner_brief(action_name: str, lane: str, intensity_x: float) -> str:
    sb = story_bible_text()
    idea_bank = (st.session_state.junk or "").strip() or "— None —"

    vb_lines = []
    if bool(st.session_state.get("global_voice_on", True)) and st.session_state.global_voice and st.session_state.global_voice != "— None —":
        vb_lines.append(f"Global Voice: {st.session_state.global_voice} (strength {float(st.session_state.global_voice_strength):.2f})")
    if st.session_state.vb_style_on:
        vb_lines.append(f"Writing Style: {st.session_state.writing_style} (intensity {float(st.session_state.style_intensity):.2f})")
    if st.session_state.vb_genre_on:
        vb_lines.append(f"Genre Influence: {st.session_state.genre} (intensity {float(st.session_state.genre_intensity):.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
        vb_lines.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {float(st.session_state.trained_intensity):.2f})")
    if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
        vb_lines.append(f"Match Sample (intensity {float(st.session_state.match_intensity):.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and (st.session_state.voice_lock_prompt or "").strip():
        vb_lines.append(f"VOICE LOCK (strength {float(st.session_state.lock_intensity):.2f}):\n{st.session_state.voice_lock_prompt.strip()}")

    voice_controls = "\n\n".join(vb_lines).strip() if vb_lines else "— None enabled —"

    project_exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        project_exemplars = retrieve_mixed_exemplars(tv, lane, query)

    project_ex_block = "\n\n---\n\n".join(project_exemplars) if project_exemplars else "— None —"

    global_exemplars: List[str] = []
    gv = st.session_state.global_voice
    if bool(st.session_state.get("global_voice_on", True)) and gv and gv != "— None —":
        ctx2 = (st.session_state.main_text or "")[-2500:]
        query2 = ctx2 if ctx2.strip() else st.session_state.synopsis
        global_exemplars = retrieve_mixed_exemplars(gv, lane, query2)

    global_ex_block = "\n\n---\n\n".join(global_exemplars) if global_exemplars else "— None —"
    intensity_x = clamp01(intensity_x)

    return f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
Professional output only. No UI talk. No process talk.

STORY BIBLE IS PROJECT-SPECIFIC CANON + CREATION SPACE.
Never contradict canon.

IDEA BANK (Junk Drawer) is supportive, non-canon unless promoted into Story Bible/Draft.
Use it only when relevant.

LANE: {lane}

EFFECTIVE INTENSITY (this action): {intensity_x:.2f}
PROFILE: {intensity_profile(intensity_x)}

VOICE CONTROLS:
{voice_controls}

GLOBAL VOICE EXEMPLARS (mimic patterns, not content):
{global_ex_block}

PROJECT TRAINED EXEMPLARS (mimic patterns, not content):
{project_ex_block}

STORY BIBLE:
{sb}

IDEA BANK:
{idea_bank}

ACTION: {action_name}
""".strip()

def call_openai(system_brief: str, user_task: str, text: str, intensity_x: float) -> str:
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
            {"role": "user", "content": f"{user_task}\n\nTEXT:\n{text.strip()}"},
        ],
        temperature=temperature_from_intensity(intensity_x),
    )
    return (resp.choices[0].message.content or "").strip()

# ============================================================
# LOCAL TOOLS
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

def local_find(term: str) -> str:
    q = (term or "").strip()
    if not q:
        return "Find: empty query."
    ql = q.lower()

    targets: List[Tuple[str, str]] = [
        ("DRAFT", st.session_state.main_text or ""),
        ("SYNOPSIS", st.session_state.synopsis or ""),
        ("GENRE/STYLE", st.session_state.genre_style_notes or ""),
        ("WORLD", st.session_state.world or ""),
        ("CHARACTERS", st.session_state.characters or ""),
        ("OUTLINE", st.session_state.outline or ""),
        ("IDEA BANK", st.session_state.junk or ""),
        ("VOICE SAMPLE", st.session_state.voice_sample or ""),
        ("VOICE LOCK", st.session_state.voice_lock_prompt or ""),
    ]

    hits: List[str] = []
    for label, txt in targets:
        if not txt.strip():
            continue
        paras = split_paragraphs(txt)
        for i, p in enumerate(paras, start=1):
            if ql in p.lower():
                snippet = p.strip()
                if len(snippet) > 260:
                    idx = p.lower().find(ql)
                    start = max(0, idx - 90)
                    end = min(len(p), idx + 170)
                    snippet = ("…" if start > 0 else "") + p[start:end].strip() + ("…" if end < len(p) else "")
                hits.append(f"[{label} • ¶{i}] {snippet}")

    if not hits:
        return f"Find: no matches for '{q}'."
    cap = 24
    out = "\n".join(hits[:cap])
    if len(hits) > cap:
        out += f"\n\n(+{len(hits) - cap} more hits)"
    return out

# ============================================================
# PROMOTE IDEAS → CANON
# ============================================================
def story_bible_locked_for_edit() -> bool:
    """Hard lock: Story Bible is read-only unless explicitly unlocked per project."""
    return bool(st.session_state.project_id) and (not bool(st.session_state.locks.get("story_bible_edit_unlocked", False)))

def idea_lines_from_bank(bank_text: str) -> List[str]:
    lines_raw = [ln.strip() for ln in (bank_text or "").splitlines()]
    lines = [ln for ln in lines_raw if ln]
    seen = set()
    out = []
    for ln in lines:
        if ln in seen:
            continue
        seen.add(ln)
        out.append(ln)
    return out

def append_bullets(existing: str, bullets: List[str]) -> str:
    existing = (existing or "").rstrip()
    add_lines = [b.strip() for b in bullets if (b or "").strip()]
    if not add_lines:
        return existing

    low = existing.lower()
    filtered = []
    for b in add_lines:
        if b.lower() in low:
            continue
        filtered.append(b)
    if not filtered:
        return existing

    block = "\n".join([f"- {b}" if not b.startswith(("-", "•")) else b for b in filtered])
    if not existing:
        return block.strip()
    return (existing + "\n\n" + block).strip()

def promote_selected_ideas(target: str, selected: List[str], remove_from_ideas: bool) -> None:
    selected = [s.strip() for s in (selected or []) if s and s.strip()]
    if not selected:
        st.session_state.tool_output = "Promote: nothing selected."
        st.session_state.voice_status = "Promote: no selection"
        return

    # Hard lock: promoting into Story Bible requires explicit unlock per project
    if story_bible_locked_for_edit() and target in ("Synopsis", "Genre/Style Notes", "World", "Characters", "Outline"):
        st.session_state.tool_output = "Story Bible is LOCKED (read-only). Toggle \"Unlock Story Bible Editing\" to promote into canon."
        st.session_state.voice_status = "Story Bible locked"
        st.session_state.last_action = "Promote blocked"
        autosave()
        return

    if target == "Synopsis":
        st.session_state.synopsis = append_bullets(st.session_state.synopsis, selected)
    elif target == "Genre/Style Notes":
        st.session_state.genre_style_notes = append_bullets(st.session_state.genre_style_notes, selected)
    elif target == "World":
        st.session_state.world = append_bullets(st.session_state.world, selected)
    elif target == "Characters":
        st.session_state.characters = append_bullets(st.session_state.characters, selected)
    elif target == "Outline":
        st.session_state.outline = append_bullets(st.session_state.outline, selected)
    elif target == "Draft":
        note_block = "\n".join([f"[IDEA → DRAFT NOTE] {s}" for s in selected])
        base = (st.session_state.main_text or "").rstrip()
        st.session_state.main_text = (base + ("\n\n" if base else "") + note_block).strip()
    else:
        st.session_state.tool_output = f"Promote: unknown target '{target}'."
        st.session_state.voice_status = "Promote: error"
        return

    if remove_from_ideas:
        bank_lines = (st.session_state.junk or "").splitlines()
        to_remove = set(selected)
        new_bank = []
        for ln in bank_lines:
            if ln.strip() and ln.strip() in to_remove:
                continue
            new_bank.append(ln)
        st.session_state.junk = "\n".join(new_bank).strip()

    st.session_state.tool_output = f"Promoted {len(selected)} idea(s) → {target}."
    st.session_state.voice_status = f"Promoted → {target}"
    st.session_state.last_action = f"Promote → {target}"
    autosave()

# ============================================================
# IMPORT DOCUMENT → STORY BIBLE
# ============================================================
def read_uploaded_text(upload) -> Tuple[str, str]:
    if upload is None:
        return ("", "")
    name = getattr(upload, "name", "") or ""
    suffix = name.lower().split(".")[-1] if "." in name else ""

    data = upload.getvalue()
    if suffix in ("txt", "md"):
        try:
            return (data.decode("utf-8"), name)
        except Exception:
            return (data.decode("latin-1", errors="ignore"), name)

    if suffix == "docx":
        try:
            from docx import Document
            import io
            f = io.BytesIO(data)
            doc = Document(f)
            paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            return ("\n".join(paras).strip(), name)
        except Exception:
            return ("", name)

    return ("", name)

_HEADING_MAP = {
    "synopsis": "synopsis",
    "summary": "synopsis",
    "logline": "synopsis",
    "genre": "genre_style_notes",
    "style": "genre_style_notes",
    "tone": "genre_style_notes",
    "world": "world",
    "setting": "world",
    "locations": "world",
    "location": "world",
    "characters": "characters",
    "cast": "characters",
    "people": "characters",
    "outline": "outline",
    "plot": "outline",
    "beats": "outline",
    "structure": "outline",
}

def heuristic_breakdown(text: str) -> Dict[str, str]:
    t = normalize_text(text)
    out = {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""}
    if not t:
        return out

    lines = t.splitlines()
    current_key = None

    def detect_heading(line: str) -> Optional[str]:
        s = line.strip()
        if not s:
            return None
        s2 = re.sub(r"^#{1,6}\s*", "", s).strip()
        s2 = re.sub(r":\s*$", "", s2).strip()
        k = s2.lower()
        k = re.sub(r"[^a-z ]+", "", k).strip()
        if k in _HEADING_MAP:
            return _HEADING_MAP[k]
        return None

    for ln in lines:
        hk = detect_heading(ln)
        if hk:
            current_key = hk
            continue
        if current_key:
            out[current_key] += (ln + "\n")

    if not any(v.strip() for v in out.values()):
        out["synopsis"] = t[:1200].strip()
    else:
        for k in list(out.keys()):
            out[k] = normalize_text(out[k])

    return out

def merge_story_bible_fields(breakdown: Dict[str, str], merge_mode: str) -> None:
    merge_mode = merge_mode if merge_mode in IMPORT_MERGE_MODES else "Append"
    stamp = now_ts()
    prefix = f"--- IMPORT {stamp} ---\n"

    def apply_field(field_key: str, new_text: str):
        new_text = normalize_text(new_text)
        if not new_text:
            return
        current = getattr(st.session_state, field_key, "") or ""
        if merge_mode == "Replace" or not current.strip():
            setattr(st.session_state, field_key, new_text)
            return
        merged = (current.rstrip() + "\n\n" + prefix + new_text).strip()
        setattr(st.session_state, field_key, merged)

    apply_field("synopsis", breakdown.get("synopsis", ""))
    apply_field("genre_style_notes", breakdown.get("genre_style_notes", ""))
    apply_field("world", breakdown.get("world", ""))
    apply_field("characters", breakdown.get("characters", ""))
    apply_field("outline", breakdown.get("outline", ""))

def log_import(filename: str, chars: int, mode: str, used_ai: bool) -> None:
    entry = {"ts": now_ts(), "filename": filename or "(pasted)", "chars": int(chars), "mode": mode, "used_ai": bool(used_ai)}
    if st.session_state.project_id:
        p = st.session_state.projects.get(st.session_state.project_id, {})
        p.setdefault("imports_log", [])
        p["imports_log"].append(entry)
    else:
        w = st.session_state.workspace or default_workspace()
        w.setdefault("imports_log", [])
        w["imports_log"].append(entry)
        st.session_state.workspace = w

def ai_breakdown_to_story_bible(text: str, intensity_x: float) -> Dict[str, str]:
    system = (
        "You are Olivetti, a professional story-bible analyst.\n"
        "Return ONLY valid JSON (no markdown, no commentary).\n"
        "Keys required: synopsis, genre_style_notes, world, characters, outline\n"
        "Values must be plain text.\n"
        "Do not invent beyond what is implied. If unknown, leave empty string."
    )
    user = (
        "Break this document into Story Bible sections.\n"
        "Rules:\n"
        "- synopsis: what the story is about (tight, professional)\n"
        "- genre_style_notes: tone, genre signals, style constraints\n"
        "- world: setting, rules, locations, time period, key lore\n"
        "- characters: principal cast and roles\n"
        "- outline: major beats in order if present; otherwise empty\n"
        "Output JSON only."
    )
    out = call_openai(system, user, text, intensity_x)
    obj = safe_extract_json(out)
    return {
        "synopsis": normalize_text(str(obj.get("synopsis", ""))) if isinstance(obj, dict) else "",
        "genre_style_notes": normalize_text(str(obj.get("genre_style_notes", ""))) if isinstance(obj, dict) else "",
        "world": normalize_text(str(obj.get("world", ""))) if isinstance(obj, dict) else "",
        "characters": normalize_text(str(obj.get("characters", ""))) if isinstance(obj, dict) else "",
        "outline": normalize_text(str(obj.get("outline", ""))) if isinstance(obj, dict) else "",
    }

# ============================================================
# IDEA BANK COMMANDS
# ============================================================
CMD_FIND = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)

def next_bay(bay: str) -> Optional[str]:
    return {"NEW": "ROUGH", "ROUGH": "EDIT", "EDIT": "FINAL"}.get(bay)

def handle_idea_commands():
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return

    is_cmd = raw.startswith("/") and (CMD_FIND.match(raw) or CMD_CREATE.match(raw) or CMD_PROMOTE.match(raw))
    if not is_cmd:
        st.session_state.idea_bank_last = st.session_state.junk
        return

    cmd_raw = raw
    preserved = st.session_state.idea_bank_last or ""
    st.session_state.junk = preserved

    m = CMD_FIND.match(cmd_raw)
    if m:
        term = m.group(1).strip()
        st.session_state.tool_output = local_find(term)
        st.session_state.voice_status = f"Find: '{term}'"
        st.session_state.last_action = "Find"
        autosave()
        return

    m = CMD_CREATE.match(cmd_raw)
    if m:
        title = m.group(1).strip()
        # Creates a NEW project directly
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
        p["idea_bank"] = st.session_state.junk
        p["voice_bible"] = vb_struct_from_session()
        p["action_controls"] = action_controls_struct()
        p["import_controls"] = import_controls_from_session()
        p["voices"] = compact_voice_vault(st.session_state.voices)

        p["story_bible_locked_ts"] = now_ts()
        p["story_bible_lock_reason"] = "Created via /create"

        st.session_state.projects[p["id"]] = p
        st.session_state.active_project_by_bay["NEW"] = p["id"]
        switch_bay("NEW")
        load_project_into_session(p["id"])
        st.session_state.voice_status = f"Created in NEW: {st.session_state.project_title}"
        st.session_state.last_action = "Create Project"
        autosave()
        return

    if CMD_PROMOTE.match(cmd_raw):
        pid = st.session_state.project_id
        bay = st.session_state.active_bay
        nb = next_bay(bay)
        if not pid or not nb:
            st.session_state.tool_output = "Promote: no project selected, or already FINAL."
            st.session_state.voice_status = "Promote blocked."
            autosave()
            return
        save_session_into_project()
        promote_project(pid, nb)
        st.session_state.active_project_by_bay[nb] = pid
        switch_bay(nb)
        st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
        st.session_state.last_action = f"Promote → {nb}"
        autosave()
        return

handle_idea_commands()

# ============================================================
# PARTNER ACTIONS
# ============================================================
def partner_action(action: str):
    if not action_enabled(action):
        st.session_state.voice_status = f"{action}: disabled"
        st.session_state.tool_output = f"{action} is disabled in Action Controls for this context."
        autosave()
        return

    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    intensity_x = effective_intensity_for_action(action)
    brief = build_partner_brief(action, lane=lane, intensity_x=intensity_x)
    use_ai = bool(OPENAI_API_KEY)

    def apply_replace(result: str):
        if result and result.strip():
            st.session_state.main_text = result.strip()
            st.session_state.last_action = action
            autosave()

    def apply_append(result: str):
        if result and result.strip():
            base = (st.session_state.main_text or "").rstrip()
            st.session_state.main_text = (base + ("\n\n" if base else "") + result.strip()).strip()
            st.session_state.last_action = action
            autosave()

    try:
        if action == "Write":
            if use_ai:
                task = (
                    f"Continue decisively in lane ({lane}). Add 1–3 paragraphs that advance the scene. "
                    "Use Story Bible + Idea Bank when relevant. "
                    "No recap. No planning. Just prose."
                )
                out = call_openai(brief, task, text if text.strip() else "Start the opening.", intensity_x)
                apply_append(out)
            return

        if action == "Rewrite":
            if use_ai:
                task = f"Rewrite for professional quality in lane ({lane}). Preserve meaning and canon. Return full revised text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            else:
                apply_replace(local_cleanup(text))
            return

        if action == "Expand":
            if use_ai:
                task = f"Expand with meaningful depth in lane ({lane}). No padding. Preserve canon. Return full revised text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Rewrite the final paragraph for maximum strength (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = "Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text."
                out = call_openai(brief, task, cleaned, intensity_x)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
            return

        if action == "Synonym":
            if not use_ai:
                st.session_state.tool_output = "Synonym: requires OpenAI key."
                autosave()
                return
            task = "Provide 10 strong synonym options for the SINGLE most important verb in the final paragraph. Output bullet list only."
            out = call_openai(brief, task, text[-1200:] if text else "No text.", intensity_x)
            st.session_state.tool_output = out
            st.session_state.last_action = "Synonym"
            autosave()
            return

        if action == "Sentence":
            if not use_ai:
                st.session_state.tool_output = "Sentence: requires OpenAI key."
                autosave()
                return
            task = f"Generate 8 alternative sentences that could REPLACE the final sentence, same meaning, lane ({lane}). Return numbered list."
            out = call_openai(brief, task, text[-1200:] if text else "No text.", intensity_x)
            st.session_state.tool_output = out
            st.session_state.last_action = "Sentence"
            autosave()
            return

        if action == "Find":
            st.session_state.tool_output = "Use /find: term in Idea Bank (Junk Drawer)."
            st.session_state.last_action = "Find"
            autosave()
            return

    except Exception as e:
        st.session_state.voice_status = f"Engine: {e}"
        st.session_state.tool_output = f"ERROR:\n{e}"
        autosave()

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])

    if cols[0].button("🆕 New", key="bay_new"):
        switch_bay("NEW")
        save_all_to_disk(force=True)

    if cols[1].button("✏️ Rough", key="bay_rough"):
        switch_bay("ROUGH")
        save_all_to_disk(force=True)

    if cols[2].button("🛠 Edit", key="bay_edit"):
        switch_bay("EDIT")
        save_all_to_disk(force=True)

    if cols[3].button("✅ Final", key="bay_final"):
        switch_bay("FINAL")
        save_all_to_disk(force=True)

    cols[4].markdown(
        f"""
        <div style='text-align:right;font-size:12px;'>
            Bay: <b>{st.session_state.active_bay}</b>
            &nbsp;•&nbsp; Project: <b>{st.session_state.project_title}</b>
            &nbsp;•&nbsp; Autosave: {st.session_state.autosave_time or '—'}
            <br/>Last Action: {st.session_state.last_action}
            &nbsp;•&nbsp; Status: {st.session_state.voice_status}
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

    bay = st.session_state.active_bay
    bay_projects = list_projects_in_bay(bay)

    if bay == "NEW":
        labels = ["— (Story Bible workspace) —"] + [f"{title}" for _, title in bay_projects]
        ids = [None] + [pid for pid, _ in bay_projects]
    else:
        labels = ["— (none) —"] + [f"{title}" for _, title in bay_projects]
        ids = [None] + [pid for pid, _ in bay_projects]

    current_pid = st.session_state.project_id if (st.session_state.project_id in ids) else None
    current_idx = ids.index(current_pid) if current_pid in ids else 0

    sel = st.selectbox("Current Bay Project", labels, index=current_idx, key="bay_project_selector")
    sel_pid = ids[labels.index(sel)] if sel in labels else None

    if sel_pid != st.session_state.project_id:
        if in_workspace_mode():
            save_workspace_from_session()
        save_session_into_project()

        st.session_state.active_project_by_bay[bay] = sel_pid
        if sel_pid:
            load_project_into_session(sel_pid)
            st.session_state.voice_status = f"{bay}: {st.session_state.project_title}"
        else:
            st.session_state.project_id = None
            st.session_state.project_title = "—"
            if bay == "NEW":
                load_workspace_into_session()
                st.session_state.voice_status = "NEW: (Story Bible workspace)"
            else:
                st.session_state.main_text = ""
                st.session_state.synopsis = ""
                st.session_state.genre_style_notes = ""
                st.session_state.world = ""
                st.session_state.characters = ""
                st.session_state.outline = ""
                st.session_state.junk = ""
                st.session_state.idea_bank_last = ""
                st.session_state.tool_output = ""
                st.session_state.voice_status = f"{bay}: (empty)"
        st.session_state.last_action = "Select Context"
        autosave()

    action_cols = st.columns([1, 1])

    if bay == "NEW":
        if in_workspace_mode():
            st.text_input("Workspace Title", key="workspace_title", on_change=autosave)
            # keep desk alias in sync (avoids duplicate widget key)
            st.session_state.desk_workspace_title = st.session_state.workspace_title

        if action_cols[0].button("Start Project", key="start_project_btn", disabled=not in_workspace_mode()):
            start_project_from_workspace()
            autosave()

        if action_cols[1].button("Promote → Rough", key="promote_new_to_rough"):
            if st.session_state.project_id:
                save_session_into_project()
                promote_project(st.session_state.project_id, "ROUGH")
                st.session_state.active_project_by_bay["ROUGH"] = st.session_state.project_id
                switch_bay("ROUGH")
                st.session_state.voice_status = f"Promoted → ROUGH: {st.session_state.project_title}"
                st.session_state.last_action = "Promote → ROUGH"
                autosave()

    elif bay in ("ROUGH", "EDIT"):
        nb = next_bay(bay)
        if action_cols[1].button(f"Promote → {nb.title()}", key=f"promote_{bay.lower()}"):
            if st.session_state.project_id and nb:
                save_session_into_project()
                promote_project(st.session_state.project_id, nb)
                st.session_state.active_project_by_bay[nb] = st.session_state.project_id
                switch_bay(nb)
                st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
                st.session_state.last_action = f"Promote → {nb}"
                autosave()


    # Hard lock: Story Bible is read-only unless explicitly unlocked per project
    if st.session_state.project_id:
        # keep widget state synced to the project lock
        st.session_state.sb_unlock_toggle = bool(st.session_state.locks.get("story_bible_edit_unlocked", False))

        def _sb_unlock_changed():
            st.session_state.locks["story_bible_edit_unlocked"] = bool(st.session_state.sb_unlock_toggle)
            if st.session_state.sb_unlock_toggle:
                st.session_state.locks["story_bible_last_unlock_ts"] = now_ts()
            st.session_state.last_action = "Story Bible Unlock" if st.session_state.sb_unlock_toggle else "Story Bible Relock"
            autosave()

        st.checkbox(
            "Unlock Story Bible Editing",
            key="sb_unlock_toggle",
            on_change=_sb_unlock_changed,
            help="HARD LOCK (per project): OFF = read-only canon. ON = edits allowed.",
        )
        if not bool(st.session_state.locks.get("story_bible_edit_unlocked", False)):
            st.caption("🔒 Story Bible is locked (read-only). Toggle above to edit.")
    elif bay == "NEW":
        st.caption("Story Bible workspace is editable. It becomes locked to a project when you press Start Project.")

    st.slider(
        "AI Intensity (Global)",
        0.0, 1.0,
        key="ai_intensity",
        help="Global knob. Per-button overrides live in Action Controls (right panel).",
        on_change=autosave
    )

    with st.expander("📥 Import Document → Story Bible", expanded=False):
        st.caption("Paste or upload a document. Olivetti breaks it into Story Bible sections.")
        up = st.file_uploader("Upload (.txt, .md, .docx)", type=["txt", "md", "docx"], key="import_upload")
        st.text_area("Or paste document text", key="import_paste", height=140)

        st.checkbox("Use AI Breakdown (recommended)", key="import_use_ai", on_change=autosave)
        st.checkbox("Use Global Intensity", key="import_use_global", on_change=autosave)
        st.slider(
            "Import Intensity Override",
            0.0, 1.0,
            key="import_intensity",
            disabled=bool(st.session_state.import_use_global),
            help="Used only when Use Global Intensity is OFF.",
            on_change=autosave
        )
        st.selectbox("Merge Mode", IMPORT_MERGE_MODES, key="import_merge_mode", on_change=autosave)

        if st.button("Import → Break Down → Populate Story Bible", key="import_run", disabled=story_bible_locked_for_edit()):
            if story_bible_locked_for_edit():
                st.session_state.tool_output = "Import blocked: Story Bible is LOCKED (read-only). Toggle \"Unlock Story Bible Editing\" first."
                st.session_state.voice_status = "Story Bible locked"
                st.session_state.last_action = "Import blocked"
                autosave()
                st.stop()
            paste = (st.session_state.import_paste or "").strip()
            file_text, fname = read_uploaded_text(up)
            src_text = paste if paste else file_text
            filename = fname if fname else ("(pasted)" if paste else "")

            if not src_text.strip():
                st.session_state.tool_output = "Import: no text provided."
                st.session_state.voice_status = "Import blocked"
                autosave()
            else:
                used_ai = bool(st.session_state.import_use_ai) and bool(OPENAI_API_KEY)
                try:
                    b = ai_breakdown_to_story_bible(src_text, effective_import_intensity()) if used_ai else heuristic_breakdown(src_text)
                    merge_story_bible_fields(b, st.session_state.import_merge_mode)
                    log_import(filename, len(src_text), st.session_state.import_merge_mode, used_ai)

                    st.session_state.tool_output = (
                        f"Imported {len(src_text):,} chars from {filename}. "
                        f"Mode={st.session_state.import_merge_mode}. "
                        f"Breakdown={'AI' if used_ai else 'Heuristic'}."
                    )
                    st.session_state.voice_status = "Import complete"
                    st.session_state.last_action = "Import → Story Bible"
                    autosave()
                except Exception as e:
                    st.session_state.tool_output = f"Import ERROR:\n{e}"
                    st.session_state.voice_status = "Import error"
                    autosave()

    with st.expander("🧠 Idea Bank (Junk Drawer)"):
        st.text_area(
            "",
            key="junk",
            height=140,
            on_change=autosave,
            help="Idea pool for this context. Commands: /find: term  |  /create: Title  |  /promote"
        )

        ideas = idea_lines_from_bank(st.session_state.junk or "")
        if ideas:
            st.caption("Promote selected idea lines into canon fields (one-click).")
            st.multiselect("Select idea line(s)", options=ideas, key="promote_selected")
            colsP = st.columns([1.2, 1.2, 1.6])
            colsP[0].selectbox("Target", ["Synopsis", "Genre/Style Notes", "World", "Characters", "Outline", "Draft"], key="promote_target")
            colsP[1].checkbox("Remove from Idea Bank", key="promote_remove_from_ideas", help="OFF by default.")
            if colsP[2].button("Promote Selected → Target", key="btn_promote_selected"):
                promote_selected_ideas(st.session_state.promote_target, st.session_state.promote_selected, bool(st.session_state.promote_remove_from_ideas))
        else:
            st.caption("Add idea lines above to enable Promote → Canon.")

        st.text_area("Tool Output", key="tool_output", height=160, disabled=True)

    with st.expander("📝 Synopsis"):
        st.text_area("", key="synopsis", height=100, on_change=autosave, disabled=story_bible_locked_for_edit())

    with st.expander("🎭 Genre / Style Notes"):
        st.text_area("", key="genre_style_notes", height=80, on_change=autosave, disabled=story_bible_locked_for_edit())

    with st.expander("🌍 World Elements"):
        st.text_area("", key="world", height=100, on_change=autosave, disabled=story_bible_locked_for_edit())

    with st.expander("👤 Characters"):
        st.text_area("", key="characters", height=120, on_change=autosave, disabled=story_bible_locked_for_edit())

    with st.expander("🧱 Outline"):
        st.text_area("", key="outline", height=160, on_change=autosave, disabled=story_bible_locked_for_edit())

# ============================================================
# CENTER — WRITING DESK
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    if st.session_state.project_id:
        p = st.session_state.projects.get(st.session_state.project_id, {}) or {}
        sbid = p.get("story_bible_id", "—")
        sbts = p.get("story_bible_created_ts", "—")
        lock_ts = p.get("story_bible_locked_ts", "—") or "—"
        st.caption(f"Linked To: **{st.session_state.active_bay} / {st.session_state.project_title}** • Story Bible ID: **{sbid}** • Created: **{sbts}** • Locked: **{lock_ts}**")
    else:
        st.caption("Linked To: **NEW / Story Bible workspace** (not yet a project)")

    with st.expander("📌 Story Bible Dock (read-only while you write)", expanded=False):
        tabs = st.tabs(["Synopsis", "Genre/Style", "World", "Characters", "Outline"])
        with tabs[0]:
            st.text_area("Synopsis (Canon)", value=st.session_state.synopsis or "", height=160, disabled=True)
        with tabs[1]:
            st.text_area("Genre/Style Notes (Canon)", value=st.session_state.genre_style_notes or "", height=160, disabled=True)
        with tabs[2]:
            st.text_area("World (Canon)", value=st.session_state.world or "", height=160, disabled=True)
        with tabs[3]:
            st.text_area("Characters (Canon)", value=st.session_state.characters or "", height=160, disabled=True)
        with tabs[4]:
            st.text_area("Outline (Canon)", value=st.session_state.outline or "", height=160, disabled=True)

        st.divider()
        st.caption("Optional: Insert canon into the draft as a note block (append).")
        st.selectbox("Insert Section", ["Synopsis", "Genre/Style Notes", "World", "Characters", "Outline"], key="desk_insert_section")
        if st.button("Insert Section → Draft (as note)", key="desk_insert_btn"):
            sec = st.session_state.desk_insert_section
            content = ""
            if sec == "Synopsis":
                content = st.session_state.synopsis or ""
            elif sec == "Genre/Style Notes":
                content = st.session_state.genre_style_notes or ""
            elif sec == "World":
                content = st.session_state.world or ""
            elif sec == "Characters":
                content = st.session_state.characters or ""
            elif sec == "Outline":
                content = st.session_state.outline or ""
            content = normalize_text(content)
            if content:
                note = f"[STORY BIBLE → {sec}]\n{content}"
                base = (st.session_state.main_text or "").rstrip()
                st.session_state.main_text = (base + ("\n\n" if base else "") + note).strip()
                st.session_state.voice_status = f"Inserted Story Bible → {sec}"
                st.session_state.last_action = f"Insert SB → {sec}"
                autosave()

    with st.expander("⚙ Project Controls (from the desk)", expanded=False):
        # FIX: unique widget key (desk_workspace_title) synced to workspace_title
        def _desk_title_sync():
            st.session_state.workspace_title = st.session_state.desk_workspace_title
            autosave()

        if in_workspace_mode():
            st.caption("You are in the Story Bible workspace. Start a project without leaving the desk.")
            st.session_state.desk_workspace_title = st.session_state.workspace_title
            st.text_input("Project Title", key="desk_workspace_title", on_change=_desk_title_sync)
            if st.button("Start Project NOW (from workspace)", key="desk_start_project_now"):
                start_project_from_workspace()
                autosave()
        else:
            st.caption("Create another NEW project without leaving the desk.")

        st.text_input("New Project Title", key="desk_new_project_title")
        c1, c2, c3 = st.columns(3)
        c1.checkbox("Copy Story Bible", key="desk_copy_story_bible", help="Copies current Story Bible into the new project.")
        c2.checkbox("Copy Draft", key="desk_copy_draft", help="Copies current draft text into the new project.")
        c3.checkbox("Copy Idea Bank", key="desk_copy_idea_bank", help="Copies current Idea Bank into the new project.")

        if st.button("Create New Project (Desk Shortcut)", key="desk_create_project_btn"):
            desk_create_new_project(
                st.session_state.desk_new_project_title,
                bool(st.session_state.desk_copy_story_bible),
                bool(st.session_state.desk_copy_draft),
                bool(st.session_state.desk_copy_idea_bank),
            )
            autosave()

    st.text_area("", key="main_text", height=650, on_change=autosave)

    b1 = st.columns(5)
    if b1[0].button("Write", key="btn_write"): partner_action("Write")
    if b1[1].button("Rewrite", key="btn_rewrite"): partner_action("Rewrite")
    if b1[2].button("Expand", key="btn_expand"): partner_action("Expand")
    if b1[3].button("Rephrase", key="btn_rephrase"): partner_action("Rephrase")
    if b1[4].button("Describe", key="btn_describe"): partner_action("Describe")

    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell"): partner_action("Spell")
    if b2[1].button("Grammar", key="btn_grammar"): partner_action("Grammar")
    if b2[2].button("Find", key="btn_find"): partner_action("Find")
    if b2[3].button("Synonym", key="btn_synonym"): partner_action("Synonym")
    if b2[4].button("Sentence", key="btn_sentence"): partner_action("Sentence")

# ============================================================
# RIGHT — VOICE BIBLE + ACTION CONTROLS
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    st.checkbox("Enable Writing Style", key="vb_style_on", on_change=autosave)
    st.selectbox(
        "Writing Style",
        ["Neutral", "Minimal", "Expressive", "Hardboiled", "Poetic"],
        key="writing_style",
        disabled=not st.session_state.vb_style_on,
        on_change=autosave
    )
    st.slider("Style Intensity", 0.0, 1.0, key="style_intensity", disabled=not st.session_state.vb_style_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Genre Influence", key="vb_genre_on", on_change=autosave)
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on,
        on_change=autosave
    )
    st.slider("Genre Intensity", 0.0, 1.0, key="genre_intensity", disabled=not st.session_state.vb_genre_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Trained Voice", key="vb_trained_on", on_change=autosave)
    trained_options = voice_names_for_selector()
    if st.session_state.trained_voice not in trained_options:
        st.session_state.trained_voice = "— None —"
    st.selectbox("Trained Voice", trained_options, key="trained_voice", disabled=not st.session_state.vb_trained_on, on_change=autosave)
    st.slider("Trained Voice Intensity", 0.0, 1.0, key="trained_intensity", disabled=not st.session_state.vb_trained_on, on_change=autosave)

    st.divider()


    with st.expander("🌐 Global Voice (trainable)", expanded=False):
        st.checkbox("Enable Global Voice", key="global_voice_on", on_change=autosave)
        gv_profiles = ["— None —"] + [global_label(n) for n in global_voice_names_for_selector()]
        if st.session_state.global_voice not in gv_profiles:
            st.session_state.global_voice = gv_profiles[1] if len(gv_profiles) > 1 else "— None —"
        st.selectbox("Global Voice Profile", gv_profiles, key="global_voice", disabled=not st.session_state.global_voice_on, on_change=autosave)
        st.slider("Global Voice Strength", 0.0, 1.0, key="global_voice_strength", disabled=not st.session_state.global_voice_on, on_change=autosave)

        st.divider()

        colA, colB = st.columns([3, 1])
        with colA:
            st.text_input("New Global Voice Name", key="gv_new_name")
        with colB:
            if st.button("Create", key="gv_create_btn"):
                nm = (st.session_state.get("gv_new_name") or "").strip()
                if nm:
                    st.session_state.global_voices.setdefault(nm, {"created_ts": now_ts(), "lanes": {ln: [] for ln in LANES}})
                    st.session_state.global_voice = global_label(nm)
                    st.session_state.gv_new_name = ""
                    st.session_state.voice_status = f"Created global voice: {nm}"
                    autosave()

        # Training input
        up = st.file_uploader("Upload training text (.txt/.md/.docx)", type=["txt", "md", "docx"], key="gv_train_upload")
        st.text_area("…or paste training text", key="gv_train_paste", height=140)

        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Auto-lane paragraphs", key="gv_auto_lane", value=True)
            st.number_input("Max paragraphs to add", 1, 200, value=60, key="gv_max_samples")
        with col2:
            st.selectbox("Forced lane (if auto-lane off)", LANES, key="gv_forced_lane", disabled=st.session_state.get("gv_auto_lane", True))
            st.number_input("Min words per paragraph", 1, 50, value=8, key="gv_min_words")

        if st.button("Train Global Voice NOW", key="gv_train_btn"):
            raw = read_uploaded_text(up) if up is not None else ""
            raw = raw if raw.strip() else (st.session_state.get("gv_train_paste") or "")
            target = st.session_state.global_voice
            target_name = global_unlabel(target) if is_global_voice(target) else (target or "Global Voice")
            if target_name == "— None —":
                target_name = "Global Voice"
                st.session_state.global_voice = global_label("Global Voice")
            added = add_voice_samples(
                st.session_state.global_voices,
                target_name,
                raw,
                auto_lane=bool(st.session_state.get("gv_auto_lane", True)),
                forced_lane=st.session_state.get("gv_forced_lane", "Narration"),
                max_samples=int(st.session_state.get("gv_max_samples", 60)),
                min_words=int(st.session_state.get("gv_min_words", 8)),
            )
            if added > 0:
                st.session_state.voice_status = f"Trained {target_name}: +{added} samples"
                autosave()
                st.success(f"Added {added} paragraphs into {target_name}.")
            else:
                st.warning("Nothing added. Paste/upload text first (and ensure paragraphs are long enough).")

        # Quick stats + maintenance
        sel = global_unlabel(st.session_state.global_voice) if is_global_voice(st.session_state.global_voice) else "Global Voice"
        v = (st.session_state.global_voices or {}).get(sel)
        if v:
            counts = {ln: len((v.get("lanes", {}) or {}).get(ln, []) or []) for ln in LANES}
            st.caption("Lane counts: " + " • ".join([f"{ln}: {counts[ln]}" for ln in LANES]))
            colX, colY = st.columns(2)
            with colX:
                if st.button("Clear last 50 (all lanes)", key="gv_clear50"):
                    for ln in LANES:
                        v["lanes"][ln] = (v["lanes"].get(ln, []) or [])[:-50]
                    st.session_state.voice_status = f"Cleared last 50 samples from {sel}"
                    autosave()
            with colY:
                if st.button("Wipe this voice (DANGER)", key="gv_wipe_voice"):
                    for ln in LANES:
                        v["lanes"][ln] = []
                    st.session_state.voice_status = f"Wiped global voice: {sel}"
                    autosave()


    st.checkbox("Enable Match My Style", key="vb_match_on", on_change=autosave)
    st.text_area("Style Example", key="voice_sample", height=100, disabled=not st.session_state.vb_match_on, on_change=autosave)
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity", disabled=not st.session_state.vb_match_on, on_change=autosave)

    st.divider()

    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on", on_change=autosave)
    st.text_area("Voice Lock Prompt", key="voice_lock_prompt", height=80, disabled=not st.session_state.vb_lock_on, on_change=autosave)
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity", disabled=not st.session_state.vb_lock_on, on_change=autosave)

    st.divider()

    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov", on_change=autosave)
    st.selectbox("Tense", ["Past", "Present"], key="tense", on_change=autosave)

    st.divider()

    with st.expander("🧰 Action Controls (Per Button)"):
        locked = st.checkbox(
            "Lock Action Controls (this context)",
            key="ac_locked",
            help="When locked, you can still run buttons, but settings cannot be edited.",
            on_change=autosave,
        )

        def disabled() -> bool:
            return bool(locked)

        st.caption("Each button has: Enable + Use Global Intensity + Override Intensity (when enabled).")

        st.markdown("**Primary Buttons**")
        for a in ACTIONS_PRIMARY:
            cols = st.columns([1.2, 1.0, 1.6])
            cols[0].checkbox(f"{a} Enabled", key=ac_key(a, "enabled"), disabled=disabled(), on_change=autosave)
            cols[1].checkbox("Use Global", key=ac_key(a, "use_global"), disabled=disabled(), on_change=autosave)
            cols[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=ac_key(a, "intensity"),
                disabled=disabled() or bool(st.session_state.get(ac_key(a, "use_global"), True)),
                help="Used only when Use Global is OFF.",
                on_change=autosave
            )

        st.markdown("**Secondary Buttons**")
        for a in ACTIONS_SECONDARY:
            cols = st.columns([1.2, 1.0, 1.6])
            cols[0].checkbox(f"{a} Enabled", key=ac_key(a, "enabled"), disabled=disabled(), on_change=autosave)
            cols[1].checkbox("Use Global", key=ac_key(a, "use_global"), disabled=disabled(), on_change=autosave)
            cols[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=ac_key(a, "intensity"),
                disabled=disabled() or bool(st.session_state.get(ac_key(a, "use_global"), True)),
                help="Used only when Use Global is OFF.",
                on_change=autosave
            )

# ============================================================
# FINAL SAFETY NET SAVE
# ============================================================
save_all_to_disk()
