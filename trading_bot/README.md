# Binance Futures Testnet Trading Bot

A clean, production-style Python CLI for placing orders on Binance Futures Testnet (USDT-M).

## Features

- ✅ Market and Limit orders (BUY & SELL)
- ✅ **Bonus:** Stop-Market orders as a third order type
- ✅ Full input validation with descriptive error messages
- ✅ Structured project layout: separate client / orders / validators / CLI layers
- ✅ Rotating file logger (`logs/trading_bot.log`) + optional verbose console output
- ✅ Clean box-formatted output in the terminal

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (HMAC auth, HTTP transport)
│   ├── orders.py          # Order placement logic & pretty-printing
│   ├── validators.py      # Input validation (raises ValueError on bad input)
│   └── logging_config.py  # Rotating file + console handler setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   ├── market_order.log   # Sample log — MARKET order
│   └── limit_order.log    # Sample log — LIMIT + STOP_MARKET orders + error example
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / unzip the project

```bash
cd trading_bot
```

### 2. Create & activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Testnet API credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account (no KYC required)
3. Navigate to **API Key** → generate a new key pair
4. Copy the API Key and Secret

### 5. Set environment variables

```bash
export BINANCE_API_KEY="your_testnet_api_key_here"
export BINANCE_API_SECRET="your_testnet_api_secret_here"
```

> **Windows (PowerShell):**
> ```powershell
> $env:BINANCE_API_KEY="your_testnet_api_key_here"
> $env:BINANCE_API_SECRET="your_testnet_api_secret_here"
> ```

---

## How to Run

### Place a Market order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Output:**
```
┌─── Order Request ───────────────────────────
│  Symbol    : BTCUSDT
│  Side      : BUY
│  Type      : MARKET
│  Quantity  : 0.001
└─────────────────────────────────────────────
┌─── Order Response ──────────────────────────
│  Order ID     : 3850293847
│  Client OID   : web_VrBp9Kq2LmNxZjTdWo3c
│  Status       : FILLED
│  Executed Qty : 0.001
│  Avg Price    : 62481.50
│  Symbol       : BTCUSDT
│  Side         : BUY
│  Type         : MARKET
└─────────────────────────────────────────────
✅  Order placed successfully!
```

---

### Place a Limit order

```bash
python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200
```

---

### Place a Stop-Market order (bonus)

```bash
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000
```

---

### View account balances

```bash
python cli.py account
```

---

### View symbol exchange info

```bash
python cli.py info --symbol BTCUSDT
```

---

### Enable verbose (DEBUG) console output

```bash
python cli.py -v place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

### Full help

```bash
python cli.py --help
python cli.py place --help
```

---

## Log Files

All requests, responses, and errors are written to `logs/trading_bot.log` at DEBUG level.  
The log rotates at 5 MB (keeps 3 backups).

Sample logs from testnet runs are included in:
- `logs/market_order.log` — successful MARKET BUY on BTCUSDT
- `logs/limit_order.log`  — successful LIMIT SELL on ETHUSDT + STOP_MARKET + an API error example

---

## Supported Order Types

| Type | `--type` flag | Extra flags required |
|---|---|---|
| Market | `MARKET` | — |
| Limit | `LIMIT` | `--price` |
| Stop-Market *(bonus)* | `STOP_MARKET` | `--stop-price` |
| Stop-Limit | `STOP` | `--price` + `--stop-price` |
| Take-Profit | `TAKE_PROFIT` | `--price` + `--stop-price` |
| Take-Profit Market | `TAKE_PROFIT_MARKET` | `--stop-price` |

---

## Error Handling

| Error type | Behaviour |
|---|---|
| Invalid CLI input (bad symbol, missing price, etc.) | `❌ Validation error: ...` — exit code 2 |
| Binance API error (e.g. -1111 precision) | `❌ API error [code]: message` — exit code 3 |
| Network failure (timeout, DNS) | `❌ Unexpected error: ...` — exit code 4 |
| Missing credentials | Clear instructions printed — exit code 1 |

---

## Assumptions

- Only **USDT-M** (linear) futures are targeted; the base URL is `https://testnet.binancefuture.com`.
- `timeInForce` defaults to `GTC` (Good Till Cancel) for all LIMIT orders — overridable by editing `validators.py`.
- Quantity precision must match the symbol's `stepSize` filter (visible via `python cli.py info --symbol BTCUSDT`). The testnet enforces the same filters as mainnet.
- No `.env` file loading is included to keep dependencies minimal; credentials are read from environment variables only.
