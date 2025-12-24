set -euo pipefail

# 1) requirements.txt
cat > requirements.txt <<'EOF'
streamlit>=1.52.0
openai>=2.0.0
python-dotenv>=1.0.1
EOF

# 2) app.py one-shot transformation
python3 - <<'PY'
from __future__ import annotations
import re
from pathlib import Path

app = Path("app.py")
if not app.exists():
    raise SystemExit("ERROR: app.py not found (run this from your repo root).")

s = app.read_text(encoding="utf-8")

# Remove import-time OpenAI client creation (must be lazy)
s = re.sub(r"^\s*client\s*=\s*OpenAI\(\)\s*\n", "", s, flags=re.M)

# Ensure list_projects has stage default
s = re.sub(
    r'meta\s*=\s*read_json\(\s*p\s*/\s*"meta\.json"\s*,\s*\{\s*"title"\s*:\s*p\.name\s*\}\s*\)\s*',
    'meta = read_json(p / "meta.json", {"title": p.name, "stage": "New"})',
    s,
)

marker = "# -----------------------------\n# Streamlit UI\n# -----------------------------\n"
idx = s.find(marker)
if idx == -1:
    raise SystemExit("ERROR: Could not find the Streamlit UI marker block in app.py")

LOCKED_UI = r'''# -----------------------------
# Streamlit UI (LOCKED LAYOUT)
# -----------------------------
st.set_page_config(page_title="Olivetti", layout="wide")

STAGES = ["New", "Rough", "Edit", "Final"]

projects = list_projects()

# Stage selection
if "stage" not in st.session_state:
    st.session_state.stage = "New"
if st.session_state.stage not in STAGES:
    st.session_state.stage = "New"

# Top bar: stages + project picker + create
with st.container():
    c_stage, c_proj, c_new = st.columns([2.2, 5.0, 2.0])

    st.session_state.stage = c_stage.radio(
        "Stage",
        STAGES,
        index=STAGES.index(st.session_state.stage),
        horizontal=True,
        label_visibility="collapsed",
        key="stage_radio",
    )

    stage_pids = [
        pid for pid, meta in (projects or {}).items()
        if (meta or {}).get("stage", "New") == st.session_state.stage
    ]
    selectable_pids = stage_pids if stage_pids else list((projects or {}).keys())

    if "pid" not in st.session_state or st.session_state.pid not in (projects or {}):
        st.session_state.pid = selectable_pids[0] if selectable_pids else None

    with c_new.expander("New Project", expanded=False):
        new_title = st.text_input("Title", value="New Story", key="new_project_title")
        if st.button("Create Project", key="btn_create_project"):
            pid_new = new_project_id(new_title)
            save_project(
                pid_new,
                meta={"title": new_title, "stage": st.session_state.stage},
                story_bible={},
                voice_bible={},
                doc="",
                settings=default_settings(),
                history=[],
            )
            st.session_state.pid = pid_new
            st.rerun()  # allowed

    if not projects:
        st.info("Create a project to begin.")
        st.stop()

    pid = c_proj.selectbox(
        "Project",
        options=selectable_pids,
        format_func=lambda x: projects.get(x, {}).get("title", x),
        index=selectable_pids.index(st.session_state.pid) if st.session_state.pid in selectable_pids else 0,
        label_visibility="collapsed",
        key="project_select",
    )

# Load project
data = load_project(pid)
meta = data["meta"]
story_bible = data["story_bible"]
voice_bible = data["voice_bible"]
doc = data["doc"]
history: List[Dict[str, Any]] = data["history"]
settings = normalize_settings(data["settings"])

# Ensure meta/stage exists for older projects
if not isinstance(meta, dict):
    meta = {"title": pid}
if meta.get("stage") not in STAGES:
    meta["stage"] = "New"
    save_project(pid, meta=meta)

# Header row: title + model + lock + desk height
with st.container():
    h1, h2, h3, h4 = st.columns([3.2, 2.0, 1.6, 1.6])
    h1.markdown(f"### {meta.get('title', pid)}")
    settings["model"] = h2.text_input("Model", value=settings.get("model", DEFAULT_MODEL), key=f"model_{pid}")
    settings["locked"] = h3.toggle("Lock AI controls", value=bool(settings.get("locked", False)), key=f"locked_{pid}")

    if "desk_height" not in st.session_state:
        st.session_state.desk_height = 420
    st.session_state.desk_height = int(
        h4.slider("Desk height", 250, 1200, int(st.session_state.desk_height), 50, key="desk_height_slider")
    )

# Save settings immediately (no rerun)
save_project(pid, settings=settings)

# LOCKED 3-column layout (desk stays centered)
left, center, right = st.columns([1.1, 2.2, 1.1])

with left:
    st.subheader("Project")
    new_title2 = st.text_input("Project title", value=meta.get("title", pid), key=f"title_{pid}")
    cA, cB = st.columns(2)
    with cA:
        if st.button("Save title", key=f"btn_save_title_{pid}"):
            meta["title"] = new_title2
            save_project(pid, meta=meta)
            st.success("Saved.")
            st.rerun()  # allowed
    with cB:
        new_stage = st.selectbox("Move to stage", STAGES, index=STAGES.index(meta.get("stage", "New")), key=f"move_stage_{pid}")
        if st.button("Move", key=f"btn_move_stage_{pid}"):
            meta["stage"] = new_stage
            save_project(pid, meta=meta)
            st.success(f"Moved to {new_stage}.")

    st.markdown("---")
    st.subheader("Story Bible")
    story_bible["world"] = st.text_area("World", value=story_bible.get("world", ""), height=110, key=f"sb_world_{pid}")
    story_bible["outline"] = st.text_area("Outline / beats", value=story_bible.get("outline", ""), height=110, key=f"sb_outline_{pid}")
    story_bible["guardrails"] = st.text_area("Guardrails (no-go rules)", value=story_bible.get("guardrails", ""), height=90, key=f"sb_guard_{pid}")
    story_bible["characters"] = st.text_area(
        "Characters (freeform / JSON-ish ok)",
        value=str(story_bible.get("characters", "")),
        height=110,
        key=f"sb_chars_{pid}",
    )
    if st.button("Save Story Bible", key=f"btn_save_sb_{pid}"):
        save_project(pid, story_bible=story_bible)
        st.success("Saved.")

    st.markdown("---")
    st.subheader("AI Button Controls")
    for label, key, _desc in ACTIONS:
        with st.expander(label, expanded=False):
            settings["actions"][key]["enabled"] = st.toggle(
                f"{label} enabled",
                value=bool(settings["actions"][key]["enabled"]),
                key=f"en_{pid}_{key}",
            )
            settings["actions"][key]["intensity"] = st.slider(
                f"{label} intensity",
                0.0,
                1.0,
                float(settings["actions"][key]["intensity"]),
                0.05,
                key=f"in_{pid}_{key}",
            )
    save_project(pid, settings=settings)

with center:
    st.subheader("Writing Desk")
    doc = st.text_area("Scene / Draft", value=doc, height=int(st.session_state.desk_height), key=f"doc_{pid}")
    selection = st.text_area("Selection (paste highlighted text here)", value="", height=120, key=f"sel_{pid}")

    if "last_output" not in st.session_state:
        st.session_state.last_output = ""

    def run_action(label: str, key: str, description: str) -> None:
        if not settings["actions"][key]["enabled"]:
            st.warning(f"{label} is disabled for this project.")
            return

        intensity = float(settings["actions"][key]["intensity"])
        instructions = build_instructions(voice_bible, intensity=intensity)
        payload = make_task_payload(
            description,
            story_bible,
            scene=doc,
            selection=selection,
            extra={"project": meta.get("title", pid)},
        )

        try:
            out = responses_text(
                model=settings["model"],
                instructions=instructions,
                input_text=payload,
                max_output_tokens=750,
            )
        except Exception as e:
            st.error(f"AI error: {e}")
            return

        st.session_state.last_output = out
        history.append({"action": label, "selection": selection, "output": out})
        save_project(pid, doc=doc, history=history)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("Continue", key=f"btn_continue_{pid}"):
            run_action("Continue", "continue_scene", ACTIONS[0][2])
    with c2:
        if st.button("Rewrite", key=f"btn_rewrite_{pid}"):
            run_action("Rewrite", "rewrite_selection", ACTIONS[1][2])
    with c3:
        if st.button("Expand", key=f"btn_expand_{pid}"):
            run_action("Expand", "expand_sensory", ACTIONS[2][2])
    with c4:
        if st.button("Describe", key=f"btn_describe_{pid}"):
            run_action("Describe", "describe_more", ACTIONS[3][2])
    with c5:
        if st.button("Brainstorm", key=f"btn_brainstorm_{pid}"):
            run_action("Brainstorm", "brainstorm_next", ACTIONS[4][2])

    st.markdown("---")
    st.subheader("Output")
    out = st.text_area("AI Output", value=st.session_state.last_output, height=220, key=f"out_{pid}")

    a, b, c = st.columns(3)
    with a:
        if st.button("Append output to draft", key=f"btn_append_{pid}"):
            if out.strip():
                doc2 = (doc.rstrip() + "\n\n" + out.strip() + "\n")
                save_project(pid, doc=doc2)
                st.success("Appended.")
                # no st.rerun (disallowed)
    with b:
        if st.button("Save Draft", key=f"btn_save_draft_{pid}"):
            save_project(pid, doc=doc)
            st.success("Saved.")
    with c:
        if st.button("Clear Output", key=f"btn_clear_out_{pid}"):
            st.session_state.last_output = ""
            # no st.rerun (disallowed)

    st.markdown("---")
    st.subheader("History (last 10)")
    if history:
        for h in reversed(history[-10:]):
            st.markdown(f"**{h.get('action','')}**")
            if (h.get("selection") or "").strip():
                st.code((h["selection"] or "")[:700])
            st.code((h.get("output", "") or "")[:1600])
    else:
        st.caption("No generations yet.")

with right:
    st.subheader("Voice Bible")
    voice_bible["style_notes"] = st.text_area("Style notes", value=voice_bible.get("style_notes", ""), height=120, key=f"vb_style_{pid}")

    def _as_lines(v) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        if isinstance(v, str):
            return [line for line in v.splitlines() if line.strip()]
        return []

    voice_bible["do"] = _as_lines(st.text_area("Do (one per line)", value="\n".join(_as_lines(voice_bible.get("do", []))), height=90, key=f"vb_do_{pid}"))
    voice_bible["dont"] = _as_lines(st.text_area("Don't (one per line)", value="\n".join(_as_lines(voice_bible.get("dont", []))), height=90, key=f"vb_dont_{pid}"))
    voice_bible["lexicon"] = _as_lines(st.text_area("Lexicon / motifs (one per line)", value="\n".join(_as_lines(voice_bible.get("lexicon", []))), height=90, key=f"vb_lex_{pid}"))
    voice_bible["anti_lexicon"] = _as_lines(st.text_area("Avoid (one per line)", value="\n".join(_as_lines(voice_bible.get("anti_lexicon", []))), height=90, key=f"vb_anti_{pid}"))

    voice_bible["pov"] = st.text_input("POV (optional)", value=voice_bible.get("pov", ""), key=f"vb_pov_{pid}")
    voice_bible["tense"] = st.text_input("Tense (optional)", value=voice_bible.get("tense", ""), key=f"vb_tense_{pid}")
    voice_bible["sentence_rhythm"] = st.text_input("Sentence rhythm (optional)", value=voice_bible.get("sentence_rhythm", ""), key=f"vb_rhythm_{pid}")
    voice_bible["imagery_profile"] = st.text_input("Imagery profile (optional)", value=voice_bible.get("imagery_profile", ""), key=f"vb_img_{pid}")
    voice_bible["dialogue_profile"] = st.text_input("Dialogue profile (optional)", value=voice_bible.get("dialogue_profile", ""), key=f"vb_dial_{pid}")
    voice_bible["metaphor_policy"] = st.text_input("Metaphor policy (optional)", value=voice_bible.get("metaphor_policy", ""), key=f"vb_meta_{pid}")
    voice_bible["profanity_policy"] = st.text_input("Profanity policy (optional)", value=voice_bible.get("profanity_policy", ""), key=f"vb_prof_{pid}")

    if st.button("Save Voice Bible", key=f"btn_save_vb_{pid}"):
        save_project(pid, voice_bible=voice_bible)
        st.success("Saved.")

    st.markdown("---")
    st.subheader("Auto Voice Learning")
    sample_len = st.slider("Use last N characters of draft", 2000, 20000, 8000, step=500, key=f"learn_len_{pid}")

    if st.button("Learn Voice from Draft", key=f"btn_learn_{pid}"):
        sample = (doc or "")[-int(sample_len):]
        if len(sample.strip()) < 400:
            st.warning("Write a bit more first (need at least ~400 characters).")
        else:
            learn_instructions = "You are a precise literary style analyst. Output STRICT JSON only."
            payload = make_voice_learn_payload(sample)

            try:
                learned = responses_json(
                    model=settings["model"],
                    instructions=learn_instructions,
                    input_text=payload,
                    max_output_tokens=950,
                )
            except Exception as e:
                st.error(f"Voice learning error: {e}")
                st.stop()

            for k in [
                "style_notes", "pov", "tense", "sentence_rhythm", "imagery_profile",
                "dialogue_profile", "metaphor_policy", "profanity_policy"
            ]:
                v = learned.get(k)
                if isinstance(v, str) and v.strip():
                    voice_bible[k] = v.strip()

            for k in ["do", "dont", "lexicon", "anti_lexicon"]:
                v = learned.get(k)
                if isinstance(v, list):
                    voice_bible[k] = [str(x).strip() for x in v if str(x).strip()][:30]

            save_project(pid, voice_bible=voice_bible)
            st.success("Voice learned + saved to this project.")
            st.rerun()  # allowed
'''

# Replace everything from marker to end
s = s[:idx] + LOCKED_UI + "\n"

app.write_text(s, encoding="utf-8")
print("OK: requirements.txt updated; app.py updated to locked layout.")
PY

# quick sanity check
python3 -m py_compile app.py
echo "OK: app.py compiles"
