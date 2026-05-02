#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
  python cli.py place --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.01 --price 3200
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000
  python cli.py account
"""

import argparse
import json
import logging
import os
import sys

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import validate_symbol

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_client() -> BinanceClient:
    """
    Build a BinanceClient from environment variables.
    Exits with a clear message if credentials are missing.
    """
    api_key = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "❌  Missing credentials.\n"
            "    Set the following environment variables before running:\n"
            "      export BINANCE_API_KEY=<your-testnet-api-key>\n"
            "      export BINANCE_API_SECRET=<your-testnet-api-secret>",
            file=sys.stderr,
        )
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


# ── Sub-command handlers ────────────────────────────────────────────────────────

def cmd_place(args: argparse.Namespace) -> None:
    """Handle the 'place' sub-command."""
    client = _get_client()

    try:
        place_order(
            client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        print(f"❌  Validation error: {exc}", file=sys.stderr)
        logger.error("Validation error: %s", exc)
        sys.exit(2)
    except BinanceAPIError as exc:
        print(f"❌  API error [{exc.code}]: {exc.message}", file=sys.stderr)
        logger.error("API error: %s", exc)
        sys.exit(3)
    except Exception as exc:  # network failures, etc.
        print(f"❌  Unexpected error: {exc}", file=sys.stderr)
        logger.exception("Unexpected error during order placement")
        sys.exit(4)


def cmd_account(args: argparse.Namespace) -> None:
    """Handle the 'account' sub-command — print account balances."""
    client = _get_client()
    try:
        account = client.get_account()
        assets = [a for a in account.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        print("\n── Account Balances ─────────────────────────────")
        if assets:
            for asset in assets:
                print(
                    f"  {asset['asset']:6s}  wallet={asset['walletBalance']}"
                    f"  unrealizedPnl={asset['unrealizedProfit']}"
                )
        else:
            print("  (no non-zero balances)")
        print("─────────────────────────────────────────────────\n")
    except BinanceAPIError as exc:
        print(f"❌  API error [{exc.code}]: {exc.message}", file=sys.stderr)
        sys.exit(3)


def cmd_info(args: argparse.Namespace) -> None:
    """Handle the 'info' sub-command — print symbol info."""
    client = _get_client()
    try:
        symbol = validate_symbol(args.symbol)
        info = client.get_symbol_info(symbol)
        if info is None:
            print(f"❌  Symbol '{symbol}' not found on testnet.", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(info, indent=2))
    except ValueError as exc:
        print(f"❌  Validation error: {exc}", file=sys.stderr)
        sys.exit(2)
    except BinanceAPIError as exc:
        print(f"❌  API error [{exc.code}]: {exc.message}", file=sys.stderr)
        sys.exit(3)


# ── Argument parser ─────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance Futures Testnet trading bot — place orders from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market BUY
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200

  # Stop-Market (bonus order type)
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000

  # Account balances
  python cli.py account

  # Symbol info
  python cli.py info --symbol BTCUSDT
        """,
    )

    # Global flags
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG-level console output (log file always captures DEBUG).",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ── place ──
    place_p = subparsers.add_parser("place", help="Place a new futures order.")
    place_p.add_argument("--symbol",     required=True,  help="Trading pair, e.g. BTCUSDT")
    place_p.add_argument("--side",       required=True,  choices=["BUY", "SELL"],
                         help="Order side: BUY or SELL")
    place_p.add_argument("--type",       required=True,
                         choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP",
                                  "TAKE_PROFIT", "TAKE_PROFIT_MARKET"],
                         help="Order type")
    place_p.add_argument("--quantity",   required=True,  type=float, help="Order quantity")
    place_p.add_argument("--price",      required=False, type=float, default=None,
                         help="Limit price (required for LIMIT / STOP / TAKE_PROFIT)")
    place_p.add_argument("--stop-price", required=False, type=float, default=None,
                         dest="stop_price",
                         help="Stop trigger price (required for STOP_MARKET / STOP / TP orders)")
    place_p.set_defaults(func=cmd_place)

    # ── account ──
    acct_p = subparsers.add_parser("account", help="Show current account balances.")
    acct_p.set_defaults(func=cmd_account)

    # ── info ──
    info_p = subparsers.add_parser("info", help="Show exchange info for a symbol.")
    info_p.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    info_p.set_defaults(func=cmd_info)

    return parser


# ── Entry point ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger.info("CLI invoked with args: %s", vars(args))

    args.func(args)


if __name__ == "__main__":
    main()
