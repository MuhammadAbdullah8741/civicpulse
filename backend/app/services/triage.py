import logging
from random import uniform
from time import sleep

import httpx

from app.observability import FALLBACKS
from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.rules import RuleBasedTriage

logger = logging.getLogger(__name__)


def retryable(error: Exception) -> bool:
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        return status == 429 or 500 <= status <= 599
    return False


def triage_with_fallback(
    provider: TriageProvider,
    text: str,
    location: str,
    complaint_id: str,
) -> tuple[TriageResult, str]:
    for attempt in range(2):
        try:
            result = provider.triage(text, location)
            # Revalidate model fields as well as malformed third-party responses.
            raw: object = result.model_dump() if isinstance(result, TriageResult) else result
            return TriageResult.model_validate(raw), provider.name
        except Exception as error:
            if attempt == 0 and retryable(error):
                sleep(uniform(0.1, 0.3))
                continue

            FALLBACKS.inc()
            logger.warning("triage_fallback", extra={
                "complaint_id": complaint_id,
                "provider": provider.name,
                "error_class": type(error).__name__,
            })
            break

    fallback = RuleBasedTriage().triage(text, location)
    return fallback, "rules:fallback"
