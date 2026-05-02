"""
Binance Futures Testnet Client
Handles all API communication with HMAC signature generation.
"""

import hashlib
import hmac
import time
import urllib.parse
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around Binance Futures Testnet REST API.
    Handles authentication (HMAC-SHA256), request signing, and HTTP transport.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append a HMAC-SHA256 signature to the parameter dict."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, signed: bool = False, **kwargs) -> dict:
        """
        Execute an HTTP request and return the parsed JSON response.

        Raises:
            BinanceAPIError: for non-2xx responses with an API error body.
            requests.RequestException: for network-level failures.
        """
        url = f"{self.base_url}{endpoint}"
        params = kwargs.pop("params", {})

        if signed:
            params = self._sign(params)

        logger.debug("REQUEST  %s %s  params=%s", method.upper(), url, params)

        response = self.session.request(method, url, params=params, **kwargs)

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

        logger.debug("RESPONSE %s  body=%s", response.status_code, data)

        if not response.ok:
            code = data.get("code", response.status_code)
            msg = data.get("msg", response.text)
            raise BinanceAPIError(code, msg)

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange metadata (symbols, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_symbol_info(self, symbol: str) -> dict | None:
        """Return metadata for a single symbol, or None if not found."""
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol.upper():
                return s
        return None

    def place_order(self, **params) -> dict:
        """
        Place a new futures order.

        Expected keyword arguments:
            symbol, side, type, quantity, [price], [timeInForce], ...
        """
        logger.info("Placing order: %s", params)
        result = self._request("POST", "/fapi/v1/order", signed=True, params=params)
        logger.info("Order placed successfully: orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Fetch details of an existing order."""
        params = {"symbol": symbol.upper(), "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", signed=True, params=params)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        params = {"symbol": symbol.upper(), "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", signed=True, params=params)

    def get_account(self) -> dict:
        """Fetch futures account information."""
        return self._request("GET", "/fapi/v2/account", signed=True, params={})
