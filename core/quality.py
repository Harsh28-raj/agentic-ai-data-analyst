"""
Data Quality Checker for uploaded CSV datasets.
"""
from typing import Dict, Any
import pandas as pd


def audit_dataset_quality(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Performs comprehensive data quality checks across single or multiple dataframes.
    Returns audit details including missing values, duplicates, and data type summaries.
    """
    report = {
        "datasets": {},
        "overall_health_score": 100.0,
        "warnings": [],
        "inferred_relationships": []
    }

    total_datasets = len(dataframes)
    if total_datasets == 0:
        return report

    penalty_points = 0.0

    for name, df in dataframes.items():
        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows == 0:
            report["warnings"].append(f"Dataset '{name}' is empty (0 rows).")
            penalty_points += 30.0
            continue

        # Missing values
        missing_counts = df.isnull().sum().to_dict()
        missing_percentages = {col: round((count / total_rows) * 100, 2) for col, count in missing_counts.items()}
        total_missing = sum(missing_counts.values())

        if total_missing > 0:
            high_missing = [col for col, pct in missing_percentages.items() if pct > 20.0]
            if high_missing:
                report["warnings"].append(f"Dataset '{name}' has >20% missing values in columns: {', '.join(high_missing)}")
                penalty_points += 10.0

        # Duplicate rows
        duplicate_count = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_count / total_rows) * 100, 2)
        if duplicate_count > 0:
            report["warnings"].append(f"Dataset '{name}' contains {duplicate_count} duplicate rows ({duplicate_pct}%).")
            penalty_points += 5.0

        # Column data types & stats
        col_types = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetime64"]).columns.tolist()

        report["datasets"][name] = {
            "row_count": total_rows,
            "column_count": total_cols,
            "duplicate_rows": duplicate_count,
            "duplicate_pct": duplicate_pct,
            "total_missing_cells": total_missing,
            "missing_percentages": missing_percentages,
            "column_types": col_types,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols
        }

    # Calculate overall health score
    health_score = max(0.0, min(100.0, 100.0 - penalty_points))
    report["overall_health_score"] = round(health_score, 1)

    # Multi-file relationship inference
    table_names = list(dataframes.keys())
    if len(table_names) > 1:
        for i in range(len(table_names)):
            for j in range(i + 1, len(table_names)):
                t1, t2 = table_names[i], table_names[j]
                common_cols = set(dataframes[t1].columns).intersection(set(dataframes[t2].columns))
                for col in common_cols:
                    report["inferred_relationships"].append({
                        "table1": t1,
                        "table2": t2,
                        "key": col,
                        "description": f"Common key '{col}' found between {t1} and {t2}"
                    })

    return report
