"""
Dashboard Statistics API Endpoints for DataMind AI.
"""
import numpy as np
from fastapi import APIRouter, HTTPException

from core.session import session_store
from core.logger import logger
from api.schemas import DashboardStatsResponse

router = APIRouter()

@router.get("/dashboard/{session_id}/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    if not session.dataframes:
        raise HTTPException(status_code=400, detail="No datasets uploaded in session.")

    table_name = list(session.dataframes.keys())[0]
    df = session.dataframes[table_name]

    try:
        kpis = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_cells": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_stats = {}
        distributions = {}
        if num_cols:
            numeric_stats = df[num_cols].describe().to_dict()
            for col in num_cols[:4]:
                counts, bin_edges = np.histogram(df[col].dropna(), bins=10)
                distributions[col] = {
                    "counts": counts.tolist(),
                    "bin_edges": bin_edges.tolist()
                }

        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        categorical_tops = {}
        for col in cat_cols[:4]:
            top_vals = df[col].value_counts().head(5).to_dict()
            categorical_tops[col] = {str(k): int(v) for k, v in top_vals.items()}

        correlation = {}
        scatter_candidates = []
        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr()
            correlation = corr_matrix.fillna(0).to_dict()
            
            corr_unstacked = corr_matrix.abs().unstack()
            corr_unstacked = corr_unstacked[corr_unstacked < 1.0]
            if not corr_unstacked.empty:
                top_pair = corr_unstacked.idxmax()
                scatter_candidates = list(top_pair)
            else:
                scatter_candidates = num_cols[:2]

        missing_values = df.isnull().sum().to_dict()

        return DashboardStatsResponse(
            session_id=session_id,
            kpis=kpis,
            numeric_stats=numeric_stats,
            categorical_tops=categorical_tops,
            correlation=correlation,
            missing_values=missing_values,
            distributions=distributions,
            scatter_candidates=scatter_candidates
        )
    except Exception as e:
        logger.error(f"Error computing dashboard stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error computing dashboard statistics: {str(e)}")
