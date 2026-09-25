from itertools import product

import pytest
from pydantic import ValidationError

from app.schemas import ComplaintCreate, Status, StatusUpdate
from app.services.status import (
    InvalidTransitionError,
    allowed_transitions,
    validate_transition,
)


VALID_PAIRS = {
    (Status.OPEN, Status.IN_PROGRESS),
    (Status.OPEN, Status.REJECTED),
    (Status.IN_PROGRESS, Status.RESOLVED),
    (Status.IN_PROGRESS, Status.REJECTED),
}


@pytest.mark.parametrize(
    "current,requested",
    list(product(Status, repeat=2)),
)
def test_status_transition_contract(current, requested):
    if (current, requested) in VALID_PAIRS:
        validate_transition(current, requested)
    else:
        with pytest.raises(InvalidTransitionError) as error:
            validate_transition(current, requested)

        assert str(error.value) == (
            f"Invalid status transition: {current.value} -> {requested.value}"
        )


@pytest.mark.parametrize("status", [Status.RESOLVED, Status.REJECTED])
def test_terminal_status_has_no_actions(status):
    assert allowed_transitions(status) == []


def test_complaint_trims_surrounding_whitespace():
    complaint = ComplaintCreate(
        text="  Water pipe is leaking outside our house.  ",
        location="  Street 12  ",
    )
    assert complaint.text == "Water pipe is leaking outside our house."
    assert complaint.location == "Street 12"
    assert complaint.reporter_contact is None


@pytest.mark.parametrize(
    "changes",
    [
        {"text": "short"},
        {"text": "x" * 2001},
        {"text": " " * 20},
        {"location": "ab"},
        {"location": "x" * 201},
        {"location": "   "},
        {"category": "water"},
        {"priority": "high"},
        {"status": "resolved"},
    ],
)
def test_invalid_or_server_owned_fields_are_rejected(changes):
    data = {
        "text": "Water pipe is leaking outside our house.",
        "location": "Street 12",
    }
    data.update(changes)

    with pytest.raises(ValidationError):
        ComplaintCreate.model_validate(data)


@pytest.mark.parametrize(
    "text_length,location_length",
    [(10, 3), (2000, 200)],
)
def test_input_length_boundaries_are_accepted(text_length, location_length):
    complaint = ComplaintCreate(
        text="x" * text_length,
        location="y" * location_length,
    )
    assert len(complaint.text) == text_length
    assert len(complaint.location) == location_length


def test_unknown_status_is_rejected():
    with pytest.raises(ValidationError):
        StatusUpdate(status="closed")
