"""
Order placement logic.
Sits between the CLI layer and the raw Binance client,
applying validation and formatting the response for display.
"""

from __future__ import annotations

import logging

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import validate_all

logger = logging.getLogger(__name__)


def _format_order_summary(params: dict) -> str:
    """Build a human-readable summary of the order request."""
    lines = [
        "┌─── Order Request ───────────────────────────",
        f"│  Symbol    : {params['symbol']}",
        f"│  Side      : {params['side']}",
        f"│  Type      : {params['type']}",
        f"│  Quantity  : {params['quantity']}",
    ]
    if "price" in params:
        lines.append(f"│  Price     : {params['price']}")
    if "stopPrice" in params:
        lines.append(f"│  Stop Price: {params['stopPrice']}")
    if "timeInForce" in params:
        lines.append(f"│  TIF       : {params['timeInForce']}")
    lines.append("└─────────────────────────────────────────────")
    return "\n".join(lines)


def _format_order_response(response: dict) -> str:
    """Build a human-readable summary of the API response."""
    avg_price = response.get("avgPrice") or response.get("price") or "N/A"
    lines = [
        "┌─── Order Response ──────────────────────────",
        f"│  Order ID     : {response.get('orderId', 'N/A')}",
        f"│  Client OID   : {response.get('clientOrderId', 'N/A')}",
        f"│  Status       : {response.get('status', 'N/A')}",
        f"│  Executed Qty : {response.get('executedQty', 'N/A')}",
        f"│  Avg Price    : {avg_price}",
        f"│  Symbol       : {response.get('symbol', 'N/A')}",
        f"│  Side         : {response.get('side', 'N/A')}",
        f"│  Type         : {response.get('type', 'N/A')}",
        "└─────────────────────────────────────────────",
    ]
    return "\n".join(lines)


def place_order(
    client: BinanceClient,
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict:
    """
    Validate inputs, place an order, and return the response dict.

    Prints a human-readable request summary and response.
    Raises ValueError for invalid inputs, BinanceAPIError for API errors.
    """
    # 1. Validate
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    # 2. Print request summary
    summary = _format_order_summary(params)
    print(summary)
    logger.info("Order request: %s", params)

    # 3. Place order via client
    response = client.place_order(**params)

    # 4. Print response
    print(_format_order_response(response))
    print("✅  Order placed successfully!\n")
    logger.info("Order response: %s", response)

    return response


def place_market_order(client: BinanceClient, symbol: str, side: str, quantity: float) -> dict:
    """Convenience wrapper for market orders."""
    return place_order(client, symbol=symbol, side=side, order_type="MARKET", quantity=quantity)


def place_limit_order(
    client: BinanceClient, symbol: str, side: str, quantity: float, price: float
) -> dict:
    """Convenience wrapper for limit orders."""
    return place_order(
        client, symbol=symbol, side=side, order_type="LIMIT", quantity=quantity, price=price
    )


def place_stop_market_order(
    client: BinanceClient, symbol: str, side: str, quantity: float, stop_price: float
) -> dict:
    """Convenience wrapper for stop-market orders (bonus order type)."""
    return place_order(
        client,
        symbol=symbol,
        side=side,
        order_type="STOP_MARKET",
        quantity=quantity,
        stop_price=stop_price,
    )
