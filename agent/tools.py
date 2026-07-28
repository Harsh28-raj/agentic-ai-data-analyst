"""
LangChain ReAct Agent Tools for DataMind AI.
"""
import json
from typing import Optional
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from functools import lru_cache

from core.config import settings
from core.session import session_store
from core.logger import logger, track_tool_latency
from agent.prompts import ANOMALY_EXPLANATION_PROMPT


import os

def _get_llm() -> ChatOpenAI:
    """Returns ChatOpenAI client instance configured for Groq Cloud API."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or "your_groq_api_key_here"
    base_url = settings.GROQ_BASE_URL or os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "llama-3.3-70b-versatile"
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,  # type: ignore
        base_url=base_url,  # type: ignore
        temperature=0
    )



@tool
def query_data_tool(session_id: str, sql_query: str) -> str:
    """
    Executes a SQL query against the session's DuckDB dataset(s).
    Use this tool to aggregate data, join tables, compute metrics, filter rows, or select specific columns.
    
    Args:
        session_id: The current active user session ID.
        sql_query: Valid DuckDB SQL query string.
    """
    with track_tool_latency("query_data_tool", session_id=session_id):
        session = session_store.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session '{session_id}' not found."})

        try:
            result_df = session.duckdb_mgr.execute_sql(sql_query)
            # Truncate for prompt payload safety if very large
            output_df = result_df.head(100)
            return json.dumps({
                "status": "success",
                "row_count": len(result_df),
                "displayed_count": len(output_df),
                "columns": list(output_df.columns),
                "data": output_df.to_dict(orient="records"),
                "sql_executed": sql_query
            })
        except Exception as e:
            logger.error(f"Error in query_data_tool: {str(e)}")
            return json.dumps({"status": "error", "message": str(e), "sql_executed": sql_query})


@tool
def generate_chart_tool(
    session_id: str,
    chart_type: str,
    title: str,
    x_column: str,
    y_column: str,
    sql_query: Optional[str] = None
) -> str:
    """
    Generates a Plotly interactive chart configuration based on query results or dataset.
    
    Args:
        session_id: Active session ID.
        chart_type: One of ['bar', 'line', 'pie', 'scatter', 'box', 'histogram'].
        title: Title of the chart.
        x_column: Name of the column for X-axis / categories / labels.
        y_column: Name of the column for Y-axis / values.
        sql_query: Optional SQL query to extract exact aggregated data for the chart.
    """
    with track_tool_latency("generate_chart_tool", session_id=session_id):
        session = session_store.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session '{session_id}' not found."})

        try:
            if sql_query:
                df = session.duckdb_mgr.execute_sql(sql_query)
            else:
                # Fallback to first registered table
                if not session.duckdb_mgr.table_names:
                    return json.dumps({"error": "No tables uploaded in session."})
                first_table = session.duckdb_mgr.table_names[0]
                df = session.duckdb_mgr.execute_sql(f"SELECT * FROM {first_table} LIMIT 100")

            if x_column not in df.columns or y_column not in df.columns:
                return json.dumps({
                    "status": "error",
                    "message": f"Columns '{x_column}' or '{y_column}' not found in dataset. Available: {list(df.columns)}"
                })

            chart_spec = {
                "chart_type": chart_type.lower(),
                "title": title,
                "x_axis": x_column,
                "y_axis": y_column,
                "data": {
                    "x": df[x_column].tolist(),
                    "y": df[y_column].tolist()
                }
            }

            return json.dumps({
                "status": "success",
                "chart_spec": chart_spec,
                "message": f"Created {chart_type} chart titled '{title}'."
            })
        except Exception as e:
            logger.error(f"Error in generate_chart_tool: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})


@tool
def anomaly_detection_tool(session_id: str, table_name: Optional[str] = None, column_name: Optional[str] = None) -> str:
    """
    Detects statistical anomalies and numerical outliers in the dataset using IQR, Z-score, and Isolation Forest.
    Returns flagged rows along with an LLM-generated business explanation of why they were flagged.
    
    Args:
        session_id: Active session ID.
        table_name: Optional target table name (defaults to first table).
        column_name: Optional numeric column name to analyze (if None, analyzes all numeric columns).
    """
    with track_tool_latency("anomaly_detection_tool", session_id=session_id):
        session = session_store.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session '{session_id}' not found."})

        target_table = table_name or (session.duckdb_mgr.table_names[0] if session.duckdb_mgr.table_names else None)
        if not target_table:
            return json.dumps({"error": "No tables uploaded."})

        df = session.duckdb_mgr.execute_sql(f"SELECT * FROM {target_table}")
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            return json.dumps({"status": "error", "message": f"Table '{target_table}' has no numeric columns for anomaly detection."})

        ignored_substrings = ["id", "uuid", "pk", "key", "ids", "index"]
        analyzed_columns = []
        skipped_columns = []
        for col in numeric_df.columns:
            col_lower = col.lower()
            series = df[col].dropna()
            
            # Condition 1: Check for ignored substrings
            if any(sub in col_lower for sub in ignored_substrings):
                skipped_columns.append(col)
                continue
                
            # Condition 2: Check if categorical (few unique values)
            if len(series.unique()) < 10:
                skipped_columns.append(col)
                continue
                
            # Condition 3: Check if it's an index (monotonic increasing)
            if series.is_monotonic_increasing:
                skipped_columns.append(col)
                continue
                
            analyzed_columns.append(col)

        columns_to_check = [column_name] if column_name and column_name in analyzed_columns else analyzed_columns

        flagged_indices = set()
        anomaly_details = []

        for col in columns_to_check:
            series = df[col].dropna()
            if len(series) < 5:
                continue

            # 1. IQR Method
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            iqr_outliers = series[(series < lower_bound) | (series > upper_bound)].index.tolist()  # type: ignore

            # 2. Z-Score Method
            z_scores = np.abs(stats.zscore(series.to_numpy()))  # type: ignore
            z_outliers = series[z_scores > 3.0].index.tolist()  # type: ignore

            # 3. Isolation Forest
            try:
                iso = IsolationForest(contamination=0.03, random_state=42)  # type: ignore
                preds = iso.fit_predict(df[[col]].fillna(df[col].median()))
                iso_outliers = series[preds == -1].index.tolist()  # type: ignore
            except Exception:
                iso_outliers = []

            col_flagged = set(iqr_outliers).union(set(z_outliers)).union(set(iso_outliers))
            flagged_indices.update(col_flagged)

            for idx in col_flagged:
                anomaly_details.append({
                    "row_index": int(idx),
                    "column": col,
                    "value": float(df.loc[idx, col]),
                    "q1": float(q1),  # type: ignore
                    "q3": float(q3),  # type: ignore
                    "iqr_bounds": [float(lower_bound), float(upper_bound)]  # type: ignore
                })

        flagged_rows = df.loc[list(flagged_indices)].head(10)
        flagged_records = flagged_rows.to_dict(orient="records")

        # Generate Business Explanation via Groq Cloud LLM
        explanation = "No significant business anomalies detected."
        if flagged_records:
            try:
                llm = _get_llm()
                prompt_content = ANOMALY_EXPLANATION_PROMPT.format(
                    table_name=target_table,
                    column_stats=json.dumps(anomaly_details[:10]),
                    skipped_columns=json.dumps(skipped_columns),
                    outliers_data=json.dumps(flagged_records)
                )
                llm_response = llm.invoke(prompt_content)
                explanation = llm_response.content
            except Exception as e:
                logger.error(f"Error generating LLM anomaly explanation: {str(e)}")
                explanation = f"Flagged {len(flagged_records)} outlier records statistically based on IQR, Z-Score, and Isolation Forest."

        return json.dumps({
            "status": "success",
            "table_name": target_table,
            "analyzed_columns": analyzed_columns,
            "skipped_columns": skipped_columns,
            "skip_reason": "Identified as a primary key or identifier",
            "total_anomalies_flagged": len(flagged_indices),
            "flagged_rows": flagged_records,
            "business_explanation": explanation
        })


@tool
def insight_summary_tool(session_id: str, table_name: Optional[str] = None) -> str:
    """
    Generates business-level summary metrics, top/bottom performers, key drivers, and dataset health insights.
    
    Args:
        session_id: Active session ID.
        table_name: Optional table name to inspect.
    """
    with track_tool_latency("insight_summary_tool", session_id=session_id):
        session = session_store.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session '{session_id}' not found."})

        target_table = table_name or (session.duckdb_mgr.table_names[0] if session.duckdb_mgr.table_names else None)
        if not target_table:
            return json.dumps({"error": "No tables uploaded."})

        df = session.duckdb_mgr.execute_sql(f"SELECT * FROM {target_table}")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

        missing_values = df.isna().sum().to_dict()
        duplicate_rows = int(df.duplicated().sum())

        summary_stats = {
            "dataset_name": target_table,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": {k: int(v) for k, v in missing_values.items()},
            "duplicate_rows": duplicate_rows,
            "numeric_columns": num_cols,
            "categorical_columns": cat_cols,
            "date_columns": date_cols,
        }

        insight_prompt = (
            f"Given this dataset profile:\n{json.dumps(summary_stats, indent=2)}\n\n"
            "Provide a JSON object with EXACTLY these keys: "
            "'target_column_guess' (string or null), "
            "'business_domain_guess' (string), "
            "'top_insights' (list of strings), "
            "'data_quality_score' (string, e.g., '8/10'), "
            "'suggested_questions' (list of strings).\n"
            "If this dataset appears to be healthcare or medical related (e.g. patients, cardio, heart), "
            "ensure 'top_insights' explicitly includes these metrics if calculable or estimated from the data: "
            "Total Patients, Average Age, High Blood Pressure %, Obesity %, Diabetes %, Smokers %, Cardiovascular Disease %, Key Risk Factors, and Business Recommendations."
        )

        advanced_insights = {}
        try:
            llm = _get_llm()
            res = llm.invoke(insight_prompt)
            content = res.content if isinstance(res.content, str) else ""
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            advanced_insights = json.loads(content)
        except Exception as e:
            logger.error(f"Error generating advanced insights: {str(e)}")
            advanced_insights = {
                "target_column_guess": None,
                "business_domain_guess": "Unknown",
                "top_insights": ["Could not generate insights."],
                "data_quality_score": "Unknown",
                "suggested_questions": []
            }
            
        summary_stats.update(advanced_insights)

        return json.dumps({
            "status": "success",
            "table_name": target_table,
            "summary": summary_stats
        })


@lru_cache(maxsize=128)
def _generate_sql_cached(schema_str: str, question: str) -> str:
    """Cached inner function for LLM SQL generation."""
    sql_prompt = (
        f"Given the following database tables and schema:\n"
        f"{schema_str}\n\n"
        f"Generate code to answer this user question:\n"
        f"'{question}'\n\n"
        f"Provide BOTH:\n"
        f"1. A valid DuckDB SQL query inside a markdown ```sql code block.\n"
        f"2. The equivalent Pandas DataFrame python code (assuming df is already loaded) inside a markdown ```python code block."
    )
    llm = _get_llm()
    res = llm.invoke(sql_prompt)
    return res.content if isinstance(res.content, str) else ""

@tool
def sql_generation_tool(session_id: str, natural_language_question: str) -> str:
    """
    Converts a natural language question into a clean, readable DuckDB SQL query string based on session schema.
    
    Args:
        session_id: Active session ID.
        natural_language_question: User question in plain language.
    """
    with track_tool_latency("sql_generation_tool", session_id=session_id):
        session = session_store.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session '{session_id}' not found."})

        schema_info = session.duckdb_mgr.get_schema_summary()
        schema_str = json.dumps(schema_info, indent=2)

        try:
            raw_text = _generate_sql_cached(schema_str, natural_language_question)
            
            # Extract SQL code snippet
            generated_sql = ""
            if "```sql" in raw_text:
                generated_sql = raw_text.split("```sql")[1].split("```")[0].strip()
            
            # Extract Python code snippet
            generated_pandas = ""
            if "```python" in raw_text:
                generated_pandas = raw_text.split("```python")[1].split("```")[0].strip()

            return json.dumps({
                "status": "success",
                "question": natural_language_question,
                "generated_sql": generated_sql,
                "generated_pandas": generated_pandas
            })
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})


ALL_AGENT_TOOLS = [
    query_data_tool,
    generate_chart_tool,
    anomaly_detection_tool,
    insight_summary_tool,
    sql_generation_tool
]
