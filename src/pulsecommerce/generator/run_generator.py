"""Command-line entry point for PulseCommerce event generation."""

from __future__ import annotations

import argparse
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from pulsecommerce.generator.batch_writer import write_event_batch
from pulsecommerce.generator.personas import (
    PERSONA_PROFILES,
    Persona,
    get_persona_profile,
)
from pulsecommerce.generator.session_generator import generate_session


DEFAULT_OUTPUT_DIRECTORY = Path("data/landing/events")


def choose_persona(rng: random.Random) -> Persona:
    """Select a persona according to configured persona weights."""

    personas = list(PERSONA_PROFILES.keys())
    weights = [
        PERSONA_PROFILES[persona].weight
        for persona in personas
    ]

    return rng.choices(
        personas,
        weights=weights,
        k=1,
    )[0]


def generate_batch(
    *,
    batch_number: int,
    users_per_batch: int,
    sessions_per_user: int,
    start_time: datetime,
    rng: random.Random,
) -> tuple[list[dict], Counter[Persona]]:
    """Generate one micro-batch of synthetic user events."""

    events: list[dict] = []
    persona_counts: Counter[Persona] = Counter()

    for user_number in range(users_per_batch):
        user_id = (
            f"USR-{batch_number:04d}-{user_number:06d}"
        )

        persona = choose_persona(rng)
        profile = get_persona_profile(persona)

        persona_counts[persona] += 1

        user_start_time = (
            start_time
            + timedelta(
                seconds=rng.randint(
                    0,
                    60 * 30,
                )
            )
        )

        for session_number in range(sessions_per_user):
            session_start = (
                user_start_time
                + timedelta(
                    hours=session_number * rng.randint(1, 12)
                )
            )

            session_events = generate_session(
                user_id=user_id,
                persona=persona,
                profile=profile,
                session_start=session_start,
                rng=rng,
            )

            events.extend(session_events)

    events.sort(
        key=lambda event: (
            event["event_timestamp"],
            event["event_id"],
        )
    )

    return events, persona_counts


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic PulseCommerce "
            "e-commerce event micro-batches."
        )
    )

    parser.add_argument(
        "--batches",
        type=int,
        default=5,
        help="Number of micro-batches to generate.",
    )

    parser.add_argument(
        "--users-per-batch",
        type=int,
        default=100,
        help="Number of users represented in each batch.",
    )

    parser.add_argument(
        "--sessions-per-user",
        type=int,
        default=2,
        help="Number of sessions generated per user.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible generation.",
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help="Landing directory for Parquet micro-batches.",
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate generator arguments."""

    if args.batches < 1:
        raise ValueError("--batches must be at least 1.")

    if args.users_per_batch < 1:
        raise ValueError(
            "--users-per-batch must be at least 1."
        )

    if args.sessions_per_user < 1:
        raise ValueError(
            "--sessions-per-user must be at least 1."
        )


def main() -> None:
    """Generate synthetic event micro-batches."""

    args = parse_arguments()

    validate_arguments(args)

    rng = random.Random(args.seed)

    generation_start = datetime.now().replace(
        microsecond=0
    )

    total_events = 0
    total_personas: Counter[Persona] = Counter()

    print("PulseCommerce Event Generator")
    print("-" * 40)
    print(f"Batches: {args.batches}")
    print(
        f"Users per batch: {args.users_per_batch}"
    )
    print(
        f"Sessions per user: "
        f"{args.sessions_per_user}"
    )
    print(f"Random seed: {args.seed}")
    print(
        f"Output directory: "
        f"{args.output_directory}"
    )
    print("-" * 40)

    for batch_number in range(
        1,
        args.batches + 1,
    ):
        batch_start_time = (
            generation_start
            + timedelta(
                minutes=(batch_number - 1) * 30
            )
        )

        events, persona_counts = generate_batch(
            batch_number=batch_number,
            users_per_batch=args.users_per_batch,
            sessions_per_user=args.sessions_per_user,
            start_time=batch_start_time,
            rng=rng,
        )

        output_path = write_event_batch(
            events=events,
            batch_number=batch_number,
            output_directory=args.output_directory,
        )

        total_events += len(events)
        total_personas.update(persona_counts)

        print(
            f"Batch {batch_number:06d} | "
            f"events={len(events):,} | "
            f"file={output_path.name}"
        )

    print("-" * 40)
    print(f"Total events generated: {total_events:,}")
    print("Persona distribution:")

    for persona, count in total_personas.items():
        print(
            f"  {persona.value}: {count:,}"
        )


if __name__ == "__main__":
    main()