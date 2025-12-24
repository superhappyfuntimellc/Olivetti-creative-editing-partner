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
    if quote_count >= 2: dialogue_score += 2.5
    if has_dialogue_punct: dialogue_score += 1.5

    toks = _tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i","me","my","mine","myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1: interior_score += 2.2

    action_score = 0.0
    if toks:
        verb_hits = sum(1 for t in toks if t in ACTION_VERBS)
        if verb_hits >= 2: action_score += 1.6
        if "!" in p: action_score += 0.3

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
# NOTE: UI lives in STORY BIBLE panel, but affects ALL generations.
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
    x = max(0.0, min(1.0, float(x)))
    return 0.15 + (x * 0.95)  # 0.0 -> 0.15, 1.0 -> 1.10

# ============================================================
# PROJECT MODEL
# ============================================================
def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
        "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
    }

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

        # Story Bible identity is PER-PROJECT (relationship lock), content stays editable.
        "story_bible_id": story_bible_id,
        "story_bible_created_ts": ts,
        "story_bible_binding": {
            "locked": True,
            "locked_ts": ts,
            "source": "system",  # workspace | clone | system
            "source_story_bible_id": None,
        },
        "story_bible_fingerprint": "",

        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        # NOTE: We persist AI intensity per project here for reliability,
        # but the CONTROL is in Story Bible panel (left). Voice Bible UI stays locked.
        "voice_bible": {
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
            "ai_intensity": 0.75,  # global AI aggression knob
        },
        "locks": {
            "story_bible_lock": True,          # relationship lock: bible belongs to this project forever
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },
        "voices": default_voice_vault(),  # compact storage: store only text+ts; vectors rebuilt in session
    }


# ============================================================
# STORY BIBLE WORKSPACE (pre-project creation space)
# ============================================================
def default_story_bible_workspace() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "workspace_story_bible_id": hashlib.md5(f"wsb|{ts}".encode("utf-8")).hexdigest()[:12],
        "workspace_story_bible_created_ts": ts,
        "title": "",
        "draft": "",
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        # Keep these as DEFAULT templates for new projects, unless you change them.
        "voice_sample": "",
        "ai_intensity": 0.75,
        "voices": compact_voice_vault(rebuild_vectors_in_voice_vault(default_voice_vault())),
    }

def in_workspace_mode() -> bool:
    return (st.session_state.active_bay == "NEW") and (st.session_state.project_id is None)

def save_workspace_from_session() -> None:
    w = st.session_state.sb_workspace or default_story_bible_workspace()
    w["title"] = st.session_state.get("workspace_title", w.get("title",""))
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
    st.session_state.sb_workspace = w

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
    st.session_state.ai_intensity = float(w.get("ai_intensity", 0.75))
    st.session_state.voices = rebuild_vectors_in_voice_vault(w.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True
    st.session_state.workspace_title = w.get("title", "") or ""

def reset_workspace_story_bible(keep_templates: bool = True) -> None:
    old = st.session_state.sb_workspace or default_story_bible_workspace()
    neww = default_story_bible_workspace()

    if keep_templates:
        neww["voice_sample"] = old.get("voice_sample", "")
        neww["ai_intensity"] = float(old.get("ai_intensity", 0.75))
        neww["voices"] = old.get("voices", default_voice_vault())

    st.session_state.sb_workspace = neww
    if in_workspace_mode():
        load_workspace_into_session()

# ============================================================
# SESSION INIT
# ============================================================
def init_state():
    defaults = {
        "active_bay": "NEW",
        "projects": {},  # id -> project dict
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

        # GLOBAL AI intensity (CONTROL in Story Bible panel)
        "ai_intensity": 0.75,

        "locks": {
            "story_bible_lock": True,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },

        "voices": {},
        "voices_seeded": False,

        "last_saved_digest": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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

    vb = p.get("voice_bible", {}) or {}
    for k in [
        "vb_style_on","vb_genre_on","vb_trained_on","vb_match_on","vb_lock_on",
        "writing_style","genre","trained_voice","voice_sample","voice_lock_prompt",
        "style_intensity","genre_intensity","trained_intensity","match_intensity","lock_intensity",
        "pov","tense","ai_intensity"
    ]:
        if k in vb:
            st.session_state[k] = vb[k]

    locks = p.get("locks", {}) or {}
    if isinstance(locks, dict):
        st.session_state.locks = locks

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True

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
    p["voice_bible"] = {
        "vb_style_on": st.session_state.vb_style_on,
        "vb_genre_on": st.session_state.vb_genre_on,
        "vb_trained_on": st.session_state.vb_trained_on,
        "vb_match_on": st.session_state.vb_match_on,
        "vb_lock_on": st.session_state.vb_lock_on,
        "writing_style": st.session_state.writing_style,
        "genre": st.session_state.genre,
        "trained_voice": st.session_state.trained_voice,
        "voice_sample": st.session_state.voice_sample,
        "voice_lock_prompt": st.session_state.voice_lock_prompt,
        "style_intensity": st.session_state.style_intensity,
        "genre_intensity": st.session_state.genre_intensity,
        "trained_intensity": st.session_state.trained_intensity,
        "match_intensity": st.session_state.match_intensity,
        "lock_intensity": st.session_state.lock_intensity,
        "pov": st.session_state.pov,
        "tense": st.session_state.tense,
        "ai_intensity": float(st.session_state.ai_intensity),
    }
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
    # Persist current context
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
            # NEW bay has a persistent Story Bible workspace.
            load_workspace_into_session()
            st.session_state.voice_status = "NEW: (Story Bible workspace)"
        else:
            # Other bays may be empty.
            st.session_state.main_text = ""
            st.session_state.synopsis = ""
            st.session_state.genre_style_notes = ""
            st.session_state.world = ""
            st.session_state.characters = ""
            st.session_state.outline = ""
            st.session_state.voice_sample = ""
            st.session_state.ai_intensity = 0.75
            st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
            st.session_state.voices_seeded = True
            st.session_state.voice_status = f"{target_bay}: (empty)"

    st.session_state.last_action = f"Bay → {target_bay}"


def _fingerprint_story_bible(sb: Dict[str, str]) -> str:
    parts = [
        (sb.get("synopsis","") or "").strip(),
        (sb.get("genre_style_notes","") or "").strip(),
        (sb.get("world","") or "").strip(),
        (sb.get("characters","") or "").strip(),
        (sb.get("outline","") or "").strip(),
    ]
    blob = "\n\n---\n\n".join(parts)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()

def create_project_from_current_bible(title: str) -> str:
    title = title.strip() if title.strip() else f"New Project {now_ts()}"

    # SOURCE CONTEXT
    source = "workspace" if in_workspace_mode() else "clone"
    source_story_bible_id = None
    source_story_bible_created_ts = None

    if source == "workspace":
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        source_story_bible_id = w.get("workspace_story_bible_id")
        source_story_bible_created_ts = w.get("workspace_story_bible_created_ts")
    else:
        pid = st.session_state.project_id
        if pid and pid in st.session_state.projects:
            source_story_bible_id = st.session_state.projects[pid].get("story_bible_id")

    # CREATE
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

    # LOCK THE RELATIONSHIP (not the content)
    if source == "workspace" and source_story_bible_id:
        p["story_bible_id"] = source_story_bible_id
        if source_story_bible_created_ts:
            p["story_bible_created_ts"] = source_story_bible_created_ts

    p["story_bible_binding"] = {
        "locked": True,
        "locked_ts": now_ts(),
        "source": source,  # workspace | clone
        "source_story_bible_id": source_story_bible_id,
    }
    p["story_bible_fingerprint"] = _fingerprint_story_bible(p["story_bible"])

    # Voice templates + intensity
    p["voice_bible"]["voice_sample"] = st.session_state.voice_sample
    p["voice_bible"]["ai_intensity"] = float(st.session_state.ai_intensity)

    # Voices vault
    p["voices"] = compact_voice_vault(st.session_state.voices)

    # Persist
    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    # If this was a workspace start, immediately mint a NEW workspace bible for the next project.
    if source == "workspace":
        reset_workspace_story_bible(keep_templates=True)

    return p["id"]


def promote_project(pid: str, to_bay: str) -> None:
    p = st.session_state.projects.get(pid)
    if not p:
        return
    p["bay"] = to_bay
    p["updated_ts"] = now_ts()

# ============================================================
# AUTOSAVE ALL
# ============================================================
def _payload() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-import-export-v1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "sb_workspace": st.session_state.sb_workspace,
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
        st.session_state.sb_workspace = st.session_state.get("sb_workspace") or default_story_bible_workspace()
        switch_bay("NEW")
        return
    try:
        with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        projs = payload.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = payload.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            for b in BAYS:
                apbb.setdefault(b, None)
            st.session_state.active_project_by_bay = apbb

        # Workspace restore + migration
        w = payload.get("sb_workspace")
        if isinstance(w, dict) and w.get("workspace_story_bible_id"):
            st.session_state.sb_workspace = w
        else:
            st.session_state.sb_workspace = default_story_bible_workspace()

        # Project migrations (older saves)
        for pid, p in (st.session_state.projects or {}).items():
            if not isinstance(p, dict):
                continue
            ts = p.get("created_ts") or now_ts()
            if not p.get("story_bible_id"):
                title = p.get("title", "Untitled")
                p["story_bible_id"] = hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12]
            if not p.get("story_bible_created_ts"):
                p["story_bible_created_ts"] = ts
            if not isinstance(p.get("story_bible_binding"), dict):
                p["story_bible_binding"] = {"locked": True, "locked_ts": ts, "source": "system", "source_story_bible_id": None}
            if "story_bible_fingerprint" not in p:
                sb = p.get("story_bible", {}) or {}
                try:
                    fp = hashlib.md5(("\n\n---\n\n".join([
                        (sb.get("synopsis","") or "").strip(),
                        (sb.get("genre_style_notes","") or "").strip(),
                        (sb.get("world","") or "").strip(),
                        (sb.get("characters","") or "").strip(),
                        (sb.get("outline","") or "").strip(),
                    ])).encode("utf-8")).hexdigest()
                except Exception:
                    fp = ""
                p["story_bible_fingerprint"] = fp

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

        st.session_state.voice_status = f"Loaded autosave ({payload.get('meta', {}).get('saved_at','')})."
        st.session_state.last_saved_digest = _digest(_payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"
        st.session_state.sb_workspace = default_story_bible_workspace()
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
    if st.session_state.synopsis.strip(): sb.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if st.session_state.genre_style_notes.strip(): sb.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if st.session_state.world.strip(): sb.append(f"WORLD:\n{st.session_state.world.strip()}")
    if st.session_state.characters.strip(): sb.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if st.session_state.outline.strip(): sb.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
    return "\n\n".join(sb).strip() if sb else "— None provided —"

def build_partner_brief(action_name: str, lane: str) -> str:
    story_bible = _story_bible_text()

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

    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)
    ex_block = "\n\n---\n\n".join(exemplars) if exemplars else "— None —"

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

TRAINED EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE:
{story_bible}

ACTION: {action_name}
""".strip()

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
        temperature=temperature_from_intensity(st.session_state.ai_intensity),
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


# ============================================================
# IMPORT / EXPORT (Documents + Bundles)
# ============================================================
from io import BytesIO

def _safe_filename(s: str, fallback: str = "export") -> str:
    s = re.sub(r"[^\w\- ]+", "", (s or "").strip()).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:80] if s else fallback

def _read_uploaded_text(uploaded) -> Tuple[str, str]:
    """Read .txt/.md/.docx from Streamlit UploadedFile."""
    if uploaded is None:
        return "", ""
    name = getattr(uploaded, "name", "") or ""
    raw = uploaded.getvalue()
    ext = os.path.splitext(name.lower())[1]

    # Plain text
    if ext in (".txt", ".md", ".markdown", ".text", ""):
        try:
            return raw.decode("utf-8"), name
        except Exception:
            return raw.decode("utf-8", errors="ignore"), name

    # DOCX
    if ext == ".docx":
        try:
            from docx import Document  # python-docx
            doc = Document(BytesIO(raw))
            parts = []
            for p in doc.paragraphs:
                t = (p.text or "").strip()
                if t:
                    parts.append(t)
            return "\n\n".join(parts), name
        except Exception:
            # Fallback: best-effort decode (won't be pretty, but won't crash)
            try:
                return raw.decode("utf-8", errors="ignore"), name
            except Exception:
                return "", name

    # Unknown binary: try utf-8 best effort
    try:
        return raw.decode("utf-8", errors="ignore"), name
    except Exception:
        return "", name

def _sb_sections_from_text_heuristic(text: str) -> Dict[str, str]:
    """
    Minimal, deterministic breakdown.
    If headings exist, split by them; otherwise drop the full text into Synopsis.
    """
    t = _normalize_text(text)
    if not t:
        return {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""}

    # Common heading patterns
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
            # no heading yet: treat as synopsis blob
            buckets["synopsis"].append(line)

    out = {k: _normalize_text("\n".join(v)) for k, v in buckets.items()}
    # If everything went into synopsis and it's huge, leave it — author can refine later.
    return out

def _extract_json_object(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    # Strip fenced blocks
    s2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE | re.MULTILINE)
    # Grab first {...} span
    m = re.search(r"\{.*\}", s2, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def sb_breakdown_ai(text: str) -> Dict[str, str]:
    """
    Uses OpenAI (if configured) to break a source document into Story Bible sections.
    Falls back to heuristic if OpenAI fails.
    """
    prompt = """Break the provided source document into these Story Bible sections.
Return STRICT JSON with these exact keys:
synopsis, genre_style_notes, world, characters, outline

Rules:
- Use clear, concrete specifics (names, places, stakes).
- Preserve existing proper nouns from the text.
- If a section is unknown, return an empty string for it.
- No commentary. JSON only.
"""
    try:
        out = call_openai(
            system_brief="You are a precise literary analyst. You output only valid JSON.",
            user_task=prompt,
            text=text
        )
        obj = _extract_json_object(out) or {}
        return {
            "synopsis": _normalize_text(str(obj.get("synopsis",""))),
            "genre_style_notes": _normalize_text(str(obj.get("genre_style_notes",""))),
            "world": _normalize_text(str(obj.get("world",""))),
            "characters": _normalize_text(str(obj.get("characters",""))),
            "outline": _normalize_text(str(obj.get("outline",""))),
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

def story_bible_markdown(title: str, sb: Dict[str, str], meta: Dict[str, Any]) -> str:
    t = title or "Untitled"
    sb = sb or {}
    def sec(h, k):
        body = (sb.get(k, "") or "").strip()
        return f"## {h}\n\n{body}\n" if body else f"## {h}\n\n\n"
    front = f"# Story Bible — {t}\n\n"
    front += f"- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n"
    return front + "\n".join([
        sec("Synopsis", "synopsis"),
        sec("Genre / Style Notes", "genre_style_notes"),
        sec("World", "world"),
        sec("Characters", "characters"),
        sec("Outline", "outline"),
    ])

def draft_markdown(title: str, draft: str, meta: Dict[str, Any]) -> str:
    t = title or "Untitled"
    front = f"# Draft — {t}\n\n"
    front += f"- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n---\n\n"
    return front + (draft or "")

def make_project_bundle(pid: str) -> Dict[str, Any]:
    p = st.session_state.projects.get(pid, {}) or {}
    return {
        "meta": {"exported_at": now_ts(), "type": "project_bundle", "version": "1"},
        "project": p,
    }

def make_library_bundle() -> Dict[str, Any]:
    # Ensure latest writes
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

    # Avoid id collisions
    pid = str(proj.get("id") or _new_pid_like("import"))
    if pid in (st.session_state.projects or {}):
        pid = _new_pid_like(pid)

    proj = json.loads(json.dumps(proj))  # deep copy
    proj["id"] = pid
    if rename.strip():
        proj["title"] = rename.strip()
    if target_bay in BAYS:
        proj["bay"] = target_bay
    proj["updated_ts"] = now_ts()

    # Migration safety
    ts = proj.get("created_ts") or now_ts()
    if not proj.get("story_bible_id"):
        title = proj.get("title", "Untitled")
        proj["story_bible_id"] = hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    proj.setdefault("story_bible_created_ts", ts)
    if not isinstance(proj.get("story_bible_binding"), dict):
        proj["story_bible_binding"] = {"locked": True, "locked_ts": ts, "source": "import", "source_story_bible_id": None}
    proj.setdefault("story_bible_fingerprint", "")

    st.session_state.projects[pid] = proj
    st.session_state.active_project_by_bay[proj.get("bay","NEW")] = pid
    return pid

def import_library_bundle(bundle: Dict[str, Any], merge: bool = True) -> int:
    """
    Merge-only import: bring projects into the current library without wiping anything.
    Returns number of projects imported.
    """
    if not isinstance(bundle, dict):
        return 0
    projs = bundle.get("projects")
    if not isinstance(projs, dict):
        return 0
    imported = 0
    for _, proj in projs.items():
        if not isinstance(proj, dict):
            continue
        tmp = {"project": proj}
        pid = import_project_bundle(tmp, target_bay=proj.get("bay","NEW"), rename="")
        if pid:
            imported += 1

    # Workspace (optional merge)
    w = bundle.get("sb_workspace")
    if isinstance(w, dict) and w.get("workspace_story_bible_id"):
        # Only fill workspace if ours is empty-ish
        cur = st.session_state.sb_workspace or default_story_bible_workspace()
        cur_sb = (cur.get("story_bible", {}) or {})
        cur_empty = not any((cur_sb.get(k,"") or "").strip() for k in ["synopsis","genre_style_notes","world","characters","outline"])
        if cur_empty:
            st.session_state.sb_workspace = w
    return imported

# ============================================================
# COMMANDS (Junk Drawer)
# ============================================================
CMD_FIND   = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)

def next_bay(bay: str) -> Optional[str]:
    if bay == "NEW": return "ROUGH"
    if bay == "ROUGH": return "EDIT"
    if bay == "EDIT": return "FINAL"
    return None

def handle_junk_commands():
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

handle_junk_commands()

# ============================================================
# PARTNER ACTIONS (all generations obey AI Intensity)
# ============================================================
def partner_action(action: str):
    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)
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
                    "MANDATORY: incorporate at least 2 Story Bible specifics. "
                    "No recap. No planning. Just prose."
                )
                out = call_openai(brief, task, text if text.strip() else "Start the opening.")
                apply_append(out)
            else:
                apply_replace(text)
            return

        if action == "Rewrite":
            if use_ai:
                task = f"Rewrite for professional quality in lane ({lane}). Preserve meaning and canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(local_cleanup(text))
            return

        if action == "Expand":
            if use_ai:
                task = f"Expand with meaningful depth in lane ({lane}). No padding. Preserve canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Replace the final sentence with a stronger one (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = f"Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text."
                out = call_openai(brief, task, cleaned)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
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
            <br/>AI Intensity: {float(st.session_state.ai_intensity):.2f}
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
# LEFT — STORY BIBLE (AI Intensity lives HERE)
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

    # Story Bible relationship lock banner (project-specific Story Bible IDs)
    if sel_pid:
        p = st.session_state.projects.get(sel_pid, {}) or {}
        sbid = p.get("story_bible_id", "—")
        sbts = p.get("story_bible_created_ts", "—")
        bind = p.get("story_bible_binding", {}) or {}
        src = bind.get("source", "—")
        st.caption(f"Locked Story Bible → Project • Bible ID: **{sbid}** • Created: **{sbts}** • Source: **{src}**")
    else:
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        sbid = w.get("workspace_story_bible_id", "—")
        sbts = w.get("workspace_story_bible_created_ts", "—")
        st.caption(f"Workspace Story Bible (not linked yet) • Bible ID: **{sbid}** • Created: **{sbts}**")

    # Switch context if changed
    if sel_pid != st.session_state.project_id:
        # Save current context first
        if in_workspace_mode():
            save_workspace_from_session()
        else:
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
                st.session_state.voice_sample = ""
                st.session_state.ai_intensity = 0.75
                st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
                st.session_state.voices_seeded = True
                st.session_state.voice_status = f"{bay}: (empty)"

        st.session_state.last_action = "Select Context"
        autosave()

    action_cols = st.columns([1, 1])
    if bay == "NEW":
        label = "Start Project (Lock Bible → Project)" if in_workspace_mode() else "Create Project (from Bible)"
        if action_cols[0].button(label, key="create_project_btn"):
            title_guess = (st.session_state.synopsis.strip().splitlines()[0].strip()
                           if st.session_state.synopsis.strip() else "New Project")
            pid = create_project_from_current_bible(title_guess)
            load_project_into_session(pid)
            st.session_state.voice_status = f"Created in NEW: {st.session_state.project_title}"
            st.session_state.last_action = "Create Project"
            autosave()

        # Workspace-only: mint a fresh blank Story Bible (new Bible ID), keep templates.
        if in_workspace_mode():
            if action_cols[0].button("New Story Bible (fresh ID)", key="new_workspace_bible_btn"):
                reset_workspace_story_bible(keep_templates=True)
                st.session_state.voice_status = "Workspace: new Story Bible minted"
                st.session_state.last_action = "New Story Bible"
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
        if nb and action_cols[1].button(f"Promote → {nb.title()}", key=f"promote_{bay.lower()}"):
            if st.session_state.project_id:
                save_session_into_project()
                promote_project(st.session_state.project_id, nb)
                st.session_state.active_project_by_bay[nb] = st.session_state.project_id
                switch_bay(nb)
                st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
                st.session_state.last_action = f"Promote → {nb}"
                autosave()

    # ✅ AI Intensity lives in Story Bible panel (left)
    st.slider(
        "AI Intensity",
        0.0, 1.0,
        key="ai_intensity",
        help="0.0 = conservative/precise, 1.0 = bold/creative. Applies to every AI generation.",
        on_change=autosave
    )

    with st.expander("📦 Import / Export"):
        # -------------------
        # Import → Writing Desk
        # -------------------
        with st.expander("⬆️ Import Document → Writing Desk"):
            st.caption("Upload .txt / .md / .docx, or paste text. Imports into the center writing desk.")
            up = st.file_uploader("Upload file", type=["txt","md","markdown","docx"], key="io_draft_upload")
            paste = st.text_area("Or paste text", key="io_draft_paste", height=120)
            mode = st.radio("Import mode", ["Append", "Replace"], horizontal=True, key="io_draft_mode")

            if st.button("Import to Writing Desk", key="io_import_draft_btn"):
                src, name = _read_uploaded_text(up)
                src = src if src.strip() else paste
                src = _normalize_text(src)
                if not src.strip():
                    st.warning("No text found to import.")
                else:
                    if mode == "Replace":
                        st.session_state.main_text = src
                    else:
                        base = (st.session_state.main_text or "").rstrip()
                        st.session_state.main_text = (base + ("\n\n" if base else "") + src).strip()
                    st.session_state.voice_status = f"Imported to Writing Desk ({name or 'paste'})"
                    st.session_state.last_action = "Import → Draft"
                    autosave()

        # -------------------
        # Import → Story Bible (breakdown)
        # -------------------
        with st.expander("⬆️ Import Document → Story Bible (Breakdown)"):
            st.caption("Break a source document into Story Bible sections. AI breakdown uses your AI Intensity.")
            up = st.file_uploader("Upload file", type=["txt","md","markdown","docx"], key="io_sb_upload")
            paste = st.text_area("Or paste text", key="io_sb_paste", height=120)

            use_ai = st.checkbox(
                "Use AI Breakdown",
                value=bool(OPENAI_API_KEY),
                disabled=not bool(OPENAI_API_KEY),
                help="Requires OPENAI_API_KEY. Falls back to heuristic if AI fails.",
                key="io_sb_use_ai"
            )
            merge_mode = st.radio("Merge mode", ["Append", "Replace"], horizontal=True, key="io_sb_merge_mode")

            if st.button("Breakdown into Story Bible", key="io_import_sb_btn"):
                src, name = _read_uploaded_text(up)
                src = src if src.strip() else paste
                src = _normalize_text(src)
                if not src.strip():
                    st.warning("No text found to break down.")
                else:
                    sections = sb_breakdown_ai(src) if use_ai else _sb_sections_from_text_heuristic(src)
                    st.session_state.synopsis = _merge_section(st.session_state.synopsis, sections.get("synopsis",""), merge_mode)
                    st.session_state.genre_style_notes = _merge_section(st.session_state.genre_style_notes, sections.get("genre_style_notes",""), merge_mode)
                    st.session_state.world = _merge_section(st.session_state.world, sections.get("world",""), merge_mode)
                    st.session_state.characters = _merge_section(st.session_state.characters, sections.get("characters",""), merge_mode)
                    st.session_state.outline = _merge_section(st.session_state.outline, sections.get("outline",""), merge_mode)

                    st.session_state.voice_status = f"Imported → Story Bible ({'AI' if use_ai else 'heuristic'}) • {name or 'paste'}"
                    st.session_state.last_action = "Import → Story Bible"
                    autosave()

        st.divider()

        # -------------------
        # Export (Draft + Story Bible)
        # -------------------
        with st.expander("⬇️ Export Draft / Story Bible"):
            if in_workspace_mode():
                title = "Workspace"
                meta = {"Context": "Workspace", "Bay": st.session_state.active_bay}
            else:
                title = st.session_state.project_title
                meta = {"Context": "Project", "Bay": st.session_state.active_bay, "Project ID": st.session_state.project_id}

            # Ensure most recent data is saved into project/workspace
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

            stem = _safe_filename(title, "olivetti")
            st.download_button(
                "Download Draft (.txt)",
                data=draft_txt,
                file_name=f"{stem}_draft.txt",
                mime="text/plain",
                key="io_dl_draft_txt"
            )
            st.download_button(
                "Download Draft (.md)",
                data=draft_markdown(title, draft_txt, meta),
                file_name=f"{stem}_draft.md",
                mime="text/markdown",
                key="io_dl_draft_md"
            )
            st.download_button(
                "Download Story Bible (.md)",
                data=story_bible_markdown(title, sb_dict, meta),
                file_name=f"{stem}_story_bible.md",
                mime="text/markdown",
                key="io_dl_sb_md"
            )

            # Optional DOCX exports if python-docx is available
            try:
                from docx import Document  # type: ignore
                def _docx_bytes(doc: "Document") -> bytes:
                    buf = BytesIO()
                    doc.save(buf)
                    return buf.getvalue()

                d = Document()
                d.add_heading(f"Draft — {title}", level=0)
                for mk, mv in meta.items():
                    d.add_paragraph(f"{mk}: {mv}")
                d.add_paragraph(now_ts())
                d.add_paragraph("")
                for para in _split_paragraphs(draft_txt):
                    d.add_paragraph(para)
                st.download_button(
                    "Download Draft (.docx)",
                    data=_docx_bytes(d),
                    file_name=f"{stem}_draft.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="io_dl_draft_docx"
                )

                sb_doc = Document()
                sb_doc.add_heading(f"Story Bible — {title}", level=0)
                for mk, mv in meta.items():
                    sb_doc.add_paragraph(f"{mk}: {mv}")
                sb_doc.add_paragraph(now_ts())
                for h, k in [("Synopsis","synopsis"),("Genre / Style Notes","genre_style_notes"),("World","world"),("Characters","characters"),("Outline","outline")]:
                    sb_doc.add_heading(h, level=1)
                    body = (sb_dict.get(k,"") or "").strip()
                    if body:
                        for para in _split_paragraphs(body):
                            sb_doc.add_paragraph(para)
                    else:
                        sb_doc.add_paragraph("")
                st.download_button(
                    "Download Story Bible (.docx)",
                    data=_docx_bytes(sb_doc),
                    file_name=f"{stem}_story_bible.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="io_dl_sb_docx"
                )
            except Exception:
                st.caption("DOCX export unavailable (python-docx not installed in this environment).")

        # -------------------
        # Bundles (JSON)
        # -------------------
        with st.expander("⬇️ Export / Import Bundles (.json)"):
            # Export bundle buttons
            if st.session_state.project_id:
                bundle = json.dumps(make_project_bundle(st.session_state.project_id), ensure_ascii=False, indent=2)
                st.download_button(
                    "Download Project Bundle (.json)",
                    data=bundle,
                    file_name=f"{_safe_filename(st.session_state.project_title,'project')}_bundle.json",
                    mime="application/json",
                    key="io_dl_project_bundle"
                )
            lib = json.dumps(make_library_bundle(), ensure_ascii=False, indent=2)
            st.download_button(
                "Download Full Library (.json)",
                data=lib,
                file_name="olivetti_library_bundle.json",
                mime="application/json",
                key="io_dl_library_bundle"
            )

            st.divider()
            st.caption("Import bundles to restore projects or merge libraries. Import is merge-only (no wiping).")
            target_bay = st.selectbox("Imported projects go to bay", BAYS, index=0, key="io_import_target_bay")
            rename = st.text_input("Optional rename for single project import", key="io_import_rename", placeholder="Leave blank to keep title")
            up = st.file_uploader("Upload .json bundle", type=["json"], key="io_bundle_upload")
            switch_after = st.checkbox("Switch to imported project after import", value=True, key="io_switch_after_import")

            if st.button("Import Bundle", key="io_import_bundle_btn"):
                if up is None:
                    st.warning("Upload a .json bundle first.")
                else:
                    try:
                        obj = json.loads(up.getvalue().decode("utf-8"))
                    except Exception:
                        st.error("Could not read JSON. Ensure it is valid UTF-8 JSON.")
                        obj = None

                    if isinstance(obj, dict) and obj.get("projects"):
                        n = import_library_bundle(obj, merge=True)
                        st.session_state.voice_status = f"Imported library bundle: {n} projects merged."
                        st.session_state.last_action = "Import Library Bundle"
                        autosave()
                    elif isinstance(obj, dict) and obj.get("project"):
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
                        else:
                            st.error("That JSON doesn't look like a project bundle.")
                    else:
                        st.error("Bundle type not recognized. Expect a project_bundle or library_bundle JSON.")

    with st.expander("🗃 Junk Drawer"):
        st.text_area(
            "", key="junk", height=80, on_change=autosave,
            help="Commands: /create: Title  |  /promote  |  /find: term"
        )
        st.text_area("Tool Output", key="tool_output", height=140, disabled=True)

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
# CENTER — WRITING DESK (freewriting only)
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
    if b2[2].button("Find", key="btn_find"): st.session_state.tool_output = "Find is wired via /find: in Junk Drawer."; autosave()
    if b2[3].button("Synonym", key="btn_synonym"): partner_action("Synonym")
    if b2[4].button("Sentence", key="btn_sentence"): partner_action("Sentence")

# ============================================================
# RIGHT — VOICE BIBLE (LOCKED UI — NO AI INTENSITY HERE)
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
        help="(Voice import wiring remains in your full build.)",
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

# ============================================================
# SAFETY NET SAVE EVERY RERUN
# ============================================================
save_all_to_disk()
