
file_path = "frontend/pages/3_Dashboard.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports
if "from exports import generate_pdf_report" not in content:
    content = content.replace("from utils import get_anomalies, post_chat, get_dashboard_stats", "from utils import get_anomalies, post_chat, get_dashboard_stats\nfrom exports import generate_pdf_report")

# Tab 1: Executive Overview -> Add Export PDF at top
tab1_start = """with tab1:
    with st.spinner("Fetching executive dashboard statistics..."):
        stats_res = get_dashboard_stats(st.session_state.session_id)"""

tab1_new = """with tab1:
    with st.spinner("Fetching executive dashboard statistics..."):
        stats_res = get_dashboard_stats(st.session_state.session_id)
        
    if "error" not in stats_res:
        st.markdown("### 📄 Master Exports")
        try:
            # Generate a fast text summary for PDF
            kpis = stats_res.get("kpis", {})
            pdf_text = f"# Executive Dashboard Report\\n\\n"
            pdf_text += f"## KPIs\\n- Total Rows: {kpis.get('total_rows', 0)}\\n- Total Columns: {kpis.get('total_columns', 0)}\\n- Missing Cells: {kpis.get('missing_cells', 0)}\\n- Duplicate Rows: {kpis.get('duplicate_rows', 0)}\\n\\n"
            pdf_text += f"## Data Quality Summary\\nDataset size is {kpis.get('memory_usage_mb', 0)} MB.\\n\\n"
            pdf_bytes = generate_pdf_report("Executive Report", pdf_text)
            st.download_button("📑 Download Executive Report PDF", data=pdf_bytes, file_name="executive_report.pdf", mime="application/pdf", key="dl_exec_pdf")
        except:
            pass
        st.markdown("---")"""
content = content.replace(tab1_start, tab1_new)

# Tab 2: Anomaly Center -> Add Download Anomaly Report
tab2_start = """                if anomaly_res.get("flagged_rows"):
                    st.markdown("#### 🚩 Outlier Rows Sample")
                    flagged_df = pd.DataFrame(anomaly_res["flagged_rows"])
                    st.dataframe(flagged_df, use_container_width=True)"""

tab2_new = """                if anomaly_res.get("flagged_rows"):
                    st.markdown("#### 🚩 Outlier Rows Sample")
                    flagged_df = pd.DataFrame(anomaly_res["flagged_rows"])
                    st.dataframe(flagged_df, use_container_width=True)
                    
                    st.markdown("#### 📄 Export Anomaly Report")
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        st.download_button("💾 Download Flagged Rows (CSV)", data=flagged_df.to_csv(index=False), file_name="anomalies.csv", mime="text/csv", key="dl_anom_csv")
                    with col_a2:
                        st.download_button("📥 Download Explanation (MD)", data=anomaly_res["business_explanation"], file_name="anomaly_explanation.md", key="dl_anom_md")"""
content = content.replace(tab2_start, tab2_new)

# Tab 3: AI Business Summary -> Add Download Business Summary
tab3_start = """            else:
                st.markdown(summary_res.get("response_text", ""))
                if summary_res.get("reasoning"):
                    st.caption(f"Reasoning: {summary_res['reasoning']}")"""

tab3_new = """            else:
                st.markdown(summary_res.get("response_text", ""))
                if summary_res.get("reasoning"):
                    st.caption(f"Reasoning: {summary_res['reasoning']}")
                    
                st.markdown("#### 📄 Export Business Summary")
                st.download_button("📥 Download Summary (MD)", data=summary_res.get("response_text", ""), file_name="business_summary.md", key="dl_bus_md")
                try:
                    pdf_bytes = generate_pdf_report("AI Business Summary", summary_res.get("response_text", ""))
                    st.download_button("📑 Download Summary (PDF)", data=pdf_bytes, file_name="business_summary.pdf", mime="application/pdf", key="dl_bus_pdf")
                except:
                    pass"""
content = content.replace(tab3_start, tab3_new)

# Add PNG download buttons to Plotly charts
charts = [
    ("st.plotly_chart(fig_missing, use_container_width=True)", "fig_missing", "missing_values.png"),
    ("st.plotly_chart(fig_cat, use_container_width=True)", "fig_cat", "categorical.png"),
    ("st.plotly_chart(fig_dist, use_container_width=True)", "fig_dist", "distribution.png"),
    ("st.plotly_chart(fig_box, use_container_width=True)", "fig_box", "boxplot.png"),
    ("st.plotly_chart(fig_corr, use_container_width=True)", "fig_corr", "correlation.png"),
    ("st.plotly_chart(fig_bar_corr, use_container_width=True)", "fig_bar_corr", "scatter_proxy.png"),
]

for old_str, fig_var, filename in charts:
    new_str = f"{old_str}\\n                    try:\\n                        st.download_button('📸 Download PNG', data={fig_var}.to_image(format='png'), file_name='{filename}', mime='image/png')\\n                    except:\\n                        pass"
    content = content.replace(old_str, new_str)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated 3_Dashboard.py successfully!")
