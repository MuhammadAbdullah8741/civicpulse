import os

from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def create_provider() -> TriageProvider:
    selected = os.environ.get("TRIAGE_PROVIDER", "simulated").lower()

    if selected == "rules":
        return RuleBasedTriage()
    if selected == "simulated":
        return SimulatedTriage()
    if selected == "llm":
        return LLMTriage()

    raise ValueError(f"Unsupported TRIAGE_PROVIDER: {selected}")
