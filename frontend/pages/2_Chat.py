"""
DataMind AI - Natural Language Conversational Analysis Page.
"""
import streamlit as st
import os
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

import plotly.express as px
import re
import requests
import os
from utils import stream_chat, BACKEND_URL
from exports import generate_pdf_report

st.set_page_config(page_title="Chat & Analysis - DataMind AI", page_icon="💬", layout="wide")

# Custom CSS for better message cards, spacing, and skeletons
st.markdown("""
<style>
.stChatMessage {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.stChatMessage:nth-child(even) {
    background-color: #1e293b;
}
.stChatMessage:nth-child(odd) {
    background-color: #0f172a;
}
.skeleton {
    animation: skeleton-loading 1s linear infinite alternate;
    height: 1rem;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
}
@keyframes skeleton-loading {
    0% { background-color: #334155; }
    100% { background-color: #475569; }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h2 style="color:#818cf8;">💬 Conversational AI Analyst</h2>', unsafe_allow_html=True)

if not st.session_state.get("session_id"):
    st.warning("⚠️ Please upload a CSV dataset first on the **1_Upload** page.")
    st.stop()

# Initialize or fetch chat history
if "chat_messages" not in st.session_state or not st.session_state.chat_messages:
    try:
        hist_resp = requests.get(f"{BACKEND_URL}/session/{st.session_state.session_id}/history", timeout=5)
        if hist_resp.status_code == 200:
            history = hist_resp.json().get("history", [])
            st.session_state.chat_messages = []
            for msg in history:
                st.session_state.chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "reasoning": msg.get("reasoning"),
                    "chart_spec": msg.get("chart_spec"),
                    "sql_code": msg.get("sql_code"),
                    "pandas_code": msg.get("pandas_code")
                })
        else:
            st.session_state.chat_messages = []
    except Exception:
        st.session_state.chat_messages = []

st.caption(f"Session ID: `{st.session_state.session_id}` | Datasets Loaded: {', '.join(st.session_state.uploaded_files)}")
st.divider()

# Example Prompt Chips
st.markdown("##### 💡 Example Questions:")
example_cols = st.columns(3)
sample_queries = [
    "Which region generated the highest revenue?",
    "Show monthly sales trends.",
    "Which products are underperforming?",
    "What are the top five customers?",
    "Generate SQL for this analysis.",
    "Detect anomalies in the dataset."
]

selected_prompt = None
for idx, query in enumerate(sample_queries):
    col = example_cols[idx % 3]
    if col.button(f"📌 {query}", key=f"chip_{idx}"):
        selected_prompt = query
st.write("")

# Helper function to parse suggested questions
def parse_suggested_questions(text):
    questions = []
    # Try to find the section
    if "**Next Suggested Questions**" in text or "Next Suggested Questions:" in text:
        parts = text.split("**Next Suggested Questions**")
        if len(parts) < 2:
            parts = text.split("Next Suggested Questions:")
        if len(parts) == 2:
            q_part = parts[1].strip()
            # Find bullet points or numbered lists
            for line in q_part.split("\n"):
                line = line.strip()
                if line.startswith("- ") or line.startswith("* ") or (len(line) > 2 and line[0].isdigit() and line[1] in (".", ")")):
                    # clean up the numbering
                    clean_q = re.sub(r'^(\d+[\.\)]\s*|[\-\*]\s*)', '', line).strip()
                    if clean_q:
                        questions.append(clean_q)
    return questions

# Display Chat History
for idx, message in enumerate(st.session_state.chat_messages):
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            if message.get("reasoning"):
                with st.expander("💡 Reasoning & Tool Timeline", expanded=False):
                    st.info(message["reasoning"])

            if message.get("chart_spec"):
                spec = message["chart_spec"]
                fig = None
                ctype = spec.get("chart_type", "bar")
                x, y = spec.get("data", {}).get("x", []), spec.get("data", {}).get("y", [])
                title = spec.get("title", "Chart Visualization")

                if ctype == "line":
                    fig = px.line(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})
                elif ctype == "pie":
                    fig = px.pie(names=x, values=y, title=title)
                elif ctype == "scatter":
                    fig = px.scatter(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})
                else:
                    fig = px.bar(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})

                if fig:
                    fig.update_layout(template="plotly_dark", title_x=0.5)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            # Code snippet sections with copy buttons natively in st.code
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
                                    except Exception:
                                        st.error("Error fetching CSV")
                    if message.get("pandas_code"):
                        st.markdown("**Pandas Equivalent**")
                        st.code(message["pandas_code"], language="python")
                        
            # Original export block removed - handled by guarded export below            # General Exports - only for assistant responses
            if message.get("role") == "assistant":
                with st.expander("📄 Export Analysis", expanded=False):
                    st.download_button("📥 Download Markdown", data=message["content"], file_name=f"analysis_{idx}.md", key=f"dl_md_{idx}")
                    try:
                        import pandas as pd
                        import io as pd_io
                        blocks = []
                        
                        # Extract content safely
                        content_str = message.get("content", "")
                        if isinstance(content_str, dict):
                            content_str = content_str.get("answer", content_str.get("text", str(content_str)))
                        elif not isinstance(content_str, str):
                            content_str = str(content_str)
                            
                        has_content = bool(content_str and content_str.strip())
                        has_sql = bool(message.get("sql_code"))
                        has_chart = bool(message.get("chart_spec") and 'fig' in locals() and fig is not None)
                        
                        if not (has_content or has_sql or has_chart):
                            st.error("Error: Assistant response is empty. Cannot generate PDF.")
                        else:
                            question_text = st.session_state.chat_messages[idx-1]['content'] if (idx > 0 and st.session_state.chat_messages[idx-1]["role"] == "user") else ""
                            if question_text:
                                blocks.append({"type": "markdown", "text": f"### Question\n{question_text}"})
                                
                            if has_content:
                                blocks.append({"type": "markdown", "text": "### AI Response\n" + content_str})
                                
                            if message.get("reasoning"):
                                blocks.append({"type": "markdown", "text": "**Reasoning:**\n" + message.get("reasoning", "")})
                                
                            sql_count = 0
                            if has_sql:
                                blocks.append({"type": "sql", "text": message.get("sql_code", "")})
                                sql_count += 1
                                try:
                                    csv_res = requests.post(f"{BACKEND_URL}/query/csv", json={"session_id": st.session_state.session_id, "sql_code": message["sql_code"]})
                                    if csv_res.status_code == 200:
                                        df = pd.read_csv(pd_io.StringIO(csv_res.text))
                                        blocks.append({"type": "table", "dataframe": df})
                                except Exception as e:
                                    blocks.append({"type": "markdown", "text": f"*(Could not fetch data table: {e})*"})
                            
                            chart_count = 0
                            if has_chart:
                                try:
                                    import plotly.io as pio
                                    img_bytes = pio.to_image(fig, format='png', engine="kaleido")
                                    blocks.append({"type": "chart", "image_bytes": img_bytes})
                                    chart_count += 1
                                except Exception as e:
                                    blocks.append({"type": "markdown", "text": f"*(Chart could not be embedded: {e})*"})
                            
                            print(f"DEBUG EXPORT: Question exists? {bool(question_text)}")
                            print(f"DEBUG EXPORT: Assistant response exists? {has_content}")
                            print(f"DEBUG EXPORT: Response type: {type(content_str)}")
                            print(f"DEBUG EXPORT: Response length: {len(content_str)}")
                            print(f"DEBUG EXPORT: First 200 chars: {content_str[:200]}")
                            print(f"DEBUG EXPORT: SQL count: {sql_count}, Charts count: {chart_count}")
                            
                            pdf_bytes = generate_pdf_report(f"DataMind AI Analysis", blocks)
                            st.download_button("📑 Download PDF Report", data=pdf_bytes, file_name="analysis.pdf", mime="application/pdf", key="dl_pdf_current")
                    except Exception as e:
                        st.error(f"PDF Export Error: {e}")

        # Suggestion chips for the LAST message only
        if message["role"] == "assistant" and idx == len(st.session_state.chat_messages) - 1:
            sqs = parse_suggested_questions(message["content"])
            if sqs:
                st.write("")
                st.markdown("###### Suggested Follow-ups:")
                sq_cols = st.columns(len(sqs))
                for i, sq in enumerate(sqs):
                    if i < len(sq_cols):
                        if sq_cols[i].button(sq, key=f"sq_{idx}_{i}"):
                            selected_prompt = sq

st.write("")

# Chat Input Handler
user_input = st.chat_input("Ask a question about your dataset...")
prompt = user_input or selected_prompt

if prompt:
    # Append user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Assistant Response Placeholder
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        
        # Tool execution timeline / status
        status_container = st.status("Thinking...", expanded=True)
        with status_container:
            st.write("Initializing request...")
            
        # Loading skeleton until first token
        message_placeholder.markdown('<div class="skeleton" style="width:100%"></div><div class="skeleton" style="width:80%"></div><div class="skeleton" style="width:90%"></div>', unsafe_allow_html=True)
        
        full_response = ""
        reasoning_text = ""
        chart_spec = None
        sql_code = None
        pandas_code = None
        
        # Start streaming
        try:
            for chunk in stream_chat(st.session_state.session_id, prompt):
                chunk_type = chunk.get("type")
                
                if chunk_type == "reasoning":
                    with status_container:
                        st.write("⏳ " + chunk.get("content", ""))
                
                elif chunk_type == "token":
                    status_container.update(label="Generating response...", state="running", expanded=False)
                    full_response += chunk.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                
                elif chunk_type == "chart":
                    with status_container:
                        st.write("📊 Creating visualization...")
                    chart_spec = chunk.get("data")
                    
                elif chunk_type == "sql":
                    with status_container:
                        st.write("🔍 Executing SQL...")
                    sql_code = chunk.get("content")
                    
                elif chunk_type == "pandas":
                    with status_container:
                        st.write("🐼 Generating Pandas code...")
                    pandas_code = chunk.get("content")
                    
                elif chunk_type == "complete":
                    reasoning_text = chunk.get("reasoning", "")
                    status_container.update(label="Done!", state="complete", expanded=False)
                    with status_container:
                        st.write("✅ Request completed.")
                    
                elif chunk_type == "error":
                    status_container.update(label="Error occurred", state="error", expanded=True)
                    st.error(f"🚨 {chunk.get('content')}")
                    break

            # Final render without the blinking cursor
            st.write("DEBUG full_response:", repr(full_response))
            message_placeholder.markdown(full_response)
            
            # Show reasoning
            if reasoning_text:
                with st.expander("💡 Reasoning & Tool Timeline", expanded=False):
                    st.info(reasoning_text)
                    
            # Show charts
            if chart_spec:
                spec = chart_spec
                fig = None
                ctype = spec.get("chart_type", "bar")
                x, y = spec.get("data", {}).get("x", []), spec.get("data", {}).get("y", [])
                title = spec.get("title", "Chart Visualization")

                if ctype == "line":
                    fig = px.line(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})
                elif ctype == "pie":
                    fig = px.pie(names=x, values=y, title=title)
                elif ctype == "scatter":
                    fig = px.scatter(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})
                else:
                    fig = px.bar(x=x, y=y, title=title, labels={"x": spec.get("x_axis", ""), "y": spec.get("y_axis", "")})

                if fig:
                    fig.update_layout(template="plotly_dark", title_x=0.5)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            # Code Snippets
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
                                    except Exception:

                                        st.error("Error fetching CSV")
                    if pandas_code:
                        st.markdown("**Pandas Equivalent**")
                        st.code(pandas_code, language="python")
                        
            with st.expander("📄 Export Analysis", expanded=False):
                st.download_button("📥 Download Markdown", data=full_response, file_name=f"analysis_{len(st.session_state.chat_messages)}.md", key=f"dl_md_curr")
                try:
                    import pandas as pd
                    import io as pd_io
                    blocks = []

                    # Extract content safely
                    content_str = full_response

                    has_content = bool(content_str.strip())
                    has_sql = bool(sql_code)
                    has_chart = bool(chart_spec and 'fig' in locals() and fig is not None)
                    
                    if not (has_content or has_sql or has_chart):
                        st.error("Error: Assistant response is empty. Cannot generate PDF.")
                    else:
                        question_text = ""
                        if len(st.session_state.chat_messages) > 0 and st.session_state.chat_messages[-1]["role"] == "user":
                            question_text = st.session_state.chat_messages[-1]['content']
                            blocks.append({"type": "markdown", "text": f"### Question\n{question_text}"})
                        
                        if has_content:
                            blocks.append({"type": "markdown", "text": "### AI Response\n" + content_str})
                        
                        if reasoning_text:
                            blocks.append({"type": "markdown", "text": "**Reasoning:**\n" + reasoning_text})
                            
                        sql_count = 0
                        if has_sql:
                            blocks.append({"type": "sql", "text": sql_code})
                            sql_count += 1
                            try:
                                csv_res = requests.post(f"{BACKEND_URL}/query/csv", json={"session_id": st.session_state.session_id, "sql_code": sql_code})
                                if csv_res.status_code == 200:
                                    df = pd.read_csv(pd_io.StringIO(csv_res.text))
                                    blocks.append({"type": "table", "dataframe": df})
                            except Exception as e:
                                blocks.append({"type": "markdown", "text": f"*(Could not fetch data table: {e})*"})
                                
                        chart_count = 0
                        if has_chart:
                            try:
                                import plotly.io as pio
                                img_bytes = pio.to_image(fig, format='png', engine="kaleido")
                                blocks.append({"type": "chart", "image_bytes": img_bytes})
                                chart_count += 1
                            except Exception as e:
                                blocks.append({"type": "markdown", "text": f"*(Chart could not be embedded: {e})*"})
                        
                        print(f"DEBUG EXPORT: backend returned answer length {len(full_response)}")
                        print(f"DEBUG EXPORT: frontend received answer: {bool(has_content)}")
                        print(f"DEBUG EXPORT: export blocks count: {len(blocks)}")
                        
                        pdf_bytes = generate_pdf_report("DataMind AI Analysis", blocks)
                        st.download_button("📑 Download PDF Report", data=pdf_bytes, file_name=f"analysis_{idx}.pdf", mime="application/pdf", key=f"dl_pdf_{idx}")
                except Exception as e:
                    st.error(f"PDF Export Error: {e}")

            # Store assistant turn
            from datetime import datetime
            st.write("DEBUG assistant:", repr(full_response))
            assistant_entry = {
                "role": "assistant",
                "content": full_response,
                "reasoning": reasoning_text,
                "chart_spec": chart_spec,
                "sql_code": sql_code,
                "pandas_code": pandas_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            st.session_state.chat_messages.append(assistant_entry)
            
            # Re-run to refresh and show suggestion chips
            st.rerun()

        except Exception as e:
            st.error(f"🚨 Connection Error: {str(e)}")
            status_container.update(label="Connection Error", state="error")
