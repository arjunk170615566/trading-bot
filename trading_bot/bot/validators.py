"""
Input validation for trading bot CLI parameters.
All validation functions raise ValueError with a descriptive message on failure.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Normalize and basic-validate a trading symbol."""
    symbol = symbol.strip().upper()
    if not symbol.isalpha():
        raise ValueError(f"Symbol must contain only letters, got: '{symbol}'")
    if len(symbol) < 5 or len(symbol) > 12:
        raise ValueError(f"Symbol '{symbol}' length seems unusual (expected 5-12 chars).")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY or SELL)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Side must be one of {sorted(VALID_SIDES)}, got: '{side}'")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got: '{order_type}'"
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    """Validate that quantity is a positive number."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number, got: '{quantity}'")
    if qty <= 0:
        raise ValueError(f"Quantity must be positive, got: {qty}")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Validate price field.
    - Required for LIMIT orders.
    - Must be positive if provided.
    - Ignored (and None returned) for MARKET orders.
    """
    if order_type in ("MARKET", "STOP_MARKET", "TAKE_PROFIT_MARKET"):
        # Price not applicable for pure market orders
        if price is not None:
            pass  # silently accept but won't send
        return None

    if price is None or str(price).strip() == "":
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price must be a number, got: '{price}'")

    if p <= 0:
        raise ValueError(f"Price must be positive, got: {p}")

    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    """Validate stop price for STOP and TAKE_PROFIT order types."""
    if order_type not in ("STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"):
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValueError(f"Stop price (--stop-price) is required for {order_type} orders.")

    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price must be a number, got: '{stop_price}'")

    if sp <= 0:
        raise ValueError(f"Stop price must be positive, got: {sp}")

    return sp


def validate_all(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict:
    """
    Run all validations and return a clean params dict ready for the API.
    Raises ValueError on the first validation failure encountered.
    """
    clean = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }

    clean_price = validate_price(price, clean["type"])
    if clean_price is not None:
        clean["price"] = clean_price
        clean["timeInForce"] = "GTC"  # Good Till Cancel — sensible default for LIMIT

    clean_stop = validate_stop_price(stop_price, clean["type"])
    if clean_stop is not None:
        clean["stopPrice"] = clean_stop

    return clean
