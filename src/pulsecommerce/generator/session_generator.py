"""Synthetic behavioral session generation."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from uuid import uuid4

from pulsecommerce.generator.events import create_event
from pulsecommerce.generator.experiments import (
    TREATMENT,
    get_experiment_assignment,
)
from pulsecommerce.generator.personas import Persona, PersonaProfile


PRODUCT_CATALOG = (
    {
        "product_id": "PROD-001",
        "category": "electronics",
        "price": 1999.0,
    },
    {
        "product_id": "PROD-002",
        "category": "fashion",
        "price": 1499.0,
    },
    {
        "product_id": "PROD-003",
        "category": "home",
        "price": 2499.0,
    },
    {
        "product_id": "PROD-004",
        "category": "beauty",
        "price": 799.0,
    },
    {
        "product_id": "PROD-005",
        "category": "sports",
        "price": 1799.0,
    },
)

COUNTRIES = (
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
)

TRAFFIC_SOURCES = (
    "organic",
    "paid_search",
    "social",
    "email",
    "direct",
)

PAYMENT_METHODS = (
    "credit_card",
    "debit_card",
    "upi",
    "wallet",
)


def _advance_time(
    timestamp: datetime,
    profile: PersonaProfile,
    rng: random.Random,
) -> datetime:
    """Advance time using persona-specific event velocity."""

    seconds = rng.randint(
        profile.min_event_gap_seconds,
        profile.max_event_gap_seconds,
    )

    return timestamp + timedelta(seconds=seconds)


def _choose_device(
    profile: PersonaProfile,
    rng: random.Random,
) -> str:
    """Choose a device based on persona behavior."""

    return (
        "mobile"
        if rng.random() < profile.mobile_probability
        else "desktop"
    )


def _get_experiment_effect(
    variant: str,
    checkout_probability: float,
    payment_error_probability: float,
    purchase_probability: float,
) -> tuple[float, float, float]:
    """Apply the checkout redesign treatment effect.

    The treatment improves conversion through reduced checkout friction
    rather than artificially forcing successful purchases.

    Effects are deliberately modest so statistical significance emerges
    from sufficient sample size rather than being guaranteed in tiny data.
    """

    if variant != TREATMENT:
        return (
            checkout_probability,
            payment_error_probability,
            purchase_probability,
        )

    adjusted_checkout_probability = min(
        checkout_probability * 1.05,
        1.0,
    )

    adjusted_payment_error_probability = max(
        payment_error_probability * 0.65,
        0.0,
    )

    adjusted_purchase_probability = min(
        purchase_probability * 1.05,
        1.0,
    )

    return (
        adjusted_checkout_probability,
        adjusted_payment_error_probability,
        adjusted_purchase_probability,
    )


def generate_session(
    *,
    user_id: str,
    persona: Persona,
    profile: PersonaProfile,
    session_start: datetime,
    rng: random.Random,
) -> list[dict]:
    """Generate one ordered synthetic user session."""

    session_id = str(uuid4())

    experiment = get_experiment_assignment(user_id)

    device_type = _choose_device(profile, rng)
    country = rng.choice(COUNTRIES)
    traffic_source = rng.choice(TRAFFIC_SOURCES)

    campaign = (
        "CMP-SEARCH-001"
        if traffic_source == "paid_search"
        else None
    )

    (
        checkout_probability,
        payment_error_probability,
        purchase_probability,
    ) = _get_experiment_effect(
        variant=experiment["variant"],
        checkout_probability=profile.checkout_probability,
        payment_error_probability=profile.payment_error_probability,
        purchase_probability=profile.purchase_probability,
    )

    timestamp = session_start
    events: list[dict] = []

    def add_event(
        event_name: str,
        *,
        page: str | None = None,
        product: dict | None = None,
        quantity: int | None = None,
        cart_value: float | None = None,
        payment_method: str | None = None,
        error_code: str | None = None,
        event_properties: dict | None = None,
    ) -> None:
        """Append one canonical event."""

        events.append(
            create_event(
                user_id=user_id,
                session_id=session_id,
                event_timestamp=timestamp,
                event_name=event_name,
                page=page,
                device_type=device_type,
                country=country,
                traffic_source=traffic_source,
                campaign=campaign,
                product_id=(
                    product["product_id"]
                    if product is not None
                    else None
                ),
                category=(
                    product["category"]
                    if product is not None
                    else None
                ),
                quantity=quantity,
                price=(
                    product["price"]
                    if product is not None
                    else None
                ),
                cart_value=cart_value,
                experiment_id=experiment["experiment_id"],
                variant=experiment["variant"],
                payment_method=payment_method,
                error_code=error_code,
                event_properties=event_properties,
            )
        )

    # Session entry.
    add_event(
        "session_start",
        page="homepage",
        event_properties={"persona": persona.value},
    )

    timestamp = _advance_time(timestamp, profile, rng)

    add_event(
        "homepage_view",
        page="homepage",
    )

    # Optional search.
    if rng.random() < profile.search_probability:
        timestamp = _advance_time(timestamp, profile, rng)

        add_event(
            "search",
            page="search",
            event_properties={
                "query": rng.choice(
                    (
                        "wireless headphones",
                        "running shoes",
                        "smart watch",
                        "home decor",
                        "skincare",
                    )
                )
            },
        )

    selected_product = rng.choice(PRODUCT_CATALOG)

    product_views = rng.randint(
        profile.product_view_min,
        profile.product_view_max,
    )

    for _ in range(product_views):
        timestamp = _advance_time(timestamp, profile, rng)

        product = rng.choice(PRODUCT_CATALOG)

        add_event(
            "product_view",
            page="product",
            product=product,
        )

    timestamp = _advance_time(timestamp, profile, rng)

    add_event(
        "product_click",
        page="product",
        product=selected_product,
    )

    if rng.random() < profile.wishlist_probability:
        timestamp = _advance_time(timestamp, profile, rng)

        add_event(
            "wishlist_add",
            page="product",
            product=selected_product,
        )

    cart_value: float | None = None
    quantity: int | None = None
    item_in_cart = False

    if rng.random() < profile.add_to_cart_probability:
        timestamp = _advance_time(timestamp, profile, rng)

        quantity = rng.randint(1, 3)

        cart_value = round(
            selected_product["price"] * quantity,
            2,
        )

        add_event(
            "add_to_cart",
            page="product",
            product=selected_product,
            quantity=quantity,
            cart_value=cart_value,
        )

        item_in_cart = True

        if rng.random() < profile.cart_view_probability:
            idle_seconds = rng.randint(
                profile.cart_idle_min_seconds,
                profile.cart_idle_max_seconds,
            )

            timestamp += timedelta(seconds=idle_seconds)

            add_event(
                "cart_view",
                page="cart",
                cart_value=cart_value,
                event_properties={
                    "idle_before_cart_view_seconds": idle_seconds
                },
            )

        if (
            item_in_cart
            and rng.random() < profile.remove_from_cart_probability
        ):
            timestamp = _advance_time(timestamp, profile, rng)

            add_event(
                "remove_from_cart",
                page="cart",
                product=selected_product,
                quantity=quantity,
                cart_value=0.0,
            )

            item_in_cart = False
            cart_value = 0.0

    if item_in_cart and rng.random() < checkout_probability:
        timestamp = _advance_time(timestamp, profile, rng)

        add_event(
            "checkout_start",
            page="checkout",
            cart_value=cart_value,
        )

        if rng.random() < profile.payment_attempt_probability:
            timestamp = _advance_time(timestamp, profile, rng)

            payment_method = rng.choice(PAYMENT_METHODS)

            add_event(
                "payment_attempt",
                page="checkout",
                cart_value=cart_value,
                payment_method=payment_method,
            )

            payment_failed = (
                rng.random() < payment_error_probability
            )

            if payment_failed:
                timestamp = _advance_time(timestamp, profile, rng)

                add_event(
                    "payment_error",
                    page="checkout",
                    cart_value=cart_value,
                    payment_method=payment_method,
                    error_code=rng.choice(
                        (
                            "PAYMENT_DECLINED",
                            "PAYMENT_TIMEOUT",
                            "UPI_FAILURE",
                        )
                    ),
                )

            elif rng.random() < purchase_probability:
                timestamp = _advance_time(timestamp, profile, rng)

                add_event(
                    "purchase_complete",
                    page="confirmation",
                    product=selected_product,
                    quantity=quantity,
                    cart_value=cart_value,
                    payment_method=payment_method,
                )

    timestamp = _advance_time(timestamp, profile, rng)

    add_event(
        "session_end",
        page=events[-1]["page"],
    )

    return events