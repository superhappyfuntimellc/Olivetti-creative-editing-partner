# ============================================================
# LEFT SIDEBAR — STORY BIBLE (WITH AI IDEAS)
# ============================================================
if left:
    with left:
        st.subheader("📖 Story Bible")

        def idea_prompt(label, existing):
            return f"""
Generate creative ideas for the following story section.
Do not explain. Just write useful content.

SECTION: {label}

CURRENT NOTES:
{existing}
"""

        # Junk Drawer
        with st.expander("Junk Drawer", expanded=True):
            junk = st.text_area("Notes", key="junk", height=120)
            if st.button("💡 Generate Ideas", key="junk_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=idea_prompt("Junk Drawer", junk),
                    temperature=0.7
                )
                st.session_state.junk = junk + "\n\n" + r.output_text

        # Synopsis
        with st.expander("Synopsis", expanded=False):
            synopsis = st.text_area("Synopsis", key="synopsis", height=120)
            if st.button("💡 Generate Synopsis Ideas", key="syn_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=idea_prompt("Synopsis", synopsis),
                    temperature=0.6
                )
                st.session_state.synopsis = synopsis + "\n\n" + r.output_text

        # Genre / Style
        with st.expander("Genre / Style", expanded=False):
            genre_notes = st.text_area("Genre & Style Notes", key="genre_notes", height=120)
            if st.button("💡 Generate Style Ideas", key="genre_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=idea_prompt("Genre / Style", genre_notes),
                    temperature=0.5
                )
                st.session_state.genre_notes = genre_notes + "\n\n" + r.output_text
        # Characters
        with st.expander("Characters", expanded=False):
            characters = st.text_area(
                "Characters (names, traits, arcs, relationships)",
                key="characters",
                height=160
            )

            if st.button("💡 Generate Character Ideas", key="char_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=f"""
Generate character ideas for a novel.
Include:
- Names
- Roles
- Key traits
- Internal conflict
- Relationships

CURRENT NOTES:
{characters}
""",
                    temperature=0.6
                )
                st.session_state.characters = characters + "\n\n" + r.output_text

        # World Elements
        with st.expander("World Elements", expanded=False):
            world = st.text_area("Worldbuilding", key="world", height=140)
            if st.button("💡 Generate World Ideas", key="world_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=idea_prompt("World Elements", world),
                    temperature=0.6
                )
                st.session_state.world = world + "\n\n" + r.output_text

        # Outline
        with st.expander("Outline", expanded=False):
            outline = st.text_area("Chapter Outline", key="outline", height=200)
            if st.button("💡 Generate Chapter Ideas", key="outline_ai"):
                r = client.responses.create(
                    model="gpt-4.1-mini",
                    input=idea_prompt("Outline", outline),
                    temperature=0.6
                )
                st.session_state.outline = outline + "\n\n" + r.output_text
