────────────────────────────────────────────────────────────────────────────────────────


[21:17:22] 🐍 Python dependencies were installed from /mount/src/superhappyfuntimellc/requirements.txt using uv.

Check if streamlit is installed

Streamlit is already installed

[21:17:23] 📦 Processed dependencies!




────────────────────── Traceback (most recent call last) ───────────────────────

  /home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptru  

  nner/exec_code.py:129 in exec_func_with_error_handling                        

                                                                                

  /home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptru  

  nner/script_runner.py:671 in code_to_exec                                     

                                                                                

  /mount/src/superhappyfuntimellc/app.py:3 in <module>                          

                                                                                

      1 import streamlit as st                                                  

      2 from openai import OpenAI                                               

  ❱   3 from docx import Document                                               

      4 from io import BytesIO                                                  

      5                                                                         

      6 # ================== SETUP ==================                           

────────────────────────────────────────────────────────────────────────────────

ModuleNotFoundError: No module named 'docx
