import os

from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def create_provider() -> TriageProvider:
    selected = os.environ.get("TRIAGE_PROVIDER", "simulated").lower()

    if selected == "rules":
        return RuleBasedTriage()
    if selected == "simulated":
        return SimulatedTriage()

    raise ValueError(f"Unsupported TRIAGE_PROVIDER: {selected}")
