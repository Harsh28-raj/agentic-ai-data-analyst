"""
Thread-safe Session Manager for storing session data, DuckDB instances, and audit state.
"""
import uuid
import time
from typing import Dict, Any, Optional
import pandas as pd
from core.duckdb_manager import DuckDBManager
from core.quality import audit_dataset_quality
from core.logger import logger


class SessionState:
    """Encapsulates data and DB state for a single active session."""

    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.duckdb_mgr: DuckDBManager = DuckDBManager()
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.table_mapping: Dict[str, str] = {} # original file name -> clean table name
        self.quality_report: Dict[str, Any] = {}
        self.history: list = []
        self.last_accessed: float = time.time()

    def update_access_time(self):
        self.last_accessed = time.time()

    def add_dataset(self, filename: str, df: pd.DataFrame) -> str:
        """Adds a dataframe and registers it into session DuckDB instance."""
        self.update_access_time()
        clean_table_name = self.duckdb_mgr.register_dataframe(filename, df)
        self.dataframes[clean_table_name] = df
        self.table_mapping[filename] = clean_table_name
        self.quality_report = audit_dataset_quality(self.dataframes)
        logger.info(f"Session '{self.session_id}': Added dataset '{filename}' as table '{clean_table_name}'")
        return clean_table_name


class SessionStore:
    """Global registry of active sessions with TTL garbage collection."""

    def __init__(self, ttl_seconds: int = 3600):
        self.sessions: Dict[str, SessionState] = {}
        self.ttl_seconds = ttl_seconds

    def _cleanup_expired_sessions(self):
        """Removes sessions older than TTL to free up memory."""
        now = time.time()
        expired = [sid for sid, sess in self.sessions.items() if (now - sess.last_accessed) > self.ttl_seconds]
        for sid in expired:
            try:
                # Close duckdb connection to free memory
                self.sessions[sid].duckdb_mgr.conn.close()
            except Exception:
                pass
            del self.sessions[sid]
            logger.info(f"Garbage Collected expired session '{sid}'")

    def create_session(self, session_id: Optional[str] = None) -> SessionState:
        """Creates a new session state."""
        self._cleanup_expired_sessions()
        sid = session_id if session_id else str(uuid.uuid4())
        session = SessionState(sid)
        self.sessions[sid] = session
        logger.info(f"Created new session with ID: {sid}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieves an existing session state."""
        self._cleanup_expired_sessions()
        session = self.sessions.get(session_id)
        if session:
            session.update_access_time()
        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState:
        """Gets existing session or creates a new one."""
        self._cleanup_expired_sessions()
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_access_time()
            return session
        return self.create_session(session_id)


# Global Singleton Session Store
session_store = SessionStore()

