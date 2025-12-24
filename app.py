import os
import re
import math
import json
import hashlib
import streamlit as st
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

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
st.set_page_config(page_title="Olivetti Desk", layout="wide", initial_sidebar_state="expanded")

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
# GLOBALS
# ============================================================
LANES = ["Dialogue", "Narration", "Interiority", "Action"]
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]  # work bays

ACTIONS_PRIMARY = ["Write", "Rewrite", "Expand", "Rephrase", "Describe"]
ACTIONS_SECONDARY = ["Spell", "Grammar", "Find", "Synonym", "Sentence"]
ALL_ACTIONS = ACTIONS_PRIMARY + ACTIONS_SECONDARY

AUTOSAVE_DIR = "autosave"
AUTOSAVE_PATH = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")

WORD_RE = re.compile(r"[A-Za-z']+")

# ============================================================
# UTILS
# ============================================================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

def _first_nonempty_line(s: str) -> str:
    for line in (s or "").splitlines():
        if line.strip():
            return line.strip()
    return ""

def clamp01(x: float) -> float:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    return max(0.0, min(1.0, v))

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
    has_dialogue_punct = (p.startswith("—") or p.startswith("- ") or p.startswith("“") or p.startswith('"'))

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
    return "MAX: aggressive originality and voice; still obey canon, no random derailments."

def temperature_from_intensity(x: float) -> float:
    x = clamp01(x)
    return 0.15 + (x * 0.95)  # 0.0 -> 0.15, 1.0 -> 1.10

# ============================================================
# ACTION CONTROLS (per-button: on/off + intensity override + project lock)
# ============================================================
def default_action_controls() -> Dict[str, Any]:
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {"enabled": True, "use_global": True, "intensity": 0.75}
    return {"locked": False, "items": items}

def _ac_key(action: str, field: str) -> str:
    return f"ac__{action}__{field}"

def init_action_control_scalars_from_struct(ac: Dict[str, Any]) -> None:
    ac = ac or default_action_controls()
    st.session_state.ac_locked = bool(ac.get("locked", False))
    items = ac.get("items", {}) or {}
    for a in ALL_ACTIONS:
        it = items.get(a, {}) or {}
        st.session_state[_ac_key(a, "enabled")] = bool(it.get("enabled", True))
        st.session_state[_ac_key(a, "use_global")] = bool(it.get("use_global", True))
        st.session_state[_ac_key(a, "intensity")] = clamp01(it.get("intensity", 0.75))

def action_controls_struct_from_scalars() -> Dict[str, Any]:
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {
            "enabled": bool(st.session_state.get(_ac_key(a, "enabled"), True)),
            "use_global": bool(st.session_state.get(_ac_key(a, "use_global"), True)),
            "intensity": clamp01(st.session_state.get(_ac_key(a, "intensity"), 0.75)),
        }
    return {"locked": bool(st.session_state.get("ac_locked", False)), "items": items}

def effective_intensity_for_action(action: str) -> float:
    global_x = clamp01(st.session_state.get("ai_intensity", 0.75))
    use_global = bool(st.session_state.get(_ac_key(action, "use_global"), True))
    if use_global:
        return global_x
    return clamp01(st.session_state.get(_ac_key(action, "intensity"), global_x))

def action_is_enabled(action: str) -> bool:
    return bool(st.session_state.get(_ac_key(action, "enabled"), True))

# ============================================================
# PROJECT MODEL
# ============================================================
def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
        "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
    }

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
        # Story Bible is per-project and travels with the project forever
        "story_bible_id": hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12],
        "story_bible_created_ts": ts,
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        # Junk Drawer = Idea Bank (per project)
        "idea_bank": "",
        # Voice Bible persists per project
        "voice_bible": default_voice_bible(),
        # Per-button controls (new)
        "action_controls": default_action_controls(),
        "locks": {
            "story_bible_lock": True,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },
        "voices": default_voice_vault(),
    }

# ============================================================
# STORY BIBLE WORKSPACE (pre-project creation space)
# ============================================================
def default_workspace() -> Dict[str, Any]:
    return {
        "title": "",
        "draft": "",
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        "idea_bank": "",
        "voice_bible": default_voice_bible(),
        "action_controls": default_action_controls(),
    }

# ============================================================
# SESSION INIT
# ============================================================
def init_state():
    defaults = {
        "active_bay": "NEW",
        "projects": {},
        "active_project_by_bay": {b: None for b in BAYS},

        "project_id": None,
        "project_title": "—",
        "autosave_time": None,
        "last_action": "—",
        "voice_status": "—",

        # Editor fields
        "main_text": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",

        # Junk Drawer = Idea Bank
        "junk": "",
        "idea_bank_last": "",

        "tool_output": "",

        "workspace": default_workspace(),
        "workspace_title": "",

        # Voice Bible controls (flat scalars)
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

        "locks": {
            "story_bible_lock": True,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },

        "voices": {},
        "voices_seeded": False,

        # Action controls scalars
        "ac_locked": False,

        "last_saved_digest": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Ensure action control scalars exist
    for a in ALL_ACTIONS:
        st.session_state.setdefault(_ac_key(a, "enabled"), True)
        st.session_state.setdefault(_ac_key(a, "use_global"), True)
        st.session_state.setdefault(_ac_key(a, "intensity"), 0.75)

init_state()

# ============================================================
# MODE HELPERS
# ============================================================
def in_workspace_mode() -> bool:
    return st.session_state.active_bay == "NEW" and not st.session_state.project_id

# ============================================================
# WORKSPACE <-> SESSION SYNC
# ============================================================
def _vb_struct_from_session() -> Dict[str, Any]:
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

def _vb_apply_to_session(vb: Dict[str, Any]) -> None:
    vb = vb or default_voice_bible()
    for k, v in vb.items():
        if k in st.session_state:
            st.session_state[k] = v

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
    w["voice_bible"] = _vb_struct_from_session()
    w["action_controls"] = action_controls_struct_from_scalars()
    st.session_state.workspace = w

def load_workspace_into_session() -> None:
    w = st.session_state.workspace or default_workspace()
    sb = (w.get("story_bible", {}) or {})
    st.session_state.workspace_title = w.get("title", "") or ""
    st.session_state.main_text = w.get("draft", "") or ""
    st.session_state.synopsis = sb.get("synopsis", "") or ""
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "") or ""
    st.session_state.world = sb.get("world", "") or ""
    st.session_state.characters = sb.get("characters", "") or ""
    st.session_state.outline = sb.get("outline", "") or ""
    st.session_state.junk = w.get("idea_bank", "") or ""
    st.session_state.idea_bank_last = st.session_state.junk
    _vb_apply_to_session(w.get("voice_bible", default_voice_bible()))
    init_action_control_scalars_from_struct(w.get("action_controls", default_action_controls()))

def reset_workspace_content(keep_templates: bool = True) -> None:
    w = st.session_state.workspace or default_workspace()
    vb = w.get("voice_bible", default_voice_bible())
    ac = w.get("action_controls", default_action_controls())
    st.session_state.workspace = default_workspace()
    if keep_templates:
        st.session_state.workspace["voice_bible"] = vb
        st.session_state.workspace["action_controls"] = ac
    st.session_state.workspace_title = ""
    if in_workspace_mode():
        load_workspace_into_session()

# ============================================================
# PROJECT <-> SESSION SYNC
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
            lanes_out[ln] = [{"ts": s.get("ts"), "text": s.get("text", "")} for s in samples if s.get("text")]
        out[vname] = {"created_ts": v.get("created_ts"), "lanes": lanes_out}
    return out

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

    vb = p.get("voice_bible", {}) or default_voice_bible()
    _vb_apply_to_session(vb)

    locks = p.get("locks", {}) or {}
    if isinstance(locks, dict):
        st.session_state.locks = locks

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True

    init_action_control_scalars_from_struct(p.get("action_controls", default_action_controls()))

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
    p["voice_bible"] = _vb_struct_from_session()
    p["action_controls"] = action_controls_struct_from_scalars()
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
        title = _first_nonempty_line(st.session_state.synopsis) or f"New Project {now_ts()}"

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
    p["voice_bible"] = _vb_struct_from_session()
    p["action_controls"] = action_controls_struct_from_scalars()
    p["voices"] = compact_voice_vault(st.session_state.voices)

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    load_project_into_session(p["id"])
    st.session_state.voice_status = f"Started Project in NEW: {st.session_state.project_title}"
    st.session_state.last_action = "Start Project"

    reset_workspace_content(keep_templates=True)

    return p["id"]

# ============================================================
# AUTOSAVE ALL
# ============================================================
def _payload() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-action-controls-v1"},
        "workspace": st.session_state.workspace,
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "projects": st.session_state.projects,
    }

def _digest(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def save_all_to_disk(force: bool = False) -> None:
    try:
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        payload = _payload()
        dig = _digest(payload)
        if (not force) and dig == st.session_state.last_saved_digest:
            return
        with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        st.session_state.last_saved_digest = dig
    except Exception as e:
        st.session_state.voice_status = f"Autosave warning: {e}"

def load_all_from_disk() -> None:
    if not os.path.exists(AUTOSAVE_PATH):
        switch_bay("NEW")
        return
    try:
        with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        ws = payload.get("workspace")
        if isinstance(ws, dict):
            st.session_state.workspace = ws
            st.session_state.workspace_title = ws.get("title", "") or ""

        projs = payload.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = payload.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            for b in BAYS:
                apbb.setdefault(b, None)
            st.session_state.active_project_by_bay = apbb

        ab = payload.get("active_bay", "NEW")
        if ab not in BAYS:
            ab = "NEW"
        st.session_state.active_bay = ab

        ensure_bay_has_active_project(ab)
        pid = st.session_state.active_project_by_bay.get(ab)
        if pid:
            load_project_into_session(pid)
        else:
            switch_bay(ab)

        st.session_state.voice_status = f"Loaded autosave ({payload.get('meta', {}).get('saved_at','')})."
        st.session_state.last_saved_digest = _digest(_payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"
        switch_bay("NEW")

if "did_load_autosave" not in st.session_state:
    st.session_state.did_load_autosave = True
    load_all_from_disk()

def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    save_all_to_disk()

# ============================================================
# VOICE VAULT OPS
# ============================================================
def seed_default_voices():
    if st.session_state.voices_seeded:
        return
    st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
    st.session_state.voices_seeded = True

seed_default_voices()

def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in st.session_state.voices.keys() if k not in ("Voice A", "Voice B")])
    return base + customs

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
    return [txt for score, txt in scored[:k] if score > 0.0 and txt][:k]

def retrieve_mixed_exemplars(voice_name: str, lane: str, query_text: str) -> List[str]:
    lane_ex = retrieve_exemplars(voice_name, lane, query_text, k=2)
    if lane == "Narration":
        return lane_ex if lane_ex else retrieve_exemplars(voice_name, "Narration", query_text, k=3)
    nar_ex = retrieve_exemplars(voice_name, "Narration", query_text, k=1)
    out = lane_ex + [x for x in nar_ex if x not in lane_ex]
    return out[:3]

# ============================================================
# AI BRIEF
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

def build_partner_brief(action_name: str, lane: str, intensity_x: float) -> str:
    story_bible = _story_bible_text()
    idea_bank = (st.session_state.junk or "").strip() or "— None —"

    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {float(st.session_state.style_intensity):.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {float(st.session_state.genre_intensity):.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
        vb.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {float(st.session_state.trained_intensity):.2f})")
    if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
        vb.append(f"Match Sample (intensity {float(st.session_state.match_intensity):.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and (st.session_state.voice_lock_prompt or "").strip():
        vb.append(f"VOICE LOCK (strength {float(st.session_state.lock_intensity):.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)
    ex_block = "\n\n---\n\n".join(exemplars) if exemplars else "— None —"

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

TRAINED EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE:
{story_bible}

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
            {"role": "user", "content": f"{user_task}\n\nDRAFT:\n{text.strip()}"},
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
        paras = _split_paragraphs(txt)
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
# COMMANDS (Idea Bank)
# ============================================================
CMD_FIND = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)

def next_bay(bay: str) -> Optional[str]:
    if bay == "NEW":
        return "ROUGH"
    if bay == "ROUGH":
        return "EDIT"
    if bay == "EDIT":
        return "FINAL"
    return None

def handle_idea_commands():
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return

    is_cmd = raw.startswith("/") and (CMD_CREATE.match(raw) or CMD_PROMOTE.match(raw) or CMD_FIND.match(raw))
    if not is_cmd:
        st.session_state.idea_bank_last = st.session_state.junk
        return

    cmd_raw = raw
    preserved = st.session_state.idea_bank_last or ""
    st.session_state.junk = preserved  # restore ideas immediately

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
        if in_workspace_mode():
            st.session_state.workspace_title = title
            start_project_from_workspace()
        else:
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
            p["voice_bible"] = _vb_struct_from_session()
            p["action_controls"] = action_controls_struct_from_scalars()
            p["voices"] = compact_voice_vault(st.session_state.voices)
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
    if not action_is_enabled(action):
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
            if (st.session_state.main_text or "").strip():
                st.session_state.main_text = (st.session_state.main_text.rstrip() + "\n\n" + result.strip()).strip()
            else:
                st.session_state.main_text = result.strip()
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
            else:
                apply_replace(text)
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
            else:
                apply_replace(text)
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Rewrite the final paragraph for maximum strength (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text, intensity_x)
                apply_replace(out)
            else:
                apply_replace(text)
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
            task = (
                "Provide 10 strong synonym options for the SINGLE most important verb in the final paragraph. "
                "Output as a clean bullet list only."
            )
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
            task = (
                f"Generate 8 alternative sentences that could REPLACE the final sentence, same meaning, lane ({lane}). "
                "Return as numbered list."
            )
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

        apply_replace(text)

    except Exception as e:
        st.session_state.voice_status = f"Engine: {e}"
        st.session_state.tool_output = f"ERROR:\n{e}"
        autosave()

# ============================================================
# TOP BAR (work bays)
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
# LOCKED LAYOUT (same ratios)
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE (creation space + linked per project)
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

        if action_cols[0].button("Start Project", key="start_project_btn", disabled=not in_workspace_mode()):
            start_project_from_workspace()
            autosave()

        if action_cols[0].button("Create Project (from Bible)", key="create_project_btn"):
            if in_workspace_mode():
                start_project_from_workspace()
            else:
                title_guess = _first_nonempty_line(st.session_state.synopsis) or "New Project"
                p = new_project_payload(title_guess)
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
                p["voice_bible"] = _vb_struct_from_session()
                p["action_controls"] = action_controls_struct_from_scalars()
                p["voices"] = compact_voice_vault(st.session_state.voices)
                st.session_state.projects[p["id"]] = p
                st.session_state.active_project_by_bay["NEW"] = p["id"]
                load_project_into_session(p["id"])
                st.session_state.voice_status = f"Created in NEW: {st.session_state.project_title}"
                st.session_state.last_action = "Create Project"
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

    st.slider(
        "AI Intensity (Global)",
        0.0, 1.0,
        key="ai_intensity",
        help="Global knob. Per-button overrides live in Action Controls (right panel).",
        on_change=autosave
    )

    with st.expander("🧠 Idea Bank (Junk Drawer)"):
        st.text_area(
            "",
            key="junk",
            height=140,
            on_change=autosave,
            help="Idea pool for this context. Commands: /find: term  |  /create: Title  |  /promote"
        )
        st.text_area("Tool Output", key="tool_output", height=160, disabled=True)

    with st.expander("📝 Synopsis"):
        st.text_area("", key="synopsis", height=100, on_change=autosave)

    with st.expander("🎭 Genre / Style Notes"):
        st.text_area("", key="genre_style_notes", height=80, on_change=autosave)

    with st.expander("🌍 World Elements"):
        st.text_area("", key="world", height=100, on_change=autosave)

    with st.expander("👤 Characters"):
        st.text_area("", key="characters", height=120, on_change=autosave)

    with st.expander("🧱 Outline"):
        st.text_area("", key="outline", height=160, on_change=autosave)

# ============================================================
# CENTER — WRITING DESK
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")
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
    st.slider(
        "Style Intensity", 0.0, 1.0,
        key="style_intensity",
        disabled=not st.session_state.vb_style_on,
        on_change=autosave
    )

    st.divider()

    st.checkbox("Enable Genre Influence", key="vb_genre_on", on_change=autosave)
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on,
        on_change=autosave
    )
    st.slider(
        "Genre Intensity", 0.0, 1.0,
        key="genre_intensity",
        disabled=not st.session_state.vb_genre_on,
        on_change=autosave
    )

    st.divider()

    st.checkbox("Enable Trained Voice", key="vb_trained_on", on_change=autosave)
    trained_options = voice_names_for_selector()
    if st.session_state.trained_voice not in trained_options:
        st.session_state.trained_voice = "— None —"
    st.selectbox(
        "Trained Voice",
        trained_options,
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on,
        on_change=autosave
    )
    st.slider(
        "Trained Voice Intensity", 0.0, 1.0,
        key="trained_intensity",
        disabled=not st.session_state.vb_trained_on,
        on_change=autosave
    )

    st.divider()

    st.checkbox("Enable Match My Style", key="vb_match_on", on_change=autosave)
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on,
        on_change=autosave
    )
    st.slider(
        "Match Intensity", 0.0, 1.0,
        key="match_intensity",
        disabled=not st.session_state.vb_match_on,
        on_change=autosave
    )

    st.divider()

    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on", on_change=autosave)
    st.text_area(
        "Voice Lock Prompt",
        key="voice_lock_prompt",
        height=80,
        disabled=not st.session_state.vb_lock_on,
        on_change=autosave
    )
    st.slider(
        "Lock Strength", 0.0, 1.0,
        key="lock_intensity",
        disabled=not st.session_state.vb_lock_on,
        on_change=autosave
    )

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

        def _disabled() -> bool:
            return bool(locked)

        st.caption("Each button has: Enable + Use Global Intensity + Override Intensity (when enabled).")

        st.markdown("**Primary Buttons**")
        for a in ACTIONS_PRIMARY:
            cols = st.columns([1.2, 1.0, 1.6])
            cols[0].checkbox(
                f"{a} Enabled",
                key=_ac_key(a, "enabled"),
                disabled=_disabled(),
                on_change=autosave
            )
            cols[1].checkbox(
                "Use Global",
                key=_ac_key(a, "use_global"),
                disabled=_disabled(),
                on_change=autosave
            )
            cols[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=_ac_key(a, "intensity"),
                disabled=_disabled() or bool(st.session_state.get(_ac_key(a, "use_global"), True)),
                help="Used only when Use Global is OFF.",
                on_change=autosave
            )

        st.markdown("**Secondary Buttons**")
        for a in ACTIONS_SECONDARY:
            cols = st.columns([1.2, 1.0, 1.6])
            cols[0].checkbox(
                f"{a} Enabled",
                key=_ac_key(a, "enabled"),
                disabled=_disabled(),
                on_change=autosave
            )
            cols[1].checkbox(
                "Use Global",
                key=_ac_key(a, "use_global"),
                disabled=_disabled(),
                on_change=autosave
            )
            cols[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=_ac_key(a, "intensity"),
                disabled=_disabled() or bool(st.session_state.get(_ac_key(a, "use_global"), True)),
                help="Used only when Use Global is OFF.",
                on_change=autosave
            )

# ============================================================
# SAFETY NET SAVE EVERY RERUN
# ============================================================
save_all_to_disk()
