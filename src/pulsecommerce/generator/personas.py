"""Behavioral persona definitions for the PulseCommerce event generator.

Each persona defines the probabilistic behavior used to generate realistic
e-commerce sessions. These parameters are the synthetic ground truth that
later analytics and machine-learning phases should be able to discover.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Persona(StrEnum):
    """Supported behavioral personas."""

    WINDOW_SHOPPER = "window_shopper"
    HIGH_INTENT_BUYER = "high_intent_buyer"
    PRICE_SENSITIVE = "price_sensitive"
    MOBILE_FRICTION = "mobile_friction"
    RETURNING_BUYER = "returning_buyer"
    HIGH_RISK_CART = "high_risk_cart"


@dataclass(frozen=True, slots=True)
class PersonaProfile:
    """Probabilistic behavioral profile for a synthetic user persona."""

    name: Persona
    weight: float

    product_view_min: int
    product_view_max: int

    search_probability: float
    wishlist_probability: float

    add_to_cart_probability: float
    remove_from_cart_probability: float

    cart_view_probability: float
    checkout_probability: float

    payment_attempt_probability: float
    payment_error_probability: float

    purchase_probability: float

    mobile_probability: float

    min_event_gap_seconds: int
    max_event_gap_seconds: int

    cart_idle_min_seconds: int
    cart_idle_max_seconds: int


PERSONA_PROFILES: dict[Persona, PersonaProfile] = {
    Persona.WINDOW_SHOPPER: PersonaProfile(
        name=Persona.WINDOW_SHOPPER,
        weight=0.30,
        product_view_min=2,
        product_view_max=8,
        search_probability=0.35,
        wishlist_probability=0.08,
        add_to_cart_probability=0.12,
        remove_from_cart_probability=0.10,
        cart_view_probability=0.25,
        checkout_probability=0.08,
        payment_attempt_probability=0.90,
        payment_error_probability=0.08,
        purchase_probability=0.20,
        mobile_probability=0.60,
        min_event_gap_seconds=5,
        max_event_gap_seconds=120,
        cart_idle_min_seconds=30,
        cart_idle_max_seconds=300,
    ),
    Persona.HIGH_INTENT_BUYER: PersonaProfile(
        name=Persona.HIGH_INTENT_BUYER,
        weight=0.20,
        product_view_min=1,
        product_view_max=4,
        search_probability=0.15,
        wishlist_probability=0.03,
        add_to_cart_probability=0.85,
        remove_from_cart_probability=0.03,
        cart_view_probability=0.75,
        checkout_probability=0.80,
        payment_attempt_probability=0.98,
        payment_error_probability=0.02,
        purchase_probability=0.90,
        mobile_probability=0.45,
        min_event_gap_seconds=5,
        max_event_gap_seconds=60,
        cart_idle_min_seconds=10,
        cart_idle_max_seconds=90,
    ),
    Persona.PRICE_SENSITIVE: PersonaProfile(
        name=Persona.PRICE_SENSITIVE,
        weight=0.15,
        product_view_min=3,
        product_view_max=10,
        search_probability=0.50,
        wishlist_probability=0.35,
        add_to_cart_probability=0.55,
        remove_from_cart_probability=0.40,
        cart_view_probability=0.65,
        checkout_probability=0.35,
        payment_attempt_probability=0.95,
        payment_error_probability=0.05,
        purchase_probability=0.45,
        mobile_probability=0.55,
        min_event_gap_seconds=10,
        max_event_gap_seconds=180,
        cart_idle_min_seconds=60,
        cart_idle_max_seconds=900,
    ),
    Persona.MOBILE_FRICTION: PersonaProfile(
        name=Persona.MOBILE_FRICTION,
        weight=0.10,
        product_view_min=2,
        product_view_max=6,
        search_probability=0.25,
        wishlist_probability=0.05,
        add_to_cart_probability=0.65,
        remove_from_cart_probability=0.10,
        cart_view_probability=0.70,
        checkout_probability=0.75,
        payment_attempt_probability=0.98,
        payment_error_probability=0.45,
        purchase_probability=0.55,
        mobile_probability=0.95,
        min_event_gap_seconds=8,
        max_event_gap_seconds=150,
        cart_idle_min_seconds=45,
        cart_idle_max_seconds=600,
    ),
    Persona.RETURNING_BUYER: PersonaProfile(
        name=Persona.RETURNING_BUYER,
        weight=0.15,
        product_view_min=1,
        product_view_max=3,
        search_probability=0.10,
        wishlist_probability=0.02,
        add_to_cart_probability=0.92,
        remove_from_cart_probability=0.02,
        cart_view_probability=0.85,
        checkout_probability=0.90,
        payment_attempt_probability=0.99,
        payment_error_probability=0.01,
        purchase_probability=0.95,
        mobile_probability=0.40,
        min_event_gap_seconds=3,
        max_event_gap_seconds=45,
        cart_idle_min_seconds=5,
        cart_idle_max_seconds=60,
    ),
    Persona.HIGH_RISK_CART: PersonaProfile(
        name=Persona.HIGH_RISK_CART,
        weight=0.10,
        product_view_min=2,
        product_view_max=7,
        search_probability=0.30,
        wishlist_probability=0.10,
        add_to_cart_probability=0.80,
        remove_from_cart_probability=0.15,
        cart_view_probability=0.95,
        checkout_probability=0.20,
        payment_attempt_probability=0.90,
        payment_error_probability=0.10,
        purchase_probability=0.15,
        mobile_probability=0.65,
        min_event_gap_seconds=10,
        max_event_gap_seconds=180,
        cart_idle_min_seconds=300,
        cart_idle_max_seconds=1800,
    ),
}


def get_persona_profile(persona: Persona) -> PersonaProfile:
    """Return the profile for a persona."""
    return PERSONA_PROFILES[persona]


def validate_persona_profiles() -> None:
    """Validate static persona configuration."""

    total_weight = sum(profile.weight for profile in PERSONA_PROFILES.values())

    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            f"Persona weights must sum to 1.0, but received {total_weight}."
        )

    for profile in PERSONA_PROFILES.values():
        probabilities = {
            "search_probability": profile.search_probability,
            "wishlist_probability": profile.wishlist_probability,
            "add_to_cart_probability": profile.add_to_cart_probability,
            "remove_from_cart_probability": profile.remove_from_cart_probability,
            "cart_view_probability": profile.cart_view_probability,
            "checkout_probability": profile.checkout_probability,
            "payment_attempt_probability": profile.payment_attempt_probability,
            "payment_error_probability": profile.payment_error_probability,
            "purchase_probability": profile.purchase_probability,
            "mobile_probability": profile.mobile_probability,
        }

        for field_name, value in probabilities.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{profile.name}.{field_name} must be between 0 and 1."
                )

        if profile.product_view_min < 1:
            raise ValueError(
                f"{profile.name}.product_view_min must be at least 1."
            )

        if profile.product_view_min > profile.product_view_max:
            raise ValueError(
                f"{profile.name} has invalid product view bounds."
            )

        if profile.min_event_gap_seconds < 1:
            raise ValueError(
                f"{profile.name}.min_event_gap_seconds must be positive."
            )

        if profile.min_event_gap_seconds > profile.max_event_gap_seconds:
            raise ValueError(
                f"{profile.name} has invalid event gap bounds."
            )

        if profile.cart_idle_min_seconds < 0:
            raise ValueError(
                f"{profile.name}.cart_idle_min_seconds cannot be negative."
            )

        if profile.cart_idle_min_seconds > profile.cart_idle_max_seconds:
            raise ValueError(
                f"{profile.name} has invalid cart idle bounds."
            )


validate_persona_profiles()