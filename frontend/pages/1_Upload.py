"""
DataMind AI - Upload & Data Quality Page.
"""
import streamlit as st
import os
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

import pandas as pd
from utils import upload_files

# Initialize required session state variables
if "quality_report" not in st.session_state:
    st.session_state.quality_report = None
if "datasets" not in st.session_state:
    st.session_state.datasets = {}
if "analysis_session" not in st.session_state:
    st.session_state.analysis_session = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False

# if "quality_report" not in st.session_state:
    # st.session_state.quality_report = None
# if "datasets" not in st.session_state:
    # st.session_state.datasets = {}
# if "analysis_session" not in st.session_state:
    # st.session_state.analysis_session = None
# if "uploaded_files" not in st.session_state:
    # st.session_state.uploaded_files = []
# if "upload_success" not in st.session_state:
    # st.session_state.upload_success = False

st.set_page_config(page_title="Upload & Data Quality - DataMind AI", page_icon="📁", layout="wide")

st.markdown('<h2 style="color:#38bdf8;">📁 Dataset Upload & Data Quality Report</h2>', unsafe_allow_html=True)
st.markdown("Upload one or multiple CSV files to initialize your DuckDB analysis session.")

uploaded_files = st.file_uploader(
    "Choose CSV file(s)",
    type=["csv"],
    accept_multiple_files=True,
    help="Support for single or multi-CSV datasets up to 50MB per file."
)

if uploaded_files:
    if st.button("🚀 Process & Initialize Analysis Session"):
        with st.spinner("Validating CSV schemas, encoding, and loading into DuckDB..."):
            files_payload = []
            for file in uploaded_files:
                bytes_data = file.getvalue()
                files_payload.append(("files", (file.name, bytes_data, "text/csv")))

            res = upload_files(files_payload)

            if "error" in res:
                st.error(f"Upload Failed: {res['error']}")
            else:
                st.session_state.session_id = res["session_id"]
                st.session_state.uploaded_files = res["uploaded_files"]
                st.session_state.quality_report = res["quality_report"]
                st.success(res["message"])

if st.session_state.get("quality_report"):
    st.markdown("---")
    report = st.session_state.get("quality_report")

    # Health Score Metric
    col_score, col_count, col_warn = st.columns(3)
    with col_score:
        score = report.get("overall_health_score", 100.0)
        st.metric("Overall Data Health Score", f"{score}/100")
    with col_count:
        st.metric("Total Datasets Loaded", len(report.get("datasets", {})))
    with col_warn:
        st.metric("Quality Warnings Count", len(report.get("warnings", [])))

    # Warnings section
    if report.get("warnings"):
        with st.expander("⚠️ Data Quality Warnings & Recommendations", expanded=True):
            for warn in report["warnings"]:
                st.warning(warn)

    # Inferred Multi-File Relationships
    if report.get("inferred_relationships"):
        with st.expander("🔗 Inferred Multi-File Join Keys", expanded=True):
            for rel in report["inferred_relationships"]:
                st.info(f"**{rel['table1']}** ↔ **{rel['table2']}** linked on common key: `{rel['key']}`")

    # Dataset Schema Tabs
    datasets = report.get("datasets", {})
    if datasets:
        st.markdown("### 📊 Dataset Schemas & Column Audit")
        tabs = st.tabs(list(datasets.keys()))
        for tab, (ds_name, meta) in zip(tabs, datasets.items()):
            with tab:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Rows", meta["row_count"])
                c2.metric("Columns", meta["column_count"])
                c3.metric("Duplicate Rows", f"{meta['duplicate_rows']} ({meta['duplicate_pct']}%)")
                c4.metric("Missing Cells", meta["total_missing_cells"])

                st.markdown("#### Column Data Types & Missingness")
                col_df = pd.DataFrame({
                    "Column": list(meta["column_types"].keys()),
                    "Data Type": list(meta["column_types"].values()),
                    "Missing %": [meta["missing_percentages"].get(c, 0.0) for c in meta["column_types"].keys()]
                })
                st.dataframe(col_df, use_container_width=True)

    st.markdown("---")
    st.success("✅ Dataset ready! Click **2_Chat** in the sidebar to start natural language analysis.")
