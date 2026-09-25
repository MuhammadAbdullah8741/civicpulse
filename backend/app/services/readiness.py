from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.providers.cache import check_cache
from app.repositories.database import check_database


def dependency_status() -> dict[str, str]:
    results = {}

    try:
        check_database()
        results["postgres"] = "ok"
    except SQLAlchemyError:
        results["postgres"] = "unavailable"

    try:
        check_cache()
        results["redis"] = "ok"
    except RedisError:
        results["redis"] = "unavailable"

    return results
