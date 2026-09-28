from app.schemas import Status
from app.services.status import allowed_transitions


def test_resolved_reports_are_terminal():
    # Resolved complaints are terminal and expose no further status actions.
    assert allowed_transitions(Status.RESOLVED) == []
