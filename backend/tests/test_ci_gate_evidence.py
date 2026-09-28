from app.schemas import Status
from app.services.status import allowed_transitions


def test_resolved_reports_are_terminal():
    # Deliberately incorrect expectation for the CI enforcement demonstration.
    assert allowed_transitions(Status.RESOLVED) == [Status.OPEN]
