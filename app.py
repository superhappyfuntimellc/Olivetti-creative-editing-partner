# ============================================================
# RIGHT SIDEBAR — VOICE BIBLE (FIXED)
# ============================================================
if right:
    with right:
        st.subheader("🎭 Voice Bible")

        # --- Active Voice ---
        voice_names = ["— Neutral —"] + list(st.session_state.voices.keys())
        active = st.selectbox(
            "Active Voice",
            voice_names,
            index=0 if not st.session_state.active_voice else voice_names.index(st.session_state.active_voice)
        )

        if active == "— Neutral —":
            st.session_state.active_voice = None
        else:
            st.session_state.active_voice = active

        # --- Intensity ---
        st.slider(
            "Voice Intensity",
            0.0,
            1.0,
            st.session_state.voices.get(st.session_state.active_voice, {}).get("intensity", 0.5),
            key="voice_intensity"
        )

        # --- Train New Voice ---
        with st.expander("Train New Voice", expanded=False):
            new_voice_name = st.text_input("Voice Name")
            new_voice_sample = st.text_area(
                "Paste a representative writing sample",
                height=160
            )

            if st.button("➕ Save Voice"):
                if new_voice_name and new_voice_sample:
                    st.session_state.voices[new_voice_name] = {
                        "sample": new_voice_sample,
                        "intensity": st.session_state.voice_intensity
                    }
                    st.session_state.active_voice = new_voice_name
                    st.success(f"Saved voice: {new_voice_name}")

        # --- Voice Library ---
        if st.session_state.voices:
            with st.expander("Voice Library", expanded=False):
                for v in list(st.session_state.voices.keys()):
                    cols = st.columns([3,1])
                    cols[0].write(v)
                    if cols[1].button("🗑", key=f"del_{v}"):
                        del st.session_state.voices[v]
                        if st.session_state.active_voice == v:
                            st.session_state.active_voice = None
                        st.experimental_rerun()
