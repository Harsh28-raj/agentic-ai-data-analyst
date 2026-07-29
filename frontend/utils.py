"""
HTTP Client Utilities for Streamlit Frontend connecting to FastAPI Backend.
"""
import os
import requests
import json
from typing import List, Dict, Any, Optional

from config import BACKEND_URL


def upload_files(files_data: List[tuple]) -> Dict[str, Any]:
    """
    Sends CSV files to backend /upload endpoint.
    files_data format: [('files', (filename, file_bytes, 'text/csv'))]
    """
    url = f"{BACKEND_URL}/upload"
    try:
        response = requests.post(url, files=files_data, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            return {"error": e.response.json().get("detail", str(e))}
        return {"error": f"Failed to connect to backend at {BACKEND_URL}: {str(e)}"}


def post_chat(session_id: str, query: str) -> Dict[str, Any]:
    """Sends chat query to backend /chat endpoint."""
    url = f"{BACKEND_URL}/chat"
    payload = {"session_id": session_id, "query": query}
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            return {"error": e.response.json().get("detail", str(e))}
        return {"error": str(e)}


def stream_chat(session_id: str, query: str):
    """Generator function that streams tokens from backend /chat/stream SSE endpoint."""
    url = f"{BACKEND_URL}/chat/stream"
    payload = {
        "session_id": session_id,
        "query": query
    }

    try:
        with requests.post(
            url,
            json=payload,
            stream=True,
            timeout=180
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):

                if not line:
                    continue

                if not line.startswith("data:"):
                    continue

                data = line[5:].strip()

                try:
                    chunk = json.loads(data)
                    yield chunk

                except json.JSONDecodeError:
                    import ast
                    try:
                        chunk = ast.literal_eval(data)
                        yield chunk
                    except Exception:
                        continue

    except Exception as e:
        yield {
            "type": "error",
            "content": str(e)
        }


def get_anomalies(session_id: str, table_name: Optional[str] = None) -> Dict[str, Any]:
    """Triggers anomaly detection via backend /anomalies endpoint."""
    url = f"{BACKEND_URL}/anomalies"
    payload = {"session_id": session_id, "table_name": table_name}
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            return {"error": e.response.json().get("detail", str(e))}
        return {"error": str(e)}


def get_health() -> Dict[str, Any]:
    """Checks backend health status."""
    url = f"{BACKEND_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_dashboard_stats(session_id: str) -> Dict[str, Any]:
    """Fetches comprehensive dashboard statistics for visualizations."""
    url = f"{BACKEND_URL}/dashboard/{session_id}/stats"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            return {"error": e.response.json().get("detail", str(e))}
        return {"error": str(e)}
