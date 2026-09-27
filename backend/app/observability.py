import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

from prometheus_client import Counter, Histogram

request_id: ContextVar[str] = ContextVar("request_id", default="system")
REQUESTS = Counter("civicpulse_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("civicpulse_request_duration_seconds", "HTTP latency", ["method", "route"],
                    buckets=(0.01, 0.05, 0.1, 0.5, 1, 5, 10, 25, 60))
TRIAGE_LATENCY = Histogram("civicpulse_triage_duration_seconds", "Triage latency including cache", ["provider"],
                           buckets=(0.001, 0.01, 0.1, 1, 5, 10, 25, 60))
FALLBACKS = Counter("civicpulse_triage_fallback_total", "Provider failures falling back to rules")


def metric_provider(name: str) -> str:
    return name if name in {"llm:groq", "llm:ollama", "rules", "simulated", "rules:fallback"} else "other"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "request_id": request_id.get(),
            "message": record.getMessage(),
        }
        for field in ("complaint_id", "provider", "error_class", "method", "route", "status", "latency_ms"):
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info and record.exc_info[0]:
            # Exception bodies may contain credentials or citizen input.
            data["error_class"] = record.exc_info[0].__name__
        return json.dumps(data)
