"""
DataMind AI - Executive Dashboard & Anomaly Analysis Page.
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
import plotly.express as px
import plotly.graph_objects as go
from utils import get_anomalies, post_chat, get_dashboard_stats
from exports import generate_pdf_report

st.set_page_config(page_title="Executive Dashboard - DataMind AI", page_icon="📊", layout="wide")

# Professional custom styling for metrics and summary cards
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h2 style="color:#c084fc;">📊 Executive Analytics Dashboard</h2>', unsafe_allow_html=True)

if not st.session_state.get("session_id"):
    st.warning("⚠️ Please upload a CSV dataset first on the **1_Upload** page.")
    st.stop()

# Use Tabs to organize the layout without deleting existing functionality
tab1, tab2, tab3 = st.tabs(["📈 Executive Overview", "🚨 Anomaly Center", "✨ AI Business Summary"])

with tab1:
    with st.spinner("Fetching executive dashboard statistics..."):
        stats_res = get_dashboard_stats(st.session_state.session_id)
        
    if "error" not in stats_res:
        st.markdown("---")
    
    if "error" in stats_res:
        st.error(f"Could not load dashboard statistics: {stats_res['error']}")
    else:
        st.markdown("### Executive KPIs")
        kpis = stats_res.get("kpis", {})
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows", f"{kpis.get('total_rows', 0):,}")
        col2.metric("Total Columns", f"{kpis.get('total_columns', 0):,}")
        col3.metric("Missing Cells", f"{kpis.get('missing_cells', 0):,}")
        col4.metric("Duplicate Rows", f"{kpis.get('duplicate_rows', 0):,}")
        
        st.markdown("---")
        
        # Missing values and overall dataset context
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.markdown("### Missing Value Visualization")
            missing = stats_res.get("missing_values", {})
            if sum(missing.values()) > 0:
                missing_df = pd.DataFrame(list(missing.items()), columns=["Feature", "Missing Count"]).sort_values("Missing Count", ascending=False)
                fig_missing = px.bar(missing_df[missing_df["Missing Count"] > 0], x="Feature", y="Missing Count", title="Null Values by Feature", color_discrete_sequence=["#ef4444"])
                fig_missing.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_missing, use_container_width=True, theme=None)
                try:
                    st.download_button('📸 Download PNG', data=fig_missing.to_image(format='png'), file_name='missing_values.png', mime='image/png')
                except Exception:

                    pass
            else:
                st.success("No missing values detected! Dataset is clean.")
        
        with col_m2:
            st.markdown("### Top Categorical Values")
            cat_tops = stats_res.get("categorical_tops", {})
            if cat_tops:
                # Create a selectbox to choose which categorical feature to view
                cat_feature = st.selectbox("Select Categorical Feature", list(cat_tops.keys()))
                if cat_feature:
                    cat_data = cat_tops[cat_feature]
                    cat_df = pd.DataFrame(list(cat_data.items()), columns=["Value", "Count"])
                    fig_cat = px.pie(cat_df, names="Value", values="Count", title=f"Top values in {cat_feature}", hole=0.4)
                    fig_cat.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_cat, use_container_width=True, theme=None)
                    try:
                        st.download_button('📸 Download PNG', data=fig_cat.to_image(format='png'), file_name='categorical.png', mime='image/png')
                    except Exception:

                        pass
            else:
                st.info("No categorical features found.")
        
        st.markdown("---")
        st.markdown("### Feature Statistics")
        
        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            dists = stats_res.get("distributions", {})
            if dists:
                dist_feature = st.selectbox("Select Numeric Feature for Distribution", list(dists.keys()))
                if dist_feature:
                    dist_data = dists[dist_feature]
                    counts = dist_data["counts"]
                    edges = dist_data["bin_edges"]
                    
                    fig_dist = go.Figure(go.Bar(
                        x=[f"{round(edges[i], 2)} - {round(edges[i+1], 2)}" for i in range(len(counts))],
                        y=counts,
                        marker_color="#60a5fa"
                    ))
                    fig_dist.update_layout(title=f"Distribution of {dist_feature}", template="plotly_dark", xaxis_title="Bins", yaxis_title="Frequency", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_dist, use_container_width=True, theme=None)
                    try:
                        st.download_button('📸 Download PNG', data=fig_dist.to_image(format='png'), file_name='distribution.png', mime='image/png')
                    except Exception:

                        pass
            else:
                st.info("No numeric features to distribute.")

        with col_d2:
            # Box plots for top numeric stats
            num_stats = stats_res.get("numeric_stats", {})
            if num_stats:
                box_feature = st.selectbox("Select Numeric Feature for Box Plot", list(num_stats.keys()))
                if box_feature:
                    b_stats = num_stats[box_feature]
                    fig_box = go.Figure(go.Box(
                        y=[b_stats.get('min', 0), b_stats.get('25%', 0), b_stats.get('50%', 0), b_stats.get('75%', 0), b_stats.get('max', 0)],
                        name=box_feature,
                        marker_color="#34d399",
                        boxpoints=False
                    ))
                    fig_box.update_layout(title=f"Box Plot for {box_feature}", template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_box, use_container_width=True, theme=None)
                    try:
                        st.download_button('📸 Download PNG', data=fig_box.to_image(format='png'), file_name='boxplot.png', mime='image/png')
                    except Exception:

                        pass
            else:
                st.info("No numeric features to summarize.")
                
        st.markdown("---")
        col_c1, col_c2 = st.columns([1, 1])
        
        with col_c1:
            st.markdown("### Correlation Heatmap")
            corr = stats_res.get("correlation", {})
            if corr:
                corr_df = pd.DataFrame(corr)
                fig_corr = px.imshow(corr_df, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", title="Pearson Correlation Matrix")
                fig_corr.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_corr, use_container_width=True, theme=None)
                try:
                    st.download_button('📸 Download PNG', data=fig_corr.to_image(format='png'), file_name='correlation.png', mime='image/png')
                except Exception:

                    pass
            else:
                st.info("Not enough numeric columns for a correlation heatmap.")
                
        with col_c2:
            st.markdown("### Scatter Plot Candidates")
            scatter_cands = stats_res.get("scatter_candidates", [])
            if len(scatter_cands) >= 2:
                target = scatter_cands[0]
                st.info(f"Top correlated pair: **{target}** vs **{scatter_cands[1]}**.")
                if target in corr:
                    corr_series = pd.Series(corr[target]).drop(target).sort_values(ascending=True)
                    fig_bar_corr = px.bar(corr_series, orientation='h', title=f"Features Correlated with {target}")
                    fig_bar_corr.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_bar_corr, use_container_width=True, theme=None)
                    try:
                        st.download_button('📸 Download PNG', data=fig_bar_corr.to_image(format='png'), file_name='scatter_proxy.png', mime='image/png')
                    except Exception:

                        pass
            else:
                st.info("Not enough numeric columns to show scatter correlations.")
                
        st.markdown("---")
        st.markdown("### 📄 Master Exports")
        try:
            import plotly.io as pio
            blocks = []
            
            # Text KPI block
            blocks.append({"type": "markdown", "text": f"## Executive Dashboard KPIs\n- **Total Rows:** {kpis.get('total_rows', 0):,}\n- **Total Columns:** {kpis.get('total_columns', 0):,}\n- **Missing Cells:** {kpis.get('missing_cells', 0):,}\n- **Duplicate Rows:** {kpis.get('duplicate_rows', 0):,}"})
            
            # Capture charts
            if 'fig_dist' in locals() and fig_dist is not None:
                blocks.append({"type": "markdown", "text": "### Feature Distribution"})
                blocks.append({"type": "chart", "image_bytes": pio.to_image(fig_dist, format='png', engine='kaleido')})
                
            if 'fig_cat' in locals() and fig_cat is not None:
                blocks.append({"type": "markdown", "text": "### Categorical Features"})
                blocks.append({"type": "chart", "image_bytes": pio.to_image(fig_cat, format='png', engine='kaleido')})
                
            if 'fig_box' in locals() and fig_box is not None:
                blocks.append({"type": "markdown", "text": "### Outlier Analysis"})
                blocks.append({"type": "chart", "image_bytes": pio.to_image(fig_box, format='png', engine='kaleido')})
                
            if 'fig_corr' in locals() and fig_corr is not None:
                blocks.append({"type": "markdown", "text": "### Correlation Heatmap"})
                blocks.append({"type": "chart", "image_bytes": pio.to_image(fig_corr, format='png', engine='kaleido')})
                
            if 'fig_bar_corr' in locals() and fig_bar_corr is not None:
                blocks.append({"type": "markdown", "text": "### Feature Correlations"})
                blocks.append({"type": "chart", "image_bytes": pio.to_image(fig_bar_corr, format='png', engine='kaleido')})
                
            pdf_bytes = generate_pdf_report("Executive Dashboard Report", blocks)
            st.download_button("📑 Download Executive Report PDF", data=pdf_bytes, file_name="executive_report.pdf", mime="application/pdf", key="dl_exec_pdf")
        except Exception as e:
            st.error(f"PDF Export Error: {e}")

with tab2:
    st.markdown("### 🚨 Anomaly Detection Center")
    st.markdown("Run statistical outlier detection (IQR, Z-Score, Isolation Forest) paired with Groq Cloud business risk explanations.")

    if st.button("🔍 Run Anomaly Detection Audit"):
        with st.spinner("Analyzing dataset with IQR, Z-score, Isolation Forest, and Groq LLM..."):
            anomaly_res = get_anomalies(st.session_state.session_id)
            if "error" in anomaly_res:
                st.error(anomaly_res["error"])
            else:
                st.success(f"Flagged {anomaly_res['total_anomalies_flagged']} statistical anomalies in dataset '{anomaly_res['table_name']}'.")

                st.markdown("#### 💡 Executive Business Explanation")
                st.info(anomaly_res["business_explanation"])

                if anomaly_res.get("flagged_rows"):
                    st.markdown("#### 🚩 Outlier Rows Sample")
                    flagged_df = pd.DataFrame(anomaly_res["flagged_rows"])
                    st.dataframe(flagged_df, use_container_width=True)
                    
                    st.markdown("#### 📄 Export Anomaly Report")
                    col_a1, col_a2, col_a3 = st.columns(3)
                    with col_a1:
                        st.download_button("💾 Download Flagged Rows (CSV)", data=flagged_df.to_csv(index=False), file_name="anomalies.csv", mime="text/csv", key="dl_anom_csv")
                    with col_a2:
                        st.download_button("📥 Download Explanation (MD)", data=anomaly_res["business_explanation"], file_name="anomaly_explanation.md", key="dl_anom_md")
                    with col_a3:
                        try:
                            blocks = [
                                {"type": "markdown", "text": "## 🚨 Anomaly Detection Center\n" + anomaly_res["business_explanation"]},
                                {"type": "table", "dataframe": flagged_df}
                            ]
                            pdf_bytes = generate_pdf_report("Anomaly Detection Report", blocks)
                            st.download_button("📑 Download Report (PDF)", data=pdf_bytes, file_name="anomaly_report.pdf", mime="application/pdf", key="dl_anom_pdf")
                        except Exception:
                            pass

with tab3:
    st.markdown("### 📈 Instant Business Summary & Highlights")
    st.markdown("Generate an AI-powered executive summary outlining key revenue distributions, top drivers, and potential risk areas.")
    
    if st.button("✨ Generate Executive Summary"):
        with st.spinner("Generating executive insights via Groq Cloud..."):
            summary_res = post_chat(st.session_state.session_id, "Summarize key business insights, revenue distributions, top drivers, and potential risk areas.")
            if "error" in summary_res:
                st.error(summary_res["error"])
            else:
                st.markdown(summary_res.get("response_text", ""))
                if summary_res.get("reasoning"):
                    st.caption(f"Reasoning: {summary_res['reasoning']}")
                    
                st.markdown("#### 📄 Export Business Summary")
                st.download_button("📥 Download Summary (MD)", data=summary_res.get("response_text", ""), file_name="business_summary.md", key="dl_bus_md")
                try:
                    pdf_bytes = generate_pdf_report("AI Business Summary", [{"type": "markdown", "text": summary_res.get("response_text", "")}])
                    st.download_button("📑 Download Summary (PDF)", data=pdf_bytes, file_name="business_summary.pdf", mime="application/pdf", key="dl_bus_pdf")
                except Exception:
                    pass
