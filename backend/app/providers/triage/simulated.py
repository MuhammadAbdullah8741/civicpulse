import os

from app.providers.triage.base import TriageResult
from app.providers.triage.rules import RuleBasedTriage


class SimulatedTriage:
    name = "simulated"

    def __init__(self, mode: str | None = None):
        self.mode = mode or os.environ.get("SIMULATED_MODE", "success")

    def triage(self, text: str, location: str) -> TriageResult:
        if self.mode == "error":
            raise RuntimeError("Simulated provider failure")

        if self.mode == "malformed":
            return TriageResult.model_validate({
                "category": "not_a_valid_category",
                "priority": "urgent",
                "summary": "Invalid simulated response",
                "confidence": 2,
            })

        if self.mode != "success":
            raise ValueError("Unknown simulated provider mode")

        return RuleBasedTriage().triage(text, location)
