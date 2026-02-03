from __future__ import annotations

from langchain_core.tools import tool


@tool("calculate_discount")
def calculate_discount(price: float, percentage: float) -> dict[str, float]:
    """Calculate discounted price by percentage."""

    discounted = price * (1 - (percentage / 100.0))
    return {"discounted_price": round(discounted, 2)}
