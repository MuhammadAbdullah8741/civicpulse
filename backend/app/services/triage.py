import logging

from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.rules import RuleBasedTriage

logger = logging.getLogger(__name__)


def triage_with_fallback(
    provider: TriageProvider,
    text: str,
    location: str,
    complaint_id: str,
) -> tuple[TriageResult, str]:
    try:
        result = provider.triage(text, location)
        if isinstance(result, TriageResult):
            result = result.model_dump()
        validated = TriageResult.model_validate(result)
        return validated, provider.name
    except Exception as error:
        # Do not log complaint text, contact details, or provider error text.
        logger.warning(
            "triage_fallback complaint_id=%s provider=%s error_class=%s",
            complaint_id,
            provider.name,
            type(error).__name__,
        )
        fallback = RuleBasedTriage().triage(text, location)
        return fallback, "rules:fallback"
