import json
import logging
import os

from pydantic import BaseModel, ValidationError
from redis.exceptions import RedisError

from app.providers.cache import get_cache
from app.repositories.stats import aggregate

TTL_SECONDS = 30


class StatsResponse(BaseModel):
    total: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]


def keys() -> tuple[str, str]:
    prefix = os.getenv("STATS_REDIS_PREFIX", "civicpulse:stats:v1")
    return prefix + ":generation", prefix + ":data"


STORE_IF_CURRENT = """
if (redis.call('GET', KEYS[1]) or '0') == ARGV[1] then
    return redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
end
return nil
"""


def invalidate() -> None:
    generation_key, data_key = keys()
    try:
        pipe = get_cache().pipeline(transaction=True)
        pipe.incr(generation_key)
        pipe.delete(data_key)
        pipe.execute()
    except RedisError:
        logging.getLogger(__name__).warning("stats_invalidation_unavailable")


def get_stats() -> tuple[dict, str]:
    generation_key, data_key = keys()
    client = get_cache()
    try:
        pipe = client.pipeline(transaction=True)
        pipe.get(generation_key)
        pipe.get(data_key)
        generation, raw = pipe.execute()
        if raw is not None:
            try:
                return StatsResponse.model_validate_json(raw).model_dump(), "HIT"
            except ValidationError:
                client.delete(data_key)
    except RedisError:
        return aggregate(), "MISS"

    data = aggregate()
    try:
        client.eval(STORE_IF_CURRENT, 2, generation_key, data_key,
                    str(generation or "0"), json.dumps(data), TTL_SECONDS)
    except RedisError:
        pass
    return data, "MISS"
