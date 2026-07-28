"""
Upload API Endpoints for DataMind AI.
"""
import io
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd

from core.config import settings
from core.session import session_store
from api.schemas import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_csv_files(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Accepts one or more CSV files, validates schema/encoding/size limits,
    loads them into session DuckDB tables, and returns data quality report.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    session = session_store.get_or_create_session(session_id)
    uploaded_names = []
    registered_tables = []

    for file in files:
        file.file.seek(0, 2)
        size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)
        
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' size ({size_mb:.1f}MB) exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB."
            )

        if not file.filename or not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is not a CSV file.")

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is empty (0 bytes).")

        df = None
        for encoding in ["utf-8", "latin1", "cp1252", "iso-8859-1"]:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                break
            except Exception:
                continue

        if df is None:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV '{file.filename}'. Malformed or unreadable encoding.")

        if df.empty:
            raise HTTPException(status_code=400, detail=f"CSV '{file.filename}' contains no data rows.")

        table_name = session.add_dataset(file.filename or "file.csv", df)
        uploaded_names.append(file.filename)
        registered_tables.append(table_name)

    return UploadResponse(
        session_id=session.session_id,
        uploaded_files=uploaded_names,
        tables_registered=registered_tables,
        quality_report=session.quality_report,
        message=f"Successfully uploaded and validated {len(uploaded_names)} CSV file(s)."
    )
