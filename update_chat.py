
file_path = "frontend/pages/2_Chat.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add export imports
if "from exports import generate_pdf_report" not in content:
    content = content.replace("from utils import post_chat, stream_chat, BACKEND_URL", "from utils import post_chat, stream_chat, BACKEND_URL\nfrom exports import generate_pdf_report")

# Add buttons in history display
history_block_old = """        # Code snippet sections with copy buttons natively in st.code
        if message.get("sql_code") or message.get("pandas_code"):
            with st.expander("💻 Code Snippets", expanded=False):
                if message.get("sql_code"):
                    st.markdown("**DuckDB SQL**")
                    st.code(message["sql_code"], language="sql")
                if message.get("pandas_code"):
                    st.markdown("**Pandas Equivalent**")
                    st.code(message["pandas_code"], language="python")"""

history_block_new = """        # Code snippet sections with copy buttons natively in st.code
        if message.get("sql_code") or message.get("pandas_code"):
            with st.expander("💻 Code Snippets & Exports", expanded=False):
                if message.get("sql_code"):
                    st.markdown("**DuckDB SQL**")
                    st.code(message["sql_code"], language="sql")
                    # Exports
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button("💾 Download SQL", data=message["sql_code"], file_name=f"query_{idx}.sql", key=f"dl_sql_{idx}")
                    with dl_col2:
                        if st.button("📊 Fetch CSV Results", key=f"fetch_csv_{idx}"):
                            with st.spinner("Executing..."):
                                try:
                                    res = requests.post(f"{BACKEND_URL}/query/csv", json={"session_id": st.session_state.session_id, "sql_code": message["sql_code"]})
                                    if res.status_code == 200:
                                        st.download_button("💾 Download CSV", data=res.text, file_name=f"results_{idx}.csv", mime="text/csv", key=f"dl_csv_{idx}")
                                except:
                                    st.error("Error fetching CSV")
                if message.get("pandas_code"):
                    st.markdown("**Pandas Equivalent**")
                    st.code(message["pandas_code"], language="python")
                    
        # General Exports
        with st.expander("📄 Export Analysis", expanded=False):
            st.download_button("📥 Download Markdown", data=message["content"], file_name=f"analysis_{idx}.md", key=f"dl_md_{idx}")
            try:
                pdf_bytes = generate_pdf_report(f"DataMind AI Analysis", message["content"])
                st.download_button("📑 Download PDF Report", data=pdf_bytes, file_name=f"analysis_{idx}.pdf", mime="application/pdf", key=f"dl_pdf_{idx}")
            except Exception as e:
                st.error(f"PDF Export Error: {e}")"""
content = content.replace(history_block_old, history_block_new)

# Same for the active response section
active_block_old = """            # Code Snippets
            if sql_code or pandas_code:
                with st.expander("💻 Code Snippets", expanded=False):
                    if sql_code:
                        st.markdown("**DuckDB SQL**")
                        st.code(sql_code, language="sql")
                    if pandas_code:
                        st.markdown("**Pandas Equivalent**")
                        st.code(pandas_code, language="python")"""

active_block_new = """            # Code Snippets
            if sql_code or pandas_code:
                with st.expander("💻 Code Snippets & Exports", expanded=False):
                    if sql_code:
                        st.markdown("**DuckDB SQL**")
                        st.code(sql_code, language="sql")
                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            st.download_button("💾 Download SQL", data=sql_code, file_name="query.sql", key="dl_sql_curr")
                        with dl_col2:
                            if st.button("📊 Fetch CSV Results", key="fetch_csv_curr"):
                                with st.spinner("Executing..."):
                                    try:
                                        res = requests.post(f"{BACKEND_URL}/query/csv", json={"session_id": st.session_state.session_id, "sql_code": sql_code})
                                        if res.status_code == 200:
                                            st.download_button("💾 Download CSV", data=res.text, file_name="results.csv", mime="text/csv", key="dl_csv_curr")
                                    except:
                                        st.error("Error fetching CSV")
                    if pandas_code:
                        st.markdown("**Pandas Equivalent**")
                        st.code(pandas_code, language="python")
                        
            with st.expander("📄 Export Analysis", expanded=False):
                st.download_button("📥 Download Markdown", data=full_response, file_name="analysis.md", key="dl_md_curr")
                try:
                    pdf_bytes = generate_pdf_report("DataMind AI Analysis", full_response)
                    st.download_button("📑 Download PDF Report", data=pdf_bytes, file_name="analysis.pdf", mime="application/pdf", key="dl_pdf_curr")
                except:
                    pass"""
content = content.replace(active_block_old, active_block_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated 2_Chat.py successfully!")
