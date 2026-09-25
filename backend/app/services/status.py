from app.schemas import Status


TRANSITIONS: dict[Status, tuple[Status, ...]] = {
    Status.OPEN: (Status.IN_PROGRESS, Status.REJECTED),
    Status.IN_PROGRESS: (Status.RESOLVED, Status.REJECTED),
    Status.RESOLVED: (),
    Status.REJECTED: (),
}


class InvalidTransitionError(ValueError):
    pass


def allowed_transitions(current: Status) -> list[Status]:
    return list(TRANSITIONS[current])


def validate_transition(current: Status, requested: Status) -> None:
    if requested not in TRANSITIONS[current]:
        raise InvalidTransitionError(
            f"Invalid status transition: {current.value} -> {requested.value}"
        )
