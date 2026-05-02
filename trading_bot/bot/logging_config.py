"""
Logging configuration for the trading bot.
Sets up both a rotating file handler (structured) and a console handler.
"""

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"

# File log format — verbose with timestamps for audit trail
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
# Console format — cleaner, no timestamps (CLI already shows these)
CONSOLE_FORMAT = "%(levelname)s: %(message)s"


def setup_logging(log_level: str = "INFO", verbose: bool = False) -> None:
    """
    Configure root logger with:
      - RotatingFileHandler  → logs/trading_bot.log  (always DEBUG level)
      - StreamHandler        → stderr  (INFO by default, DEBUG if verbose)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # ── File handler (rotating, max 5 MB × 3 backups) ──────────────────
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FILE_FORMAT))
    root.addHandler(fh)

    # ── Console handler ─────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.WARNING)
    ch.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    root.addHandler(ch)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
