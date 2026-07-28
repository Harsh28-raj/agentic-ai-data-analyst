"""
DataMind AI - Main Streamlit Application Entrypoint.
"""
import streamlit as st
import os
from utils import get_health

st.set_page_config(
    page_title="DataMind AI - Autonomous Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Premium UI Styling
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize Session States
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "quality_report" not in st.session_state:
    st.session_state.quality_report = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Sidebar Status
st.sidebar.image("https://img.icons8.com/isometric/96/artificial-intelligence.png", width=64)
st.sidebar.title("DataMind AI")
st.sidebar.caption("Powered by Groq Cloud (llama-3.3-70b-versatile) & LangGraph")

health = get_health()
if health.get("status") == "healthy":
    st.sidebar.success(f"Backend Connected | Model: {health.get('model')}")
else:
    st.sidebar.error("Backend Disconnected")

st.sidebar.markdown("---")
st.sidebar.markdown("### Active Session")
if st.session_state.session_id:
    st.sidebar.info(f"ID: `{st.session_state.session_id[:8]}...`")
    st.sidebar.caption(f"Files: {len(st.session_state.uploaded_files)}")
else:
    st.sidebar.warning("No dataset uploaded yet.")

# Main Landing Page Body
st.markdown('<h1 class="gradient-header">DataMind AI</h1>', unsafe_allow_html=True)
st.markdown("### Production-Ready AI Data Analyst Powered by Groq Cloud & LangGraph ReAct Agent")

st.markdown("""
<div class="glass-card">
    <h4>Welcome to DataMind AI</h4>
    <p>Upload your CSV datasets, ask complex analytical questions in natural language, generate instant Plotly visualizations, inspect auto-generated SQL code, detect statistical anomalies, and explore executive data quality reports.</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="glass-card">
        <h3>📁 Multi-CSV Upload</h3>
        <p>Upload single or joined CSV files with automated schema validation, encoding detection, and data health scores.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="glass-card">
        <h3>💬 ReAct Agent Chat</h3>
        <p>Interact using natural language with live token streaming, transparent SQL/Pandas code view, and step-by-step analytical reasoning.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="glass-card">
        <h3>📊 Executive Dashboard</h3>
        <p>Instant KPI summaries, automated anomaly detection (IQR, Z-Score, Isolation Forest), and business explanations.</p>
    </div>
    """, unsafe_allow_html=True)

st.info("👈 Select **1_Upload** in the sidebar to get started by uploading your dataset!")
