
files = [
    "frontend/pages/1_Upload.py",
    "frontend/pages/2_Chat.py",
    "frontend/pages/3_Dashboard.py"
]

css_loader = """import os
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()
"""

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "load_css()" not in content:
        # inject after streamlit import
        content = content.replace("import streamlit as st", f"import streamlit as st\\n{css_loader}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

print("CSS injected into pages.")
