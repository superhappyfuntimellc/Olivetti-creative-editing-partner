[02:38:20] 🐍 Python dependencies were installed from /mount/src/superhappyfuntimellc/requirements.txt using uv.

Check if streamlit is installed

Streamlit is already installed

[02:38:21] 📦 Processed dependencies!




────────────────────── Traceback (most recent call last) ───────────────────────

  /home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptru  

  nner/exec_code.py:129 in exec_func_with_error_handling                        

                                                                                

  /home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptru  

  nner/script_runner.py:671 in code_to_exec                                     

                                                                                

  /mount/src/superhappyfuntimellc/app.py:137 in <module>                        

                                                                                

    134 # ============================================================          

    135 project = st.session_state.projects[st.session_state.current_project]   

    136 chapters = project["chapters"]                                          

  ❱ 137 chapter = chapters[st.session_state.current_chapter]                    

    138                                                                         

    139 tabs = st.tabs(["Chapter", "Story Bible"])                              

    140                                                                         

────────────────────────────────────────────────────────────────────────────────

IndexError: list index out of range

main
