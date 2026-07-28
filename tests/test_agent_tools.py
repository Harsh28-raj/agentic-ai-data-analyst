"""
Unit Tests for Isolated Agent Tools (query_data_tool, generate_chart_tool).
"""
import json
import pytest
import pandas as pd
from core.session import session_store
from agent.tools import query_data_tool, generate_chart_tool


@pytest.fixture
def setup_test_session():
    session = session_store.create_session("tool_test_session")
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [15000, 12000, 18000, 9000]
    })
    session.add_dataset("sales.csv", df)
    return session.session_id


def test_query_data_tool_execution(setup_test_session):
    """Test DuckDB SQL execution tool."""
    session_id = setup_test_session
    sql = "SELECT region, revenue FROM sales_csv WHERE revenue > 10000 ORDER BY revenue DESC"
    
    result_str = query_data_tool.invoke({"session_id": session_id, "sql_query": sql})
    res = json.loads(result_str)
    
    assert res["status"] == "success"
    assert res["row_count"] == 3
    assert res["data"][0]["region"] == "East"


def test_generate_chart_tool(setup_test_session):
    """Test Plotly chart spec generation tool."""
    session_id = setup_test_session
    result_str = generate_chart_tool.invoke({
        "session_id": session_id,
        "chart_type": "bar",
        "title": "Revenue by Region",
        "x_column": "region",
        "y_column": "revenue"
    })
    res = json.loads(result_str)
    
    assert res["status"] == "success"
    assert res["chart_spec"]["chart_type"] == "bar"
    assert res["chart_spec"]["title"] == "Revenue by Region"
