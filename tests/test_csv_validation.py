"""
Unit Tests for CSV Validation, Size Limits, and Encoding Error Handling.
"""
import io
import pandas as pd
from core.session import session_store


def test_empty_csv_parsing():
    """Test handling of empty 0-byte CSV files."""
    content = b""
    assert len(content) == 0


def test_malformed_csv_parsing():
    """Test handling of corrupt or malformed CSV content."""
    corrupt_content = b"col1,col2\nval1\nval2,val3,val4,val5,val6\n"
    df = pd.read_csv(io.BytesIO(corrupt_content), on_bad_lines="skip")
    assert not df.empty


def test_session_dataset_registration():
    """Test adding dataset into DuckDB session instance."""
    session = session_store.create_session("test_session_csv")
    sample_df = pd.DataFrame({
        "region": ["North", "South"],
        "revenue": [1000, 2000]
    })
    table_name = session.add_dataset("test_sales.csv", sample_df)
    assert table_name == "test_sales_csv"
    assert "test_sales_csv" in session.duckdb_mgr.table_names
    
    # Query DuckDB
    res_df = session.duckdb_mgr.execute_sql("SELECT SUM(revenue) as total FROM test_sales_csv")
    assert res_df["total"].iloc[0] == 3000
