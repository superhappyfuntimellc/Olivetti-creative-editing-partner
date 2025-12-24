import os
import re
import math
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from prompts import make_voice_learn_payload
from ai import generate_json

import streamlit as st

# =========================
# Olivetti — Base Engine
# Single-file Streamlit app
# =========================

# --- Stability: disable file watcher issues in some deployments ---
os.environ.setdefault("STREAMLIT_WATCH_FILES", "false")

# --- OpenAI config (optional) ---
DEFAULT_MODEL = "gpt-4.1-mini"
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # type: ignore[attr-defined]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)  # type: ignore[attr-defined]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

# --- App config ---
st.set_page_config(page_title="Olivetti", layout="wide", initial_sidebar_state="expanded")

# --- Sexy & shiny skin (no layout change) ---
st.markdown(
    """
    <style>
    :root{
      --o-brass:#c7a24c;
      --o-brass2:#e2c26d;
      --o-steel:#15181f;
      --o-graph:#0f1218;
      --o-paper:#f6f2e8;
      --o-ink:#111213;
      --o-ink2:#2a2d34;
      --o-shadow: 0 10px 30px rgba(0,0,0,.30);
      --o-shadow2: 0 6px 18px rgba(0,0,0,.22);
      --o-radius: 18px;
    }

    /* Page background */
    .stApp {
      background: radial-gradient(1200px 700px at 20% 10%, rgba(199,162,76,.10), transparent 55%),
                  radial-gradient(900px 520px at 85% 35%, rgba(226,194,109,.08), transparent 60%),
                  linear-gradient(180deg, #0b0d12 0%, #0d1017 55%, #0b0d12 100%);
      color: #f2f3f5;
    }

    /* Make expanders/cards feel like a console */
    div[data-testid="stExpander"] > details {
      border-radius: var(--o-radius);
      background: linear-gradient(180deg, rgba(21,24,31,.95), rgba(10,12,16,.92));
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: var(--o-shadow2);
      overflow: hidden;
    }
    div[data-testid="stExpander"] > details > summary {
      font-weight: 600;
      letter-spacing: .2px;
    }

    /* Buttons: brass */
    button[kind="primary"]{
      background: linear-gradient(180deg, rgba(226,194,109,1), rgba(199,162,76,1)) !important;
      color: #121212 !important;
      border: 1px solid rgba(0,0,0,.35) !important;
      box-shadow: 0 6px 18px rgba(199,162,76,.25);
      border-radius: 14px !important;
      transition: transform .08s ease, filter .08s ease;
    }
    button[kind="primary"]:hover{ transform: translateY(-1px); filter: brightness(1.03); }

    /* Secondary buttons: steel */
    button[kind="secondary"]{
      background: linear-gradient(180deg, rgba(40,45,56,.95), rgba(20,24,32,.95)) !important;
      border: 1px solid rgba(255,255,255,.12) !important;
      border-radius: 14px !important;
      box-shadow: var(--o-shadow2);
      transition: transform .08s ease, filter .08s ease;
    }
    button[kind="secondary"]:hover{ transform: translateY(-1px); filter: brightness(1.05); }

    /* Writing paper */
    div[data-testid="stTextArea"] textarea{
      background: linear-gradient(180deg, rgba(246,242,232,1), rgba(241,236,224,1)) !important;
      color: var(--o-ink) !important;
      border-radius: 16px !important;
      border: 1px solid rgba(0,0,0,.18) !important;
      box-shadow: var(--o-shadow2);
      font-size: 18px !important;
      line-height: 1.65 !important;
      padding: 18px !important;
      min-height: 520px !important;
      resize: vertical !important;
    }

    /* Inputs */
    input, select{
      border-radius: 14px !important;
    }

    /* Tighten margins a bit */
    .block-container{ padding-top: 1.1rem; padding-bottom: 1.1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Constants
# ============================================================
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]
LANES = ["Dialogue", "Narration", "Interiority", "Action"]

ACTIONS_PRIMARY = ["Write", "Rewrite", "Expand", "Rephrase", "Describe"]
ACTIONS_SECONDARY = ["Spell", "Grammar", "Find", "Synonym", "Sentence"]
ALL_ACTIONS = ACTIONS_PRIMARY + ACTIONS_SECONDARY

ENGINE_STYLES = ["NARRATIVE", "DESCRIPTIVE", "EMOTIONAL", "LYRICAL"]
ENGINE_GENRES = ["Romance", "Thriller", "Fantasy", "Science Fiction", "Comedy"]

MAX_UPLOAD_BYTES = 10_000_000  # 10MB safety
MAX_BANK_SAMPLES_PER_LANE = 250
RETRIEVE_WINDOW = 160

AUTOSAVE_DIR = "autosave"
AUTOSAVE_FILE = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")
AUTOSAVE_BAK = os.path.join(AUTOSAVE_DIR, "olivetti_state.bak.json")

WORD_RE = re.compile(r"[A-Za-z']+")

# ============================================================
# Utilities
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
    t = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()

def split_paragraphs(text: str) -> List[str]:
    t = normalize_text(text)
    if not t:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", t, flags=re.MULTILINE) if p.strip()]

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
        return {}

# ============================================================
# Lane detection (lightweight)
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
    dialogue_score = (2.5 if quote_count >= 2 else 0.0) + (1.5 if has_dialogue_punct else 0.0)

    toks = tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i", "me", "my", "mine", "myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1:
            interior_score = 2.2

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
    paras = split_paragraphs(text)
    return detect_lane(paras[-1]) if paras else "Narration"

# ============================================================
# Data model defaults
# ============================================================
def default_story_bible() -> Dict[str, str]:
    return {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""}

def default_voice_bible() -> Dict[str, Any]:
    return {
        # Tabs / modules (always add-only)
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_lock_on": False,
        "vb_pov_on": True,
        "vb_tense_on": True,

        # Selections
        "writing_style": "NARRATIVE",
        "genre": "Romance",
        "trained_voice": "— None —",
        "pov": "Close Third",
        "tense": "Past",

        # Prompts / exemplars
        "voice_sample": "",
        "voice_lock_prompt": "",

        # Intensities (0–1)
        "style_intensity": 0.65,
        "genre_intensity": 0.65,
        "trained_intensity": 0.70,
        "match_intensity": 0.80,
        "lock_intensity": 1.00,
        "pov_strength": 0.90,
        "tense_strength": 0.90,

        # Global intensity (main left slider remains authoritative)
        "ai_intensity": 0.75,

        # Global Voice (optional): master in global settings + per-project toggle here
        "use_global_voice": False,
        "global_voice_strength": 0.65,
    }


def default_action_controls() -> Dict[str, Any]:FF
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {"enabled": True, "use_global": True, "intensity": 0.75}
    return {"locked": False, "items": items}

def default_import_controls() -> Dict[str, Any]:
    return {"use_ai": True, "use_global_intensity": True, "intensity": 0.65, "merge_mode": "Append"}

def _default_lane_bank() -> Dict[str, List[Dict[str, Any]]]:
    return {ln: [] for ln in LANES}

def default_style_banks() -> Dict[str, Any]:
    # engine styles: per-lane exemplars
    return {style: {"created_ts": now_ts(), "lanes": _default_lane_bank()} for style in ENGINE_STYLES}

def default_genre_banks() -> Dict[str, Any]:
    return {g: {"created_ts": now_ts(), "lanes": _default_lane_bank()} for g in ENGINE_GENRES}

def default_global_voice() -> Dict[str, Any]:
    # Global voice is optional and controlled by a master toggle + strength slider
    return {
        "enabled": False,
        "strength": 0.65,
        "created_ts": now_ts(),
        "lanes": _default_lane_bank(),
    }

def new_project_payload(title: str) -> Dict[str, Any]:
    ts = now_ts()
    title = (title or "").strip() or "Untitled Project"
    pid = hashlib.md5(f"{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    sbid = hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": pid,
        "title": title,
        "created_ts": ts,
        "updated_ts": ts,
        "bay": "NEW",
        "draft": "",
        "idea_bank": "",
        "story_bible_id": sbid,
        "story_bible_created_ts": ts,
        "story_bible_locked_ts": "",  # set when project starts from workspace
        "story_bible_lock_reason": "",
        "story_bible_edit_unlocked": False,  # hard-lock behavior
        "story_bible": default_story_bible(),
        "voice_bible": default_voice_bible(),
        "action_controls": default_action_controls(),
        "import_controls": default_import_controls(),
        "imports_log": [],
        "style_banks": compact_banks(rebuild_banks(default_style_banks())),  # safe because helper defined below
        "genre_banks": compact_banks(rebuild_banks(default_genre_banks())),
        "voices": {},  # reserved for later trained "named voices" if you want
    }

def default_workspace() -> Dict[str, Any]:
    return {
        "title": "",
        "draft": "",
        "idea_bank": "",
        "story_bible": default_story_bible(),
        "voice_bible": default_voice_bible(),
        "action_controls": default_action_controls(),
        "import_controls": default_import_controls(),
        "imports_log": [],
        "style_banks": compact_banks(rebuild_banks(default_style_banks())),
        "genre_banks": compact_banks(rebuild_banks(default_genre_banks())),
    }

# ============================================================
# Bank rebuild/compact helpers (style + genre + global voice)
# Keep stable: vectors exist only in session; persisted data is compact.
# ============================================================
def _trim_sample(text: str) -> str:
    t = normalize_text(text)
    if len(t) > 2400:
        t = t[:2400].rstrip() + "…"
    return t

def rebuild_banks(compact: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name, blob in (compact or {}).items():
        lanes_in = (blob or {}).get("lanes", {}) or {}
        lanes_out: Dict[str, Any] = {ln: [] for ln in LANES}
        for ln in LANES:
            samples = lanes_in.get(ln, []) or []
            for s in samples:
                txt = _trim_sample(s.get("text", ""))
                if len(txt) < 20:
                    continue
                lanes_out[ln].append({"ts": s.get("ts") or now_ts(), "text": txt, "vec": hash_vec(txt)})
            # cap
            lanes_out[ln] = lanes_out[ln][-MAX_BANK_SAMPLES_PER_LANE:]
        out[name] = {"created_ts": blob.get("created_ts") or now_ts(), "lanes": lanes_out}
    return out

def compact_banks(full: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name, blob in (full or {}).items():
        lanes = (blob or {}).get("lanes", {}) or {}
        out[name] = {
            "created_ts": blob.get("created_ts") or now_ts(),
            "lanes": {ln: [{"ts": s.get("ts"), "text": s.get("text", "")} for s in (lanes.get(ln, []) or []) if s.get("text")] for ln in LANES},
        }
    return out

def retrieve_from_bank(bank_full: Dict[str, Any], name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    blob = (bank_full or {}).get(name)
    if not blob:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = (blob.get("lanes", {}) or {}).get(lane, []) or []
    if not pool:
        return []
    qv = hash_vec(query_text)
    window = pool[-RETRIEVE_WINDOW:]
    scored = [ (cosine(qv, s.get("vec", [])), s.get("text","")) for s in window ]
    scored.sort(key=lambda x: x[0], reverse=True)
    out = [txt for score, txt in scored[:k] if score > 0 and txt]
    return out[:k]

# Global voice bank uses same structure as a bank named "GLOBAL"
def rebuild_global_voice(compact: Dict[str, Any]) -> Dict[str, Any]:
    compact = compact or default_global_voice()
    lanes_out = {ln: [] for ln in LANES}
    lanes_in = compact.get("lanes", {}) or {}
    for ln in LANES:
        for s in (lanes_in.get(ln, []) or []):
            txt = _trim_sample(s.get("text", ""))
            if len(txt) < 20:
                continue
            lanes_out[ln].append({"ts": s.get("ts") or now_ts(), "text": txt, "vec": hash_vec(txt)})
        lanes_out[ln] = lanes_out[ln][-MAX_BANK_SAMPLES_PER_LANE:]
    return {
        "enabled": bool(compact.get("enabled", False)),
        "strength": clamp01(compact.get("strength", 0.65)),
        "created_ts": compact.get("created_ts") or now_ts(),
        "lanes": lanes_out,
    }

def compact_global_voice(full: Dict[str, Any]) -> Dict[str, Any]:
    full = full or default_global_voice()
    lanes = full.get("lanes", {}) or {}
    return {
        "enabled": bool(full.get("enabled", False)),
        "strength": clamp01(full.get("strength", 0.65)),
        "created_ts": full.get("created_ts") or now_ts(),
        "lanes": {ln: [{"ts": s.get("ts"), "text": s.get("text","")} for s in (lanes.get(ln,[]) or []) if s.get("text")] for ln in LANES},
    }

def retrieve_from_global_voice(global_full: Dict[str, Any], lane: str, query_text: str, k: int = 2) -> List[str]:
    lane = lane if lane in LANES else "Narration"
    pool = (global_full.get("lanes", {}) or {}).get(lane, []) or []
    if not pool:
        return []
    qv = hash_vec(query_text)
    window = pool[-RETRIEVE_WINDOW:]
    scored = [ (cosine(qv, s.get("vec", [])), s.get("text","")) for s in window ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [txt for score, txt in scored[:k] if score > 0 and txt][:k]

# ============================================================
# Prompt directives (adaptive)
# ============================================================
def intensity_profile(x: float) -> str:
    x = clamp01(x)
    if x <= 0.25:
        return "LOW: conservative, literal, minimal invention; prioritize continuity and clarity."
    if x <= 0.60:
        return "MED: balanced creativity; controlled invention within canon."
    if x <= 0.85:
        return "HIGH: bolder choices and richer specificity; still obey canon."
    return "MAX: aggressive originality and voice; still obey canon; no random derailments."

def temperature_from_intensity(x: float) -> float:
    x = clamp01(x)
    return 0.15 + (x * 0.95)

def engine_style_directive(style: str, x: float, lane: str) -> str:
    x = clamp01(x)
    base = {
        "NARRATIVE": "clarity, scene logic, cause→effect, controlled pacing, strong verbs, professional prose",
        "DESCRIPTIVE": "sensory specificity, concrete detail, spatial clarity, texture/light/sound, avoid purple unless intensity is high",
        "EMOTIONAL": "interiority, stakes, subtext, desire/fear, emotional logic; avoid melodrama unless intensity is high",
        "LYRICAL": "musical cadence, image-driven language, metaphor discipline; never obscure meaning; keep story moving",
    }.get(style, "professional prose")
    weight = "subtle" if x < 0.35 else "strong" if x < 0.75 else "dominant"
    return f"ENGINE STYLE: {style} ({weight}). Prioritize: {base}. Lane-aware: {lane}. Intensity={x:.2f}."

def engine_genre_directive(genre: str, x: float, lane: str) -> str:
    x = clamp01(x)
    base = {
        "Romance": "chemistry, longing, intimacy tension, emotional stakes, relational power shifts; keep consent and clarity; avoid clichés unless knowingly stylized",
        "Thriller": "tension escalation, urgency, risk, clean cause→effect, sharp beats, compression; avoid meandering",
        "Fantasy": "wonder, mythic resonance, concrete lore, consistent rules, vivid setting; avoid exposition dumps",
        "Science Fiction": "conceptual rigor, plausible tech/social speculation, crisp terminology; show consequences; avoid sterile textbook tone",
        "Comedy": "timing, contrast, voice, surprise, comedic misdirection; keep character truth; avoid cheap randomness",
    }.get(genre, "genre discipline")
    weight = "subtle" if x < 0.35 else "strong" if x < 0.75 else "dominant"
    return f"ENGINE GENRE: {genre} ({weight}). Prioritize: {base}. Lane-aware: {lane}. Intensity={x:.2f}."

# ============================================================
# OpenAI call (optional)
# ============================================================
def call_openai(system: str, user: str, intensity_x: float) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. Add 'openai' to requirements.txt.") from e

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature_from_intensity(intensity_x),
    )
    return (resp.choices[0].message.content or "").strip()

# ============================================================
# Session state init
# ============================================================
def ss_setdefault(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value

def init_state() -> None:
    ss_setdefault("active_bay", "NEW")
    ss_setdefault("projects", {})
    ss_setdefault("active_project_by_bay", {b: None for b in BAYS})
    ss_setdefault("workspace", default_workspace())

    # current context (mirrors either workspace or a project)
    ss_setdefault("project_id", None)
    ss_setdefault("project_title", "—")

    # shared editable fields (current context)
    ss_setdefault("workspace_title", "")
    ss_setdefault("main_text", "")
    ss_setdefault("junk", "")

    sb = default_story_bible()
    for k in sb:
        ss_setdefault(k, "")

    vb = default_voice_bible()
    for k, v in vb.items():
        ss_setdefault(k, v)

    ss_setdefault("locks", {"story_bible_edit_unlocked": False})
    ss_setdefault("ai_intensity", 0.75)

    # global voice
    ss_setdefault("global_voice", compact_global_voice(rebuild_global_voice(default_global_voice())))
    ss_setdefault("global_voice_full", rebuild_global_voice(st.session_state.global_voice))

    # banks live in session as full vectors for current context
    ss_setdefault("style_banks_full", rebuild_banks(st.session_state.workspace.get("style_banks", default_style_banks())))
    ss_setdefault("genre_banks_full", rebuild_banks(st.session_state.workspace.get("genre_banks", default_genre_banks())))

    # action controls scalars
    ss_setdefault("ac_locked", False)
    for a in ALL_ACTIONS:
        ss_setdefault(f"ac__{a}__enabled", True)
        ss_setdefault(f"ac__{a}__use_global", True)
        ss_setdefault(f"ac__{a}__intensity", 0.75)

    # import controls scalars
    ss_setdefault("import_use_ai", True)
    ss_setdefault("import_use_global", True)
    ss_setdefault("import_intensity", 0.65)
    ss_setdefault("import_merge_mode", "Append")
    ss_setdefault("import_paste", "")

    # trainer UI
    ss_setdefault("style_train_text", "")
    ss_setdefault("style_train_upload", None)
    ss_setdefault("style_train_style", ENGINE_STYLES[0])
    ss_setdefault("style_train_lane", "Narration")
    ss_setdefault("style_train_split", "Paragraphs")

    ss_setdefault("genre_train_text", "")
    ss_setdefault("genre_train_upload", None)
    ss_setdefault("genre_train_genre", ENGINE_GENRES[0])
    ss_setdefault("genre_train_lane", "Narration")
    ss_setdefault("genre_train_split", "Paragraphs")

    ss_setdefault("tool_output", "")
    ss_setdefault("voice_status", "—")
    ss_setdefault("last_action", "—")
    ss_setdefault("autosave_time", None)

    ss_setdefault("_dispatch", None)  # action queue
    ss_setdefault("_last_saved_digest", "")

init_state()

# ============================================================
# Persistence (atomic + backup)
# ============================================================
def _payload() -> Dict[str, Any]:
    # snapshot current context back into containers
    save_current_context()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-base-engine-v1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "projects": st.session_state.projects,
        "workspace": st.session_state.workspace,
        "global_voice": compact_global_voice(st.session_state.global_voice_full),
    }

def _digest(obj: Dict[str, Any]) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def autosave(force: bool = False) -> None:
    try:
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        payload = _payload()
        dig = _digest(payload)
        if (not force) and dig == st.session_state._last_saved_digest:
            return
        tmp = AUTOSAVE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # rotate backup
        if os.path.exists(AUTOSAVE_FILE):
            try:
                with open(AUTOSAVE_FILE, "r", encoding="utf-8") as rf:
                    prev = rf.read()
                with open(AUTOSAVE_BAK, "w", encoding="utf-8") as bf:
                    bf.write(prev)
            except Exception:
                pass
        os.replace(tmp, AUTOSAVE_FILE)
        st.session_state._last_saved_digest = dig
        st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    except Exception as e:
        st.session_state.voice_status = f"Autosave warning: {e}"

def load_autosave() -> None:
    def _load(path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    payload = _load(AUTOSAVE_FILE) or _load(AUTOSAVE_BAK)
    if not payload:
        return
    try:
        st.session_state.active_bay = payload.get("active_bay", "NEW")
        st.session_state.active_project_by_bay = payload.get("active_project_by_bay", {b: None for b in BAYS})
        st.session_state.projects = payload.get("projects", {})
        st.session_state.workspace = payload.get("workspace", default_workspace())

        # global voice compact -> rebuild
        gv_compact = payload.get("global_voice", default_global_voice())
        st.session_state.global_voice = gv_compact
        st.session_state.global_voice_full = rebuild_global_voice(gv_compact)

        # ensure keys exist
        for b in BAYS:
            st.session_state.active_project_by_bay.setdefault(b, None)

        # load current context into session keys (without dispatch hazards — this happens at top)
        load_context_from_bay_selection(st.session_state.active_bay)

        st.session_state.voice_status = f"Loaded autosave ({payload.get('meta', {}).get('saved_at','')})."
        st.session_state._last_saved_digest = _digest(_payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"

if "did_load" not in st.session_state:
    st.session_state.did_load = True
    load_autosave()

# ============================================================
# Context save/load wiring
# ============================================================
def action_controls_struct_from_scalars() -> Dict[str, Any]:
    items = {}
    for a in ALL_ACTIONS:
        items[a] = {
            "enabled": bool(st.session_state.get(f"ac__{a}__enabled", True)),
            "use_global": bool(st.session_state.get(f"ac__{a}__use_global", True)),
            "intensity": clamp01(st.session_state.get(f"ac__{a}__intensity", 0.75)),
        }
    return {"locked": bool(st.session_state.get("ac_locked", False)), "items": items}

def apply_action_controls_struct(ac: Dict[str, Any]) -> None:
    ac = ac or default_action_controls()
    st.session_state.ac_locked = bool(ac.get("locked", False))
    items = ac.get("items", {}) or {}
    for a in ALL_ACTIONS:
        it = items.get(a, {}) or {}
        st.session_state[f"ac__{a}__enabled"] = bool(it.get("enabled", True))
        st.session_state[f"ac__{a}__use_global"] = bool(it.get("use_global", True))
        st.session_state[f"ac__{a}__intensity"] = clamp01(it.get("intensity", 0.75))

def import_controls_struct_from_scalars() -> Dict[str, Any]:
    return {
        "use_ai": bool(st.session_state.import_use_ai),
        "use_global_intensity": bool(st.session_state.import_use_global),
        "intensity": clamp01(st.session_state.import_intensity),
        "merge_mode": st.session_state.import_merge_mode if st.session_state.import_merge_mode in ("Append","Replace") else "Append",
    }

def apply_import_controls_struct(ic: Dict[str, Any]) -> None:
    ic = ic or default_import_controls()
    st.session_state.import_use_ai = bool(ic.get("use_ai", True))
    st.session_state.import_use_global = bool(ic.get("use_global_intensity", True))
    st.session_state.import_intensity = clamp01(ic.get("intensity", 0.65))
    mm = ic.get("merge_mode", "Append")
    st.session_state.import_merge_mode = mm if mm in ("Append","Replace") else "Append"

def voice_bible_struct_from_session() -> Dict[str, Any]:
    keys = default_voice_bible().keys()
    return {k: st.session_state.get(k) for k in keys}

def apply_voice_bible_struct(vb: Dict[str, Any]) -> None:
    vb = vb or default_voice_bible()
    for k, v in default_voice_bible().items():
        st.session_state[k] = vb.get(k, v)

def story_bible_struct_from_session() -> Dict[str, str]:
    return {k: st.session_state.get(k, "") for k in default_story_bible().keys()}

def apply_story_bible_struct(sb: Dict[str, Any]) -> None:
    sb = sb or default_story_bible()
    for k in default_story_bible().keys():
        st.session_state[k] = sb.get(k, "")

def save_current_context() -> None:
    # save session -> current container (workspace or project)
    pid = st.session_state.project_id
    if pid and pid in st.session_state.projects:
        p = st.session_state.projects[pid]
        p["updated_ts"] = now_ts()
        p["draft"] = st.session_state.main_text
        p["idea_bank"] = st.session_state.junk
        p["story_bible"] = story_bible_struct_from_session()
        p["voice_bible"] = voice_bible_struct_from_session()
        p["action_controls"] = action_controls_struct_from_scalars()
        p["import_controls"] = import_controls_struct_from_scalars()
        # persist compact banks
        p["style_banks"] = compact_banks(st.session_state.style_banks_full)
        p["genre_banks"] = compact_banks(st.session_state.genre_banks_full)
        # hard-lock state
        p["story_bible_edit_unlocked"] = bool(st.session_state.locks.get("story_bible_edit_unlocked", False))
    else:
        w = st.session_state.workspace
        w["title"] = st.session_state.workspace_title
        w["draft"] = st.session_state.main_text
        w["idea_bank"] = st.session_state.junk
        w["story_bible"] = story_bible_struct_from_session()
        w["voice_bible"] = voice_bible_struct_from_session()
        w["action_controls"] = action_controls_struct_from_scalars()
        w["import_controls"] = import_controls_struct_from_scalars()
        w["style_banks"] = compact_banks(st.session_state.style_banks_full)
        w["genre_banks"] = compact_banks(st.session_state.genre_banks_full)

def load_workspace_into_session() -> None:
    w = st.session_state.workspace or default_workspace()
    st.session_state.project_id = None
    st.session_state.project_title = "—"
    st.session_state.workspace_title = w.get("title","") or ""
    st.session_state.main_text = w.get("draft","") or ""
    st.session_state.junk = w.get("idea_bank","") or ""
    apply_story_bible_struct(w.get("story_bible", default_story_bible()))
    apply_voice_bible_struct(w.get("voice_bible", default_voice_bible()))
    apply_action_controls_struct(w.get("action_controls", default_action_controls()))
    apply_import_controls_struct(w.get("import_controls", default_import_controls()))
    st.session_state.style_banks_full = rebuild_banks(w.get("style_banks", default_style_banks()))
    st.session_state.genre_banks_full = rebuild_banks(w.get("genre_banks", default_genre_banks()))
    st.session_state.locks = {"story_bible_edit_unlocked": True}  # workspace editable
    st.session_state.voice_status = "NEW: (Story Bible workspace)"

def load_project_into_session(pid: str) -> None:
    p = st.session_state.projects.get(pid)
    if not p:
        return
    st.session_state.project_id = pid
    st.session_state.project_title = p.get("title","Untitled Project")
    st.session_state.workspace_title = ""  # irrelevant inside project
    st.session_state.main_text = p.get("draft","") or ""
    st.session_state.junk = p.get("idea_bank","") or ""
    apply_story_bible_struct(p.get("story_bible", default_story_bible()))
    apply_voice_bible_struct(p.get("voice_bible", default_voice_bible()))
    apply_action_controls_struct(p.get("action_controls", default_action_controls()))
    apply_import_controls_struct(p.get("import_controls", default_import_controls()))
    st.session_state.style_banks_full = rebuild_banks(p.get("style_banks", default_style_banks()))
    st.session_state.genre_banks_full = rebuild_banks(p.get("genre_banks", default_genre_banks()))
    st.session_state.locks = {"story_bible_edit_unlocked": bool(p.get("story_bible_edit_unlocked", False))}
    st.session_state.voice_status = f"{p.get('bay','')}: {st.session_state.project_title}"

def list_projects_in_bay(bay: str) -> List[Tuple[str,str]]:
    items = [(pid, p.get("title","Untitled")) for pid,p in (st.session_state.projects or {}).items() if p.get("bay")==bay]
    items.sort(key=lambda x: x[1].lower())
    return items

def ensure_active_project(bay: str) -> None:
    pid = st.session_state.active_project_by_bay.get(bay)
    if pid and pid in st.session_state.projects and st.session_state.projects[pid].get("bay")==bay:
        return
    items = list_projects_in_bay(bay)
    st.session_state.active_project_by_bay[bay] = items[0][0] if items else None

def load_context_from_bay_selection(bay: str) -> None:
    # called at top or via dispatch, safe to set widget keys
    ensure_active_project(bay)
    pid = st.session_state.active_project_by_bay.get(bay)
    if bay == "NEW" and not pid:
        load_workspace_into_session()
    elif pid:
        load_project_into_session(pid)
    else:
        # empty bay, keep a blank context
        st.session_state.project_id = None
        st.session_state.project_title = "—"
        st.session_state.main_text = ""
        st.session_state.junk = ""
        apply_story_bible_struct(default_story_bible())
        apply_voice_bible_struct(default_voice_bible())
        st.session_state.style_banks_full = rebuild_banks(default_style_banks())
        st.session_state.genre_banks_full = rebuild_banks(default_genre_banks())
        st.session_state.locks = {"story_bible_edit_unlocked": False}
        st.session_state.voice_status = f"{bay}: (empty)"

# ============================================================
# Dispatch (pre-widget) to avoid session_state mutation errors
# ============================================================
def set_dispatch(job: Dict[str, Any]) -> None:
    st.session_state._dispatch = job
    st.rerun()

def dispatch_run() -> None:
    job = st.session_state._dispatch
    if not job:
        return
    st.session_state._dispatch = None  # clear first
    typ = job.get("type","")

    try:
        if typ == "switch_bay":
            save_current_context()
            st.session_state.active_bay = job["bay"]
            load_context_from_bay_selection(job["bay"])
            st.session_state.last_action = f"Bay → {job['bay']}"
            autosave(force=True)
            return

        if typ == "select_project":
            save_current_context()
            bay = st.session_state.active_bay
            st.session_state.active_project_by_bay[bay] = job.get("pid")
            load_context_from_bay_selection(bay)
            st.session_state.last_action = "Select Context"
            autosave()
            return

        if typ == "promote":
            pid = st.session_state.project_id
            if not pid:
                st.session_state.tool_output = "Promote blocked: no project selected."
                return
            bay = st.session_state.projects[pid].get("bay")
            nxt = {"NEW":"ROUGH","ROUGH":"EDIT","EDIT":"FINAL"}.get(bay)
            if not nxt:
                st.session_state.tool_output = "Promote blocked: already FINAL."
                return
            save_current_context()
            st.session_state.projects[pid]["bay"] = nxt
            st.session_state.projects[pid]["updated_ts"] = now_ts()
            st.session_state.active_project_by_bay[nxt] = pid
            st.session_state.active_bay = nxt
            load_context_from_bay_selection(nxt)
            st.session_state.last_action = f"Promote → {nxt}"
            autosave(force=True)
            return

        if typ == "start_project":
            # From workspace to NEW project
            if st.session_state.project_id:
                st.session_state.tool_output = "Start Project is only available from workspace."
                return
            title = normalize_text(job.get("title","")) or normalize_text(st.session_state.workspace_title) or "Untitled Project"
            save_current_context()
            p = new_project_payload(title)
            # carry over workspace content
            p["draft"] = st.session_state.main_text
            p["idea_bank"] = st.session_state.junk
            p["story_bible"] = story_bible_struct_from_session()
            p["voice_bible"] = voice_bible_struct_from_session()
            p["action_controls"] = action_controls_struct_from_scalars()
            p["import_controls"] = import_controls_struct_from_scalars()
            p["style_banks"] = compact_banks(st.session_state.style_banks_full)
            p["genre_banks"] = compact_banks(st.session_state.genre_banks_full)

            # lock stamp
            p["story_bible_locked_ts"] = now_ts()
            p["story_bible_lock_reason"] = "Started from Story Bible workspace"
            p["story_bible_edit_unlocked"] = False

            st.session_state.projects[p["id"]] = p
            st.session_state.active_project_by_bay["NEW"] = p["id"]
            st.session_state.active_bay = "NEW"
            load_project_into_session(p["id"])

            # reset workspace (keep templates)
            st.session_state.workspace = default_workspace()
            load_workspace_into_session()  # safe here (still pre-widgets)
            st.session_state.last_action = "Start Project"
            autosave(force=True)
            return

        if typ == "partner_action":
            action = job.get("action","")
            run_partner_action(action)
            autosave()
            return

        if typ == "import_story_bible":
            run_import_story_bible(job.get("text",""), job.get("filename","(pasted)"))
            autosave()
            return

        if typ == "import_draft":
            run_import_draft(job.get("text",""), job.get("filename","(pasted)"))
            autosave()
            return

        if typ == "promote_ideas":
            run_promote_ideas(job.get("target","World"), job.get("selected",[]), bool(job.get("remove", False)))
            autosave()
            return

        if typ == "train_style":
            run_train_bank(kind="style", name=job.get("name","NARRATIVE"), lane=job.get("lane","Narration"), text=job.get("text",""), split=job.get("split","Paragraphs"))
            autosave()
            return

        if typ == "train_genre":
            run_train_bank(kind="genre", name=job.get("name","Romance"), lane=job.get("lane","Narration"), text=job.get("text",""), split=job.get("split","Paragraphs"))
            autosave()
            return

        if typ == "train_global_voice":
            run_train_global_voice(lane=job.get("lane","Narration"), text=job.get("text",""), split=job.get("split","Paragraphs"))
            autosave()
            return

    except Exception as e:
        st.session_state.voice_status = f"ERROR: {e}"
        st.session_state.tool_output = f"ERROR:\n{e}"

# Run dispatch before any widgets instantiate (prevents StreamlitAPIException)
dispatch_run()

# ============================================================
# Canon / lock helpers
# ============================================================
def story_bible_locked() -> bool:
    if not st.session_state.project_id:
        return False
    return not bool(st.session_state.locks.get("story_bible_edit_unlocked", False))

# ============================================================
# Import / export helpers
# ============================================================
def read_uploaded_text(upload) -> Tuple[str, str]:
    if upload is None:
        return ("", "")
    name = getattr(upload, "name", "") or ""
    suffix = name.lower().split(".")[-1] if "." in name else ""
    raw = upload.getvalue()
    if raw and len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload too large (> {MAX_UPLOAD_BYTES//1_000_000}MB).")

    if suffix in ("txt","md"):
        try:
            return (raw.decode("utf-8"), name)
        except Exception:
            return (raw.decode("latin-1", errors="ignore"), name)

    if suffix == "docx":
        try:
            from docx import Document
            import io
            f = io.BytesIO(raw)
            doc = Document(f)
            paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            return ("\n".join(paras).strip(), name)
        except Exception:
            return ("", name)

    return ("", name)

def merge_field(existing: str, new_text: str, mode: str) -> str:
    new_text = normalize_text(new_text)
    if not new_text:
        return existing or ""
    if mode == "Replace" or not (existing or "").strip():
        return new_text
    stamp = f"--- IMPORT {now_ts()} ---"
    return (existing.rstrip() + "\n\n" + stamp + "\n" + new_text).strip()

def heuristic_breakdown(text: str) -> Dict[str,str]:
    t = normalize_text(text)
    out = default_story_bible()
    if not t:
        return out
    # simple headings detection
    lines = t.splitlines()
    key = None
    heading_map = {
        "synopsis":"synopsis","summary":"synopsis","logline":"synopsis",
        "genre":"genre_style_notes","style":"genre_style_notes","tone":"genre_style_notes",
        "world":"world","setting":"world","locations":"world","location":"world",
        "characters":"characters","cast":"characters","people":"characters",
        "outline":"outline","plot":"outline","beats":"outline","structure":"outline",
    }
    def head(line: str) -> Optional[str]:
        s = line.strip().lower()
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r":\s*$","",s).strip()
        s = re.sub(r"[^a-z ]+","",s).strip()
        return heading_map.get(s)
    for ln in lines:
        h = head(ln)
        if h:
            key = h
            continue
        if key:
            out[key] += ln + "\n"
    for k in out:
        out[k] = normalize_text(out[k])
    if not any(v.strip() for v in out.values()):
        out["synopsis"] = t[:1400].strip()
    return out

def ai_breakdown(text: str, intensity_x: float) -> Dict[str,str]:
    system = (
        "You are Olivetti, a professional story-bible analyst. "
        "Return ONLY valid JSON (no markdown, no commentary). "
        "Keys: synopsis, genre_style_notes, world, characters, outline. "
        "No invention; if unknown, empty string."
    )
    user = "Break the document into Story Bible sections. Output JSON only.\n\nDOCUMENT:\n" + text
    out = call_openai(system, user, intensity_x)
    obj = safe_extract_json(out)
    b = default_story_bible()
    for k in b:
        b[k] = normalize_text(str(obj.get(k,""))) if isinstance(obj, dict) else ""
    return b

def effective_import_intensity() -> float:
    if bool(st.session_state.import_use_global):
        return clamp01(st.session_state.ai_intensity)
    return clamp01(st.session_state.import_intensity)

def run_import_story_bible(text: str, filename: str) -> None:
    if story_bible_locked():
        st.session_state.tool_output = "Import blocked: Story Bible is locked. Toggle 'Unlock Story Bible Editing'."
        st.session_state.voice_status = "Import blocked"
        return
    text = normalize_text(text)
    if not text:
        st.session_state.tool_output = "Import: no text."
        return
    use_ai = bool(st.session_state.import_use_ai) and bool(OPENAI_API_KEY)
    try:
        b = ai_breakdown(text, effective_import_intensity()) if use_ai else heuristic_breakdown(text)
        mode = st.session_state.import_merge_mode
        st.session_state.synopsis = merge_field(st.session_state.synopsis, b["synopsis"], mode)
        st.session_state.genre_style_notes = merge_field(st.session_state.genre_style_notes, b["genre_style_notes"], mode)
        st.session_state.world = merge_field(st.session_state.world, b["world"], mode)
        st.session_state.characters = merge_field(st.session_state.characters, b["characters"], mode)
        st.session_state.outline = merge_field(st.session_state.outline, b["outline"], mode)
        st.session_state.tool_output = f"Imported → Story Bible ({'AI' if use_ai else 'Heuristic'}) from {filename}."
        st.session_state.voice_status = "Import complete"
        st.session_state.last_action = "Import → Story Bible"
    except Exception as e:
        st.session_state.tool_output = f"Import ERROR:\n{e}"
        st.session_state.voice_status = "Import error"

def run_import_draft(text: str, filename: str) -> None:
    text = normalize_text(text)
    if not text:
        st.session_state.tool_output = "Import: no text."
        return
    mode = st.session_state.import_merge_mode
    st.session_state.main_text = merge_field(st.session_state.main_text, text, mode)
    st.session_state.tool_output = f"Imported → Draft ({mode}) from {filename}."
    st.session_state.voice_status = "Draft import complete"
    st.session_state.last_action = "Import → Draft"

# ============================================================
# Idea bank promotion
# ============================================================
def idea_lines(bank: str) -> List[str]:
    out = []
    seen = set()
    for ln in (bank or "").splitlines():
        s = ln.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out

def append_bullets(existing: str, bullets: List[str]) -> str:
    existing = (existing or "").rstrip()
    bullets = [b.strip() for b in bullets if b and b.strip()]
    if not bullets:
        return existing
    existing_low = existing.lower()
    uniq = []
    for b in bullets:
        if b.lower() in existing_low:
            continue
        uniq.append(b)
    if not uniq:
        return existing
    block = "\n".join([f"- {b}" if not b.startswith(("-", "•")) else b for b in uniq])
    return (existing + ("\n\n" if existing else "") + block).strip()

def run_promote_ideas(target: str, selected: List[str], remove: bool) -> None:
    if story_bible_locked() and target in ("Synopsis","Genre/Style Notes","World","Characters","Outline"):
        st.session_state.tool_output = "Promote blocked: Story Bible is locked. Toggle 'Unlock Story Bible Editing'."
        st.session_state.voice_status = "Promote blocked"
        return

    selected = [s.strip() for s in selected if s and s.strip()]
    if not selected:
        st.session_state.tool_output = "Promote: nothing selected."
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
        base = (st.session_state.main_text or "").rstrip()
        note = "\n".join([f"[IDEA → DRAFT NOTE] {s}" for s in selected])
        st.session_state.main_text = (base + ("\n\n" if base else "") + note).strip()
    else:
        st.session_state.tool_output = f"Promote: unknown target '{target}'."
        return

    if remove:
        bank_lines = (st.session_state.junk or "").splitlines()
        rm = set(selected)
        st.session_state.junk = "\n".join([ln for ln in bank_lines if ln.strip() not in rm]).strip()

    st.session_state.tool_output = f"Promoted {len(selected)} → {target}."
    st.session_state.voice_status = f"Promoted → {target}"
    st.session_state.last_action = f"Promote → {target}"

# ============================================================
# Training (engine styles + genres + global voice)
# ============================================================
def _train_split(text: str, split: str) -> List[str]:
    t = normalize_text(text)
    if not t:
        return []
    if split == "Whole":
        return [t]
    return split_paragraphs(t)

def _add_samples_to_lane(pool: List[Dict[str, Any]], samples: List[str]) -> List[Dict[str, Any]]:
    for s in samples:
        txt = _trim_sample(s)
        if len(txt) < 20:
            continue
        pool.append({"ts": now_ts(), "text": txt, "vec": hash_vec(txt)})
    pool = pool[-MAX_BANK_SAMPLES_PER_LANE:]
    return pool

def run_train_bank(kind: str, name: str, lane: str, text: str, split: str) -> None:
    text = normalize_text(text)
    if not text:
        st.session_state.tool_output = "Trainer: no text."
        return
    lane = lane if lane in LANES else "Narration"
    split = split if split in ("Paragraphs","Whole") else "Paragraphs"
    chunks = _train_split(text, split)
    if not chunks:
        st.session_state.tool_output = "Trainer: nothing to add."
        return

    if kind == "style":
        banks = st.session_state.style_banks_full
        if name not in banks:
            banks[name] = {"created_ts": now_ts(), "lanes": _default_lane_bank()}
        pool = banks[name]["lanes"][lane]
        banks[name]["lanes"][lane] = _add_samples_to_lane(pool, chunks)
        st.session_state.style_banks_full = banks
        st.session_state.tool_output = f"Added {len(chunks)} sample(s) → Style {name} / {lane}."
        st.session_state.voice_status = "Style trained"
        st.session_state.last_action = "Train Style"
        return

    if kind == "genre":
        banks = st.session_state.genre_banks_full
        if name not in banks:
            banks[name] = {"created_ts": now_ts(), "lanes": _default_lane_bank()}
        pool = banks[name]["lanes"][lane]
        banks[name]["lanes"][lane] = _add_samples_to_lane(pool, chunks)
        st.session_state.genre_banks_full = banks
        st.session_state.tool_output = f"Added {len(chunks)} sample(s) → Genre {name} / {lane}."
        st.session_state.voice_status = "Genre trained"
        st.session_state.last_action = "Train Genre"
        return

def run_train_global_voice(lane: str, text: str, split: str) -> None:
    text = normalize_text(text)
    if not text:
        st.session_state.tool_output = "Global Voice: no text."
        return
    lane = lane if lane in LANES else "Narration"
    chunks = _train_split(text, split)
    gv = st.session_state.global_voice_full
    pool = gv["lanes"][lane]
    gv["lanes"][lane] = _add_samples_to_lane(pool, chunks)
    st.session_state.global_voice_full = gv
    st.session_state.global_voice = compact_global_voice(gv)
    st.session_state.tool_output = f"Added {len(chunks)} sample(s) → Global Voice / {lane}."
    st.session_state.voice_status = "Global voice trained"
    st.session_state.last_action = "Train Global Voice"

# ============================================================
# Partner action (AI + deterministic fallbacks)
# ============================================================
def action_enabled(action: str) -> bool:
    return bool(st.session_state.get(f"ac__{action}__enabled", True))

def effective_intensity_for_action(action: str) -> float:
    global_x = clamp01(st.session_state.ai_intensity)
    use_global = bool(st.session_state.get(f"ac__{action}__use_global", True))
    if use_global:
        return global_x
    return clamp01(st.session_state.get(f"ac__{action}__intensity", global_x))

def local_cleanup(text: str) -> str:
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
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
    targets = [
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
    hits = []
    for label, txt in targets:
        if not (txt or "").strip():
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
        out += f"\n\n(+{len(hits)-cap} more hits)"
    return out

def story_bible_text() -> str:
    parts = []
    if (st.session_state.synopsis or "").strip():
        parts.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if (st.session_state.genre_style_notes or "").strip():
        parts.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if (st.session_state.world or "").strip():
        parts.append(f"WORLD:\n{st.session_state.world.strip()}")
    if (st.session_state.characters or "").strip():
        parts.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if (st.session_state.outline or "").strip():
        parts.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
    return "\n\n".join(parts).strip() if parts else "— None provided —"

def build_brief(action: str, lane: str, intensity_x: float) -> str:
    intensity_x = clamp01(intensity_x)

    # voice bible controls text
    vb_lines = []
    if st.session_state.vb_style_on:
        vb_lines.append(f"Writing Style: {st.session_state.writing_style} (intensity {float(st.session_state.style_intensity):.2f})")
    if st.session_state.vb_genre_on:
        vb_lines.append(f"Genre: {st.session_state.genre} (intensity {float(st.session_state.genre_intensity):.2f})")
    if st.session_state.vb_pov_on:
        vb_lines.append(f"POV: {st.session_state.pov} (strength {float(st.session_state.pov_strength):.2f})")
    if st.session_state.vb_tense_on:
        vb_lines.append(f"Tense: {st.session_state.tense} (strength {float(st.session_state.tense_strength):.2f})")
    if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
        vb_lines.append(f"Match Sample (intensity {float(st.session_state.match_intensity):.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and (st.session_state.voice_lock_prompt or "").strip():
        vb_lines.append(f"VOICE LOCK (strength {float(st.session_state.lock_intensity):.2f}):\n{st.session_state.voice_lock_prompt.strip()}")

    # Engine style exemplars
    style_ex = []
    style_dir = ""
    if st.session_state.vb_style_on and st.session_state.writing_style in ENGINE_STYLES:
        style_dir = engine_style_directive(st.session_state.writing_style, float(st.session_state.style_intensity), lane)
        ctx = (st.session_state.main_text or "")[-2500:] or (st.session_state.synopsis or "")
        style_ex = retrieve_from_bank(st.session_state.style_banks_full, st.session_state.writing_style, lane, ctx, k=2)

    # Engine genre exemplars
    genre_ex = []
    genre_dir = ""
    if st.session_state.vb_genre_on and st.session_state.genre in ENGINE_GENRES:
        genre_dir = engine_genre_directive(st.session_state.genre, float(st.session_state.genre_intensity), lane)
        ctx = (st.session_state.main_text or "")[-2500:] or (st.session_state.synopsis or "")
        genre_ex = retrieve_from_bank(st.session_state.genre_banks_full, st.session_state.genre, lane, ctx, k=2)

    # Global voice exemplars (if enabled globally + per-project)
    gv_dir = ""
    gv_ex = []
    gv_full = st.session_state.global_voice_full
    if bool(gv_full.get("enabled", False)) and bool(st.session_state.use_global_voice):
        strength = clamp01(gv_full.get("strength", 0.65) * float(st.session_state.global_voice_strength))
        gv_dir = f"GLOBAL VOICE: enabled (effective strength {strength:.2f}). Mimic cadence/diction; never copy content."
        ctx = (st.session_state.main_text or "")[-2500:] or (st.session_state.synopsis or "")
        gv_ex = retrieve_from_global_voice(gv_full, lane, ctx, k=2)

    # Assemble
    ex_blocks = []
    if gv_ex:
        ex_blocks.append("GLOBAL VOICE EXEMPLARS:\n" + "\n\n---\n\n".join(gv_ex))
    if style_ex:
        ex_blocks.append("ENGINE STYLE EXEMPLARS:\n" + "\n\n---\n\n".join(style_ex))
    if genre_ex:
        ex_blocks.append("ENGINE GENRE EXEMPLARS:\n" + "\n\n---\n\n".join(genre_ex))
    exemplar_text = "\n\n".join(ex_blocks).strip() if ex_blocks else "— None —"

    pov_dir = ""
    tense_dir = ""
    if st.session_state.vb_pov_on:
        pov_dir = f"POV CONSTRAINT: {st.session_state.pov} (strength {float(st.session_state.pov_strength):.2f})."
    if st.session_state.vb_tense_on:
        tense_dir = f"TENSE CONSTRAINT: {st.session_state.tense} (strength {float(st.session_state.tense_strength):.2f})."
    directives = "\n".join([d for d in [gv_dir, style_dir, genre_dir, pov_dir, tense_dir] if d]).strip() or "— None —"
    voice_controls = "\n".join(vb_lines).strip() if vb_lines else "— None enabled —"

    return f"""
YOU ARE OLIVETTI: the author's professional writing engine.
No UI talk. No process talk.

STORY BIBLE is project-specific canon. Never contradict canon.
IDEA BANK supports, not canon unless promoted.

LANE: {lane}
ACTION: {action}

EFFECTIVE INTENSITY: {intensity_x:.2f}
PROFILE: {intensity_profile(intensity_x)}

DIRECTIVES:
{directives}

VOICE BIBLE SETTINGS:
{voice_controls}

EXEMPLARS (mimic patterns, not content):
{exemplar_text}

STORY BIBLE:
{story_bible_text()}

IDEA BANK:
{(st.session_state.junk or '').strip() or '— None —'}
""".strip()

def run_partner_action(action: str) -> None:
    if action not in ALL_ACTIONS:
        return
    if not action_enabled(action):
        st.session_state.tool_output = f"{action} is disabled in Action Controls."
        st.session_state.voice_status = f"{action}: disabled"
        return

    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    intensity_x = effective_intensity_for_action(action)
    brief = build_brief(action, lane, intensity_x)

    try:
        if action == "Find":
            st.session_state.tool_output = "Use /find: term in the Idea Bank (Junk Drawer), or the search box below."
            st.session_state.last_action = "Find"
            return

        use_ai = bool(OPENAI_API_KEY)

        if action == "Write":
            if not use_ai:
                st.session_state.tool_output = "Write requires OPENAI_API_KEY."
                return
            task = f"Continue decisively in lane ({lane}). Add 1–3 paragraphs that advance the scene. No recap. Just prose."
            out = call_openai(brief, task + "\n\nTEXT:\n" + (text.strip() or "Start the opening."), intensity_x)
            if out:
                st.session_state.main_text = (text.rstrip() + ("\n\n" if text.strip() else "") + out.strip()).strip()
            st.session_state.last_action = "Write"
            st.session_state.voice_status = "Write complete"
            return

        if action in ("Rewrite","Expand","Rephrase","Describe","Spell","Grammar"):
            if not use_ai:
                # deterministic fallback
                st.session_state.main_text = local_cleanup(text)
                st.session_state.tool_output = f"{action}: local cleanup (no API key)."
                st.session_state.last_action = action
                return

            task_map = {
                "Rewrite": f"Rewrite for professional quality in lane ({lane}). Preserve meaning and canon. Return full revised text.",
                "Expand": f"Expand with meaningful depth in lane ({lane}). No padding. Preserve canon. Return full revised text.",
                "Rephrase": f"Rewrite the final paragraph for maximum strength (same meaning) in lane ({lane}). Return full text.",
                "Describe": f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text.",
                "Spell": "Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text.",
                "Grammar": "Copyedit grammar/punctuation and clean sentence flow. Preserve voice. Return full revised text.",
            }
            out = call_openai(brief, task_map[action] + "\n\nTEXT:\n" + (text.strip() or "—"), intensity_x)
            if out:
                st.session_state.main_text = out.strip()
            st.session_state.last_action = action
            st.session_state.voice_status = f"{action} complete"
            return

        if action in ("Synonym","Sentence"):
            if not use_ai:
                st.session_state.tool_output = f"{action}: requires OPENAI_API_KEY."
                return
            if action == "Synonym":
                task = "Provide 10 strong synonym options for the single most important verb in the final paragraph. Output bullet list only."
            else:
                task = f"Generate 8 alternative sentences that could replace the final sentence, same meaning, lane ({lane}). Return numbered list."
            out = call_openai(brief, task + "\n\nTEXT:\n" + (text[-1200:].strip() or "—"), intensity_x)
            st.session_state.tool_output = out
            st.session_state.last_action = action
            st.session_state.voice_status = f"{action} complete"
            return

    except Exception as e:
        st.session_state.voice_status = f"Engine error"
        st.session_state.tool_output = f"ERROR:\n{e}"

# ============================================================
# Header / status
# ============================================================
top = st.container()
with top:
    cols = st.columns([1,1,1,1,2.2])
    if cols[0].button("🆕 New", key="bay_new"):
        set_dispatch({"type":"switch_bay","bay":"NEW"})
    if cols[1].button("✏️ Rough", key="bay_rough"):
        set_dispatch({"type":"switch_bay","bay":"ROUGH"})
    if cols[2].button("🛠 Edit", key="bay_edit"):
        set_dispatch({"type":"switch_bay","bay":"EDIT"})
    if cols[3].button("✅ Final", key="bay_final"):
        set_dispatch({"type":"switch_bay","bay":"FINAL"})
    cols[4].markdown(
        f"""
        <div style='text-align:right;font-size:12px;opacity:.95;'>
          Bay: <b>{st.session_state.active_bay}</b> •
          Project: <b>{st.session_state.project_title}</b> •
          Autosave: {st.session_state.autosave_time or "—"}<br/>
          Last Action: {st.session_state.last_action} • Status: {st.session_state.voice_status}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ============================================================
# Layout columns (locked)
# ============================================================
left, center, right = st.columns([1.25, 3.2, 1.65])

# ============================================================
# LEFT — Story Bible + pipeline + import/export + idea bank
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    bay = st.session_state.active_bay
    projects = list_projects_in_bay(bay)
    if bay == "NEW":
        labels = ["— (Story Bible workspace) —"] + [t for _,t in projects]
        ids = [None] + [pid for pid,_ in projects]
    else:
        labels = ["— (none) —"] + [t for _,t in projects]
        ids = [None] + [pid for pid,_ in projects]

    current_pid = st.session_state.project_id if st.session_state.project_id in ids else None
    idx = ids.index(current_pid) if current_pid in ids else 0

    sel = st.selectbox("Current Bay Project", labels, index=idx, key="sel_project")
    sel_pid = ids[labels.index(sel)]

    if sel_pid != st.session_state.project_id:
        set_dispatch({"type":"select_project","pid": sel_pid})

    # Workspace title + Start Project
    if bay == "NEW" and not st.session_state.project_id:
        st.text_input("Workspace Title", key="workspace_title")
        if st.button("Start Project", key="btn_start_project", type="primary"):
            set_dispatch({"type":"start_project","title": st.session_state.workspace_title})

    # Promote button (if in a project)
    if st.session_state.project_id and st.session_state.active_bay in ("NEW","ROUGH","EDIT"):
        nxt = {"NEW":"ROUGH","ROUGH":"EDIT","EDIT":"FINAL"}[st.session_state.active_bay]
        if st.button(f"Promote → {nxt}", key="btn_promote", type="secondary"):
            set_dispatch({"type":"promote"})

    # Global AI intensity
    st.slider("AI Intensity", 0.0, 1.0, key="ai_intensity")

    # Hard-lock toggle for Story Bible editing (projects only)
    if st.session_state.project_id:
        unlocked = st.checkbox(
            "Unlock Story Bible Editing",
            value=bool(st.session_state.locks.get("story_bible_edit_unlocked", False)),
            help="Hard Lock: ON by default. Toggle ON to edit canon / import to canon / promote to canon.",
            key="sb_unlock_toggle",
        )
        st.session_state.locks["story_bible_edit_unlocked"] = bool(unlocked)

    with st.expander("📦 Import / Export", expanded=False):
        st.caption("Import into Draft or Story Bible. Export Draft/Story Bible and JSON bundles.")

        up = st.file_uploader("Upload (.txt .md .docx)", type=["txt","md","docx"], key="imp_upload")
        paste = st.text_area("Or paste text", key="import_paste", height=120, label_visibility="collapsed")

        st.checkbox("Use AI breakdown (Story Bible)", key="import_use_ai")
        st.checkbox("Use Global Intensity", key="import_use_global")
        st.slider("Import Intensity Override", 0.0, 1.0, key="import_intensity", disabled=bool(st.session_state.import_use_global))
        st.selectbox("Merge Mode", ["Append","Replace"], key="import_merge_mode")

        colA, colB = st.columns(2)
        if colA.button("Import → Draft", key="btn_imp_draft", type="secondary"):
            txt, name = read_uploaded_text(up) if up else ("","")
            src = normalize_text(paste) if paste.strip() else txt
            set_dispatch({"type":"import_draft","text": src, "filename": name or "(pasted)"})
        if colB.button("Import → Story Bible", key="btn_imp_sb", type="secondary"):
            txt, name = read_uploaded_text(up) if up else ("","")
            src = normalize_text(paste) if paste.strip() else txt
            set_dispatch({"type":"import_story_bible","text": src, "filename": name or "(pasted)"})

        st.divider()

        # Export helpers
        def export_story_bible_md() -> str:
            sb = story_bible_struct_from_session()
            return "\n\n".join([
                "# Story Bible",
                "## Synopsis\n" + (sb["synopsis"] or "").strip(),
                "## Genre / Style Notes\n" + (sb["genre_style_notes"] or "").strip(),
                "## World\n" + (sb["world"] or "").strip(),
                "## Characters\n" + (sb["characters"] or "").strip(),
                "## Outline\n" + (sb["outline"] or "").strip(),
            ]).strip() + "\n"

        def export_project_bundle(pid: Optional[str]) -> str:
            save_current_context()
            if pid and pid in st.session_state.projects:
                data = {"type":"project_bundle", "exported_at": now_ts(), "project": st.session_state.projects[pid], "global_voice": compact_global_voice(st.session_state.global_voice_full)}
            else:
                data = {"type":"library_bundle", "exported_at": now_ts(), "projects": st.session_state.projects, "workspace": st.session_state.workspace, "active_project_by_bay": st.session_state.active_project_by_bay, "global_voice": compact_global_voice(st.session_state.global_voice_full)}
            return json.dumps(data, ensure_ascii=False, indent=2)

        st.download_button("Export Draft (.txt)", data=(st.session_state.main_text or ""), file_name="draft.txt", mime="text/plain")
        st.download_button("Export Draft (.md)", data="# Draft\n\n" + (st.session_state.main_text or ""), file_name="draft.md", mime="text/markdown")
        st.download_button("Export Story Bible (.md)", data=export_story_bible_md(), file_name="story_bible.md", mime="text/markdown")
        st.download_button("Export Project Bundle (.json)", data=export_project_bundle(st.session_state.project_id), file_name="project_bundle.json", mime="application/json")
        st.download_button("Export Full Library (.json)", data=export_project_bundle(None), file_name="olivetti_library.json", mime="application/json")

        st.divider()
        st.caption("Import Bundle (.json) merges in safely — never wipes.")
        bun = st.file_uploader("Import Bundle (.json)", type=["json"], key="imp_bundle")
        if st.button("Import Bundle NOW", key="btn_import_bundle", type="primary"):
            if not bun:
                st.session_state.tool_output = "Bundle import: no file."
            else:
                raw = bun.getvalue()
                if raw and len(raw) > MAX_UPLOAD_BYTES:
                    st.session_state.tool_output = "Bundle import: file too large."
                else:
                    try:
                        obj = json.loads(raw.decode("utf-8"))
                        typ = obj.get("type","")
                        if typ == "project_bundle":
                            p = obj.get("project", {})
                            if not isinstance(p, dict) or not p.get("id"):
                                raise ValueError("Invalid project bundle.")
                            st.session_state.projects[p["id"]] = p
                            st.session_state.tool_output = f"Imported project bundle: {p.get('title','')}."
                        elif typ == "library_bundle":
                            projs = obj.get("projects", {})
                            if isinstance(projs, dict):
                                st.session_state.projects.update(projs)
                            ws = obj.get("workspace")
                            if isinstance(ws, dict):
                                st.session_state.workspace = ws
                            apbb = obj.get("active_project_by_bay")
                            if isinstance(apbb, dict):
                                for b in BAYS:
                                    apbb.setdefault(b, None)
                                st.session_state.active_project_by_bay = apbb
                            gv = obj.get("global_voice")
                            if isinstance(gv, dict):
                                st.session_state.global_voice_full = rebuild_global_voice(gv)
                                st.session_state.global_voice = compact_global_voice(st.session_state.global_voice_full)
                            st.session_state.tool_output = "Imported full library bundle."
                        else:
                            raise ValueError("Unknown bundle type.")
                        autosave(force=True)
                        st.rerun()
                    except Exception as e:
                        st.session_state.tool_output = f"Bundle import error:\n{e}"

    with st.expander("🧠 Idea Bank (Junk Drawer)", expanded=False):
        st.text_area("", key="junk", height=140, label_visibility="collapsed")
        ideas = idea_lines(st.session_state.junk or "")
        if ideas:
            selected = st.multiselect("Select idea line(s)", options=ideas, key="promote_selected")
            cols = st.columns([1.2,1.2,1.6])
            target = cols[0].selectbox("Target", ["Synopsis","Genre/Style Notes","World","Characters","Outline","Draft"], key="promote_target")
            remove = cols[1].checkbox("Remove from Idea Bank", key="promote_remove")
            if cols[2].button("Promote Selected → Target", key="btn_promote_selected", type="secondary"):
                set_dispatch({"type":"promote_ideas","target": target, "selected": selected, "remove": remove})
        st.markdown("**Search**")
        term = st.text_input("Find term", key="find_term", label_visibility="collapsed")
        if st.button("Find", key="btn_find_local", type="secondary"):
            st.session_state.tool_output = local_find(term)

        st.markdown("**Tool Output**")
        st.code(st.session_state.tool_output or "", language="text")

    # Story Bible editors (lockable)
    disabled = story_bible_locked()
    with st.expander("📝 Synopsis", expanded=False):
        st.text_area("", key="synopsis", height=120, disabled=disabled, label_visibility="collapsed")
    with st.expander("🎭 Genre / Style Notes", expanded=False):
        st.text_area("", key="genre_style_notes", height=120, disabled=disabled, label_visibility="collapsed")
    with st.expander("🌍 World", expanded=False):
        st.text_area("", key="world", height=160, disabled=disabled, label_visibility="collapsed")
    with st.expander("👤 Characters", expanded=False):
        st.text_area("", key="characters", height=160, disabled=disabled, label_visibility="collapsed")
    with st.expander("🧱 Outline", expanded=False):
        st.text_area("", key="outline", height=200, disabled=disabled, label_visibility="collapsed")

# ============================================================
# CENTER — Writing Desk (linked)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    if st.session_state.project_id:
        p = st.session_state.projects.get(st.session_state.project_id, {})
        st.caption(
            f"Linked To: **{st.session_state.active_bay} / {st.session_state.project_title}** "
            f"• Bible ID: **{p.get('story_bible_id','—')}** "
            f"• Created: **{p.get('story_bible_created_ts','—')}** "
            f"• Locked: **{p.get('story_bible_locked_ts','—') or '—'}**"
        )
    else:
        w = st.session_state.workspace
        # Workspace gets its own deterministic bible id for clarity
        wid = st.session_state.workspace.get("workspace_bible_id")
        if not wid:
            wid = hashlib.md5(("workspace|" + now_ts()).encode("utf-8")).hexdigest()[:12]
            st.session_state.workspace["workspace_bible_id"] = wid
            st.session_state.workspace["workspace_bible_created_ts"] = now_ts()
        st.caption(
            f"Workspace Story Bible (not linked yet) • Bible ID: **{wid}** • Created: {st.session_state.workspace.get('workspace_bible_created_ts','—')}"
        )

    if not st.session_state.project_id:
        with st.expander("⚙ Project Controls (from the desk)", expanded=False):
            st.caption("You are in the Story Bible workspace. Start a project to lock this Bible to a NEW project.")
            if "desk_workspace_title" not in st.session_state:
                st.session_state.desk_workspace_title = st.session_state.workspace_title

            def _sync_desk_title():
                st.session_state.workspace_title = st.session_state.desk_workspace_title

            st.text_input("Project Title", key="desk_workspace_title", on_change=_sync_desk_title)
            if st.button("Start Project NOW (from desk)", key="btn_start_project_desk", type="primary"):
                set_dispatch({"type":"start_project","title": st.session_state.workspace_title})

    with st.expander("📌 Story Bible Dock (read-only)", expanded=False):
        tabs = st.tabs(["Synopsis","Genre/Style","World","Characters","Outline"])
        tabs[0].text_area("Synopsis", value=st.session_state.synopsis or "", height=150, disabled=True, label_visibility="collapsed")
        tabs[1].text_area("Genre/Style", value=st.session_state.genre_style_notes or "", height=150, disabled=True, label_visibility="collapsed")
        tabs[2].text_area("World", value=st.session_state.world or "", height=150, disabled=True, label_visibility="collapsed")
        tabs[3].text_area("Characters", value=st.session_state.characters or "", height=150, disabled=True, label_visibility="collapsed")
        tabs[4].text_area("Outline", value=st.session_state.outline or "", height=150, disabled=True, label_visibility="collapsed")

    # Draft editor
    st.text_area("", key="main_text", height=680, label_visibility="collapsed")

    # Action buttons (dispatch to avoid session_state mutation after widgets)
    row1 = st.columns(5)
    for i, a in enumerate(ACTIONS_PRIMARY):
        if row1[i].button(a, key=f"btn_{a.lower()}", type="primary"):
            set_dispatch({"type":"partner_action","action": a})

    row2 = st.columns(5)
    for i, a in enumerate(ACTIONS_SECONDARY):
        if row2[i].button(a, key=f"btn_{a.lower()}", type="secondary"):
            set_dispatch({"type":"partner_action","action": a})

# ============================================================
# RIGHT — Voice Bible + Training + Action Controls
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    # Writing style
    st.checkbox("Enable Writing Style", key="vb_style_on")
    st.selectbox("Writing Style", ENGINE_STYLES + ["Neutral","Minimal","Expressive","Hardboiled","Poetic"], key="writing_style", disabled=not st.session_state.vb_style_on)
    st.slider("Style Intensity", 0.0, 1.0, key="style_intensity", disabled=not st.session_state.vb_style_on)

    with st.expander("🎨 Style Trainer (Engine Styles)", expanded=False):
        st.caption("Train NARRATIVE / DESCRIPTIVE / EMOTIONAL / LYRICAL with your own text. Project-specific.")
        up = st.file_uploader("Upload training doc (.txt .md .docx)", type=["txt","md","docx"], key="style_train_upload")
        st.text_area("Or paste training text", key="style_train_text", height=120)
        st.selectbox("Style Bank", ENGINE_STYLES, key="style_train_style")
        st.selectbox("Lane", LANES, key="style_train_lane")
        st.selectbox("Split Mode", ["Paragraphs","Whole"], key="style_train_split")
        if st.button("Add Samples → Style Bank", key="btn_train_style", type="primary"):
            txt, name = read_uploaded_text(up) if up else ("","")
            src = normalize_text(st.session_state.style_train_text) if st.session_state.style_train_text.strip() else txt
            set_dispatch({"type":"train_style","name": st.session_state.style_train_style, "lane": st.session_state.style_train_lane, "text": src, "split": st.session_state.style_train_split})

    st.divider()

    # Genre influence
    st.checkbox("Enable Genre Influence", key="vb_genre_on")
    st.selectbox("Genre", ENGINE_GENRES + ["Literary","Noir","Thriller(alt)","Comedy(alt)"], key="genre", disabled=not st.session_state.vb_genre_on)
    st.slider("Genre Intensity", 0.0, 1.0, key="genre_intensity", disabled=not st.session_state.vb_genre_on)

    with st.expander("🧬 Genre Trainer (Engine Genres)", expanded=False):
        st.caption("Train Romance / Thriller / Fantasy / Science Fiction / Comedy with your own text. Project-specific.")
        up = st.file_uploader("Upload training doc (.txt .md .docx)", type=["txt","md","docx"], key="genre_train_upload")
        st.text_area("Or paste training text", key="genre_train_text", height=120)
        st.selectbox("Genre Bank", ENGINE_GENRES, key="genre_train_genre")
        st.selectbox("Lane", LANES, key="genre_train_lane")
        st.selectbox("Split Mode", ["Paragraphs","Whole"], key="genre_train_split")
        if st.button("Add Samples → Genre Bank", key="btn_train_genre", type="primary"):
            txt, name = read_uploaded_text(up) if up else ("","")
            src = normalize_text(st.session_state.genre_train_text) if st.session_state.genre_train_text.strip() else txt
            set_dispatch({"type":"train_genre","name": st.session_state.genre_train_genre, "lane": st.session_state.genre_train_lane, "text": src, "split": st.session_state.genre_train_split})

    st.divider()

    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area("Style Example", key="voice_sample", height=120, disabled=not st.session_state.vb_match_on)
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity", disabled=not st.session_state.vb_match_on)

    st.divider()

    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on")
    st.text_area("Voice Lock Prompt", key="voice_lock_prompt", height=100, disabled=not st.session_state.vb_lock_on)
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity", disabled=not st.session_state.vb_lock_on)

    st.divider()

    
    st.checkbox("Enforce POV", key="vb_pov_on")
    st.selectbox("POV", ["First","Close Third","Omniscient"], key="pov", disabled=not st.session_state.vb_pov_on)
    st.slider("POV Strength", 0.0, 1.0, key="pov_strength", disabled=not st.session_state.vb_pov_on)

    st.divider()

    st.checkbox("Enforce Tense", key="vb_tense_on")
    st.selectbox("Tense", ["Past","Present"], key="tense", disabled=not st.session_state.vb_tense_on)
    st.slider("Tense Strength", 0.0, 1.0, key="tense_strength", disabled=not st.session_state.vb_tense_on)


    st.divider()

    # Global voice (optional master + per-project toggle)
    with st.expander("🌐 Global Voice (optional)", expanded=False):
        gv = st.session_state.global_voice_full
        enabled = st.checkbox("Enable Global Voice (master)", value=bool(gv.get("enabled", False)), key="gv_enabled")
        strength = st.slider("Global Voice Strength", 0.0, 1.0, value=float(gv.get("strength", 0.65)), key="gv_strength")
        gv["enabled"] = bool(enabled)
        gv["strength"] = clamp01(strength)
        st.session_state.global_voice_full = gv
        st.session_state.global_voice = compact_global_voice(gv)

        if st.session_state.project_id:
            st.checkbox("Use Global Voice (this project)", key="use_global_voice")
            st.slider("Project Global Voice Mix", 0.0, 1.0, key="global_voice_strength")
        else:
            st.caption("Per-project toggle appears inside projects (not workspace).")

        st.divider()
        st.caption("Train Global Voice with your own text (affects all projects that enable it).")
        up = st.file_uploader("Upload training doc", type=["txt","md","docx"], key="gv_upload")
        gv_text = st.text_area("Or paste training text", key="gv_paste", height=110)
        gv_lane = st.selectbox("Lane", LANES, key="gv_lane")
        gv_split = st.selectbox("Split Mode", ["Paragraphs","Whole"], key="gv_split")
        if st.button("Add Samples → Global Voice", key="btn_train_gv", type="primary"):
            txt, name = read_uploaded_text(up) if up else ("","")
            src = normalize_text(gv_text) if gv_text.strip() else txt
            set_dispatch({"type":"train_global_voice","lane": gv_lane, "text": src, "split": gv_split})

    # Action Controls
    with st.expander("🧰 Action Controls (Per Button)", expanded=False):
        st.checkbox("Lock Action Controls (this context)", key="ac_locked")
        locked = bool(st.session_state.ac_locked)
        st.caption("Each button has Enable + Use Global Intensity + Override Intensity.")

        st.markdown("**Primary Buttons**")
        for a in ACTIONS_PRIMARY:
            c = st.columns([1.2, 1.0, 1.6])
            c[0].checkbox(f"{a} Enabled", key=f"ac__{a}__enabled", disabled=locked)
            c[1].checkbox("Use Global", key=f"ac__{a}__use_global", disabled=locked)
            c[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=f"ac__{a}__intensity",
                disabled=locked or bool(st.session_state.get(f"ac__{a}__use_global", True)),
            )

        st.markdown("**Secondary Buttons**")
        for a in ACTIONS_SECONDARY:
            c = st.columns([1.2, 1.0, 1.6])
            c[0].checkbox(f"{a} Enabled", key=f"ac__{a}__enabled", disabled=locked)
            c[1].checkbox("Use Global", key=f"ac__{a}__use_global", disabled=locked)
            c[2].slider(
                "Intensity Override",
                0.0, 1.0,
                key=f"ac__{a}__intensity",
                disabled=locked or bool(st.session_state.get(f"ac__{a}__use_global", True)),
            )

# ============================================================
# End-of-run autosave (safe & cheap)
# ============================================================
autosave()

