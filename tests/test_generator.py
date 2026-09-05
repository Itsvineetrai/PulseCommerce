import random
from datetime import datetime

from pulsecommerce.generator.personas import (
    Persona,
    get_persona_profile,
)
from pulsecommerce.generator.session_generator import (
    generate_session,
)


def test_session_has_required_boundary_events() -> None:
    persona = Persona.HIGH_INTENT_BUYER
    profile = get_persona_profile(persona)

    events = generate_session(
        user_id="USR-TEST-001",
        persona=persona,
        profile=profile,
        session_start=datetime(2026, 1, 1, 10, 0, 0),
        rng=random.Random(42),
    )

    assert events[0]["event_name"] == "session_start"
    assert events[-1]["event_name"] == "session_end"


def test_session_events_are_time_ordered() -> None:
    persona = Persona.HIGH_INTENT_BUYER
    profile = get_persona_profile(persona)

    events = generate_session(
        user_id="USR-TEST-002",
        persona=persona,
        profile=profile,
        session_start=datetime(2026, 1, 1, 10, 0, 0),
        rng=random.Random(42),
    )

    timestamps = [
        event["event_timestamp"]
        for event in events
    ]

    assert timestamps == sorted(timestamps)


def test_session_has_stable_identity() -> None:
    persona = Persona.HIGH_INTENT_BUYER
    profile = get_persona_profile(persona)

    events = generate_session(
        user_id="USR-TEST-003",
        persona=persona,
        profile=profile,
        session_start=datetime(2026, 1, 1, 10, 0, 0),
        rng=random.Random(42),
    )

    user_ids = {
        event["user_id"]
        for event in events
    }

    session_ids = {
        event["session_id"]
        for event in events
    }

    assert user_ids == {"USR-TEST-003"}
    assert len(session_ids) == 1


def test_events_follow_experiment_assignment() -> None:
    persona = Persona.HIGH_INTENT_BUYER
    profile = get_persona_profile(persona)

    events = generate_session(
        user_id="USR-TEST-004",
        persona=persona,
        profile=profile,
        session_start=datetime(2026, 1, 1, 10, 0, 0),
        rng=random.Random(42),
    )

    experiment_ids = {
        event["experiment_id"]
        for event in events
    }

    variants = {
        event["variant"]
        for event in events
    }

    assert experiment_ids == {"EXP-001"}
    assert len(variants) == 1


def test_event_ids_are_unique() -> None:
    persona = Persona.WINDOW_SHOPPER
    profile = get_persona_profile(persona)

    events = generate_session(
        user_id="USR-TEST-005",
        persona=persona,
        profile=profile,
        session_start=datetime(2026, 1, 1, 10, 0, 0),
        rng=random.Random(42),
    )

    event_ids = [
        event["event_id"]
        for event in events
    ]

    assert len(event_ids) == len(set(event_ids))