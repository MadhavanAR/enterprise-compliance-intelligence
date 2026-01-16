"""
Structured logging with observability features
- Trace IDs for request tracking
- Latency tracking
- Token usage logging
- JSON-structured logs
"""
import logging
import json
import time
import uuid
from typing import Optional, Dict, Any
from rag.config import (
    LOG_LEVEL,
    ENABLE_STRUCTURED_LOGS,
    LOG_TRACE_IDS,
    LOG_LATENCIES,
    LOG_TOKEN_USAGE
)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("rag")

class StructuredLogger:
    """Enhanced logger with trace IDs and structured logging."""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or (str(uuid.uuid4()) if LOG_TRACE_IDS else None)
        self._latency_start = {}
    
    def _log(self, level: str, message: str, **kwargs):
        """Log with structured data."""
        data = {
            "message": message,
            **kwargs
        }
        
        if self.trace_id:
            data["trace_id"] = self.trace_id
        
        if ENABLE_STRUCTURED_LOGS:
            # JSON format for log aggregators
            log_msg = json.dumps(data)
        else:
            # Human-readable format
            parts = [message]
            for key, value in kwargs.items():
                parts.append(f"{key}={value}")
            if self.trace_id:
                parts.append(f"trace_id={self.trace_id}")
            log_msg = " | ".join(parts)
        
        getattr(logger, level.lower())(log_msg)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def start_timer(self, stage: str):
        """Start latency tracking for a stage."""
        if LOG_LATENCIES:
            self._latency_start[stage] = time.time()
    
    def end_timer(self, stage: str, **metadata):
        """End latency tracking and log."""
        if LOG_LATENCIES and stage in self._latency_start:
            latency_ms = (time.time() - self._latency_start[stage]) * 1000
            self.info(f"Stage complete: {stage}", latency_ms=round(latency_ms, 2), **metadata)
            del self._latency_start[stage]
            return latency_ms
        return None
    
    def log_token_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
        """Log token usage."""
        if LOG_TOKEN_USAGE:
            self.info("Token usage", 
                     prompt_tokens=prompt_tokens,
                     completion_tokens=completion_tokens,
                     total_tokens=total_tokens)

# Global logger instance (backward compatibility)
def get_logger(trace_id: Optional[str] = None) -> StructuredLogger:
    """Get a logger instance with optional trace ID."""
    return StructuredLogger(trace_id)

# Default logger for backward compatibility
default_logger = StructuredLogger()
