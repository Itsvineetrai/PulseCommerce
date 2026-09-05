from pulsecommerce.generator.experiments import (
    CONTROL,
    TREATMENT,
    assign_variant,
)


def test_variant_assignment_is_stable() -> None:
    user_id = "USR-TEST-001"

    first_assignment = assign_variant(user_id)
    second_assignment = assign_variant(user_id)

    assert first_assignment == second_assignment


def test_variant_is_valid() -> None:
    variant = assign_variant("USR-TEST-002")

    assert variant in {CONTROL, TREATMENT}


def test_assignment_has_both_variants() -> None:
    assignments = {
        assign_variant(f"USR-{number:05d}")
        for number in range(1_000)
    }

    assert CONTROL in assignments
    assert TREATMENT in assignments