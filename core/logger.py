"""
Structured Logging and Latency Tracker for DataMind AI.
"""
import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as JSON objects for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        tool_name = getattr(record, "tool_name", None)
        if tool_name is not None:
            log_object["tool_name"] = tool_name
        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            log_object["duration_ms"] = duration_ms
        session_id = getattr(record, "session_id", None)
        if session_id is not None:
            log_object["session_id"] = session_id
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_object)


def setup_logger(name: str = "datamind_ai", log_level: str = "INFO") -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Console Handler (Human-readable / JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(console_handler)

    # File Handler (JSON structured log file)
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


@contextmanager
def track_tool_latency(tool_name: str, session_id: str = "unknown") -> Generator[None, None, None]:
    """Context manager to measure and log tool execution latency."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"Tool '{tool_name}' executed in {elapsed_ms} ms",
            extra={"tool_name": tool_name, "duration_ms": elapsed_ms, "session_id": session_id}
        )
