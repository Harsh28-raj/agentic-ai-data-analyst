"""
Pydantic Data Contracts and Schemas for DataMind AI REST API.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    session_id: str
    uploaded_files: List[str]
    tables_registered: List[str]
    quality_report: Dict[str, Any]
    message: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Active session identifier")
    query: str = Field(..., description="Natural language question or command")


class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    reasoning: str
    chart_spec: Optional[Dict[str, Any]] = None
    sql_code: Optional[str] = None
    pandas_code: Optional[str] = None


class StreamChunk(BaseModel):
    type: str # 'token', 'reasoning', 'chart', 'sql', 'complete', 'error'
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class AnomalyRequest(BaseModel):
    session_id: str
    table_name: Optional[str] = None
    column_name: Optional[str] = None


class AnomalyResponse(BaseModel):
    session_id: str
    table_name: str
    total_anomalies_flagged: int
    flagged_rows: List[Dict[str, Any]]
    business_explanation: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    message_count: int
    history: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    model: str
    active_sessions: int
    version: str = "1.0.0"


class DashboardStatsResponse(BaseModel):
    session_id: str
    kpis: Dict[str, Any]
    numeric_stats: Dict[str, Any]
    categorical_tops: Dict[str, Any]
    correlation: Dict[str, Any]
    missing_values: Dict[str, Any]
    distributions: Dict[str, Any]
    scatter_candidates: List[str]


class QueryCsvRequest(BaseModel):
    session_id: str
    sql_code: str

