"""Canonical event creation for the PulseCommerce generator."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4


def create_event(
    *,
    user_id: str,
    session_id: str,
    event_timestamp: datetime,
    event_name: str,
    page: str | None = None,
    device_type: str | None = None,
    country: str | None = None,
    traffic_source: str | None = None,
    campaign: str | None = None,
    product_id: str | None = None,
    category: str | None = None,
    quantity: int | None = None,
    price: float | None = None,
    cart_value: float | None = None,
    experiment_id: str | None = None,
    variant: str | None = None,
    payment_method: str | None = None,
    error_code: str | None = None,
    event_properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one event that follows the canonical event contract."""

    return {
        "event_id": str(uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "event_timestamp": event_timestamp,
        "event_name": event_name,
        "page": page,
        "device_type": device_type,
        "country": country,
        "traffic_source": traffic_source,
        "campaign": campaign,
        "product_id": product_id,
        "category": category,
        "quantity": quantity,
        "price": price,
        "cart_value": cart_value,
        "experiment_id": experiment_id,
        "variant": variant,
        "payment_method": payment_method,
        "error_code": error_code,
        "event_properties": event_properties or {},
    }