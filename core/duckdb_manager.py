"""
DuckDB Session Manager for high-performance SQL querying over uploaded CSVs.
"""
from typing import Dict, List, Any
import duckdb
import pandas as pd
from core.logger import logger
from functools import lru_cache


class DuckDBManager:
    """Manages DuckDB in-memory database instance per session."""

    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")
        self.table_names: List[str] = []

    def register_dataframe(self, table_name: str, df: pd.DataFrame) -> str:
        """Registers a pandas DataFrame as a DuckDB table."""
        # Clean table name to be SQL compliant
        clean_name = "".join([c if c.isalnum() else "_" for c in table_name]).lower()
        if not clean_name[0].isalpha():
            clean_name = f"df_{clean_name}"
            
        self.conn.register(clean_name, df)
        if clean_name not in self.table_names:
            self.table_names.append(clean_name)
        logger.info(f"Registered table '{clean_name}' with {len(df)} rows into DuckDB")
        return clean_name

    @lru_cache(maxsize=128)
    def execute_sql(self, query: str) -> pd.DataFrame:
        """Executes a SQL query and returns the result as a DataFrame."""
        try:
            logger.info(f"Executing DuckDB SQL: {query}")
            result_df = self.conn.execute(query).df()
            return result_df
        except Exception as e:
            logger.error(f"SQL Execution Error: {str(e)} | Query: {query}")
            raise ValueError(f"DuckDB SQL Execution Error: {str(e)}")

    def get_schema_summary(self) -> Dict[str, Any]:
        """Returns schemas and row counts of all registered tables."""
        schema_info = {}
        for table in self.table_names:
            df = self.conn.execute(f"SELECT * FROM {table} LIMIT 5").df()
            res = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            count = res[0] if res else 0
            schema_info[table] = {
                "row_count": count,
                "columns": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
                "sample_rows": df.head(3).to_dict(orient="records")
            }
        return schema_info

    def infer_joins(self) -> List[Dict[str, str]]:
        """Infers potential common join keys between uploaded tables."""
        if len(self.table_names) < 2:
            return []

        join_suggestions = []
        table_cols = {}
        for table in self.table_names:
            df = self.conn.execute(f"SELECT * FROM {table} LIMIT 1").df()
            table_cols[table] = set(df.columns)

        for i in range(len(self.table_names)):
            for j in range(i + 1, len(self.table_names)):
                t1, t2 = self.table_names[i], self.table_names[j]
                common = table_cols[t1].intersection(table_cols[t2])
                for col in common:
                    join_suggestions.append({
                        "table1": t1,
                        "table2": t2,
                        "common_key": col,
                        "sql_snippet": f"SELECT * FROM {t1} JOIN {t2} ON {t1}.{col} = {t2}.{col}"
                    })
        return join_suggestions
