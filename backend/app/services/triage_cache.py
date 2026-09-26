"""Validated read-through triage cache and bounded, shared provider history."""
import hashlib
import json
import os
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from redis.exceptions import RedisError

from app.providers.cache import get_cache
from app.providers.triage.base import TriageProvider, TriageResult
from app.services.triage import triage_with_fallback

CACHE_TTL_SECONDS = 86400


def prefix() -> str:
    return os.environ.get("TRIAGE_REDIS_PREFIX", "civicpulse:triage:v1")


def cache_key(provider: TriageProvider, text: str, location: str) -> str:
    model = None
    if provider.name == "llm:groq":
        model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    elif provider.name == "llm:ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    material = json.dumps({
        "provider": provider.name,
        "model": model,
        "mode": getattr(provider, "mode", None),
        "text": text,
        "location": location,
    }, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return prefix() + ":result:" + digest


def record_outcome(provider: str, latency_ms: int, cache_hit: bool) -> None:
    outcome = {
        "provider": provider,
        "latency_ms": latency_ms,
        "fallback": provider == "rules:fallback",
        "cache_hit": cache_hit,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    try:
        pipe = get_cache().pipeline(transaction=True)
        pipe.lpush(prefix() + ":recent", json.dumps(outcome))
        pipe.ltrim(prefix() + ":recent", 0, 19)
        pipe.hincrby(prefix() + ":counts", "total", 1)
        pipe.hincrby(prefix() + ":counts", "hits", int(cache_hit))
        pipe.execute()
    except RedisError:
        # Recording telemetry must not discard a valid complaint.
        pass


def triage_with_cache(
    provider: TriageProvider,
    text: str,
    location: str,
    complaint_id: str,
) -> tuple[TriageResult, str]:
    started = perf_counter()
    key = cache_key(provider, text, location)
    result = None
    try:
        raw = get_cache().get(key)
        if raw is not None:
            try:
                result = TriageResult.model_validate_json(raw)
            except ValueError:
                get_cache().delete(key)
    except RedisError:
        pass

    cache_hit = result is not None
    actual_provider = provider.name
    if result is None:
        result, actual_provider = triage_with_fallback(
            provider, text, location, complaint_id
        )
        # A temporary provider outage must not poison its cache for 24 hours.
        if actual_provider != "rules:fallback":
            try:
                get_cache().setex(key, CACHE_TTL_SECONDS, result.model_dump_json())
            except RedisError:
                pass

    latency_ms = max(0, round((perf_counter() - started) * 1000))
    record_outcome(actual_provider, latency_ms, cache_hit)
    return result, actual_provider


def provider_metadata(active_provider: str) -> dict[str, Any]:
    pipe = get_cache().pipeline(transaction=True)
    pipe.hgetall(prefix() + ":counts")
    pipe.lrange(prefix() + ":recent", 0, 19)
    counts, recent = pipe.execute()
    total = int(counts.get("total", 0))
    hits = int(counts.get("hits", 0))
    return {
        "active_provider": active_provider,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "triage_requests": total,
        "cache_hits": hits,
        "cache_hit_rate": hits / total if total else 0.0,
        "recent_outcomes": [json.loads(row) for row in recent],
    }
