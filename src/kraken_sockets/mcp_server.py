"""
MCP server exposing the kraken_sockets control API as agent tools.

Runs as a separate process speaking MCP over stdio, forwarding tool calls to the
local control server started by KrakenWebSocketAPI.run(controls=True). Configure
the control server location with the KRAKEN_CONTROL_URL environment variable
(default http://127.0.0.1:8000).

Launch:

    kraken-mcp                        # installed script
    python -m kraken_sockets.mcp_server

Claude Desktop / Claude Code config example:

    {
      "mcpServers": {
        "kraken": {
          "command": "kraken-mcp",
          "env": {"KRAKEN_CONTROL_URL": "http://127.0.0.1:8000"}
        }
      }
    }
"""

import os

from typing import Literal, Optional

import requests

from mcp.server.fastmcp import FastMCP

CONTROL_URL = os.getenv("KRAKEN_CONTROL_URL", "http://127.0.0.1:8000")

mcp = FastMCP(
    "kraken-sockets",
    instructions=(
        "Tools for live Kraken market data, computed indicators, condition alerts, "
        "and order execution via a local always-on websocket client. Typical strategy "
        "loop: subscribe to market data, read indicators once warmed up, register "
        "conditions, poll alerts, and place orders when your strategy criteria are met. "
        "Order acknowledgements and fills stream on the websocket; use get_status and "
        "get_alerts rather than expecting synchronous trade results."
    ),
)


def _get(path: str, params: Optional[dict] = None) -> dict:
    res = requests.get(f"{CONTROL_URL}{path}", params=params, timeout=10)
    res.raise_for_status()
    return res.json()


def _post(path: str, body: dict) -> dict:
    body = {k: v for k, v in body.items() if v is not None}
    res = requests.post(f"{CONTROL_URL}{path}", json=body, timeout=10)
    res.raise_for_status()
    return res.json()


def _delete(path: str) -> dict:
    res = requests.delete(f"{CONTROL_URL}{path}", timeout=10)
    res.raise_for_status()
    return res.json()


# ---------------------------------------------------------------------------
# Status and market data
# ---------------------------------------------------------------------------

@mcp.tool()
def get_status() -> dict:
    """Returns the set of currently active websocket channel subscriptions."""
    return _get("/status")


@mcp.tool()
def subscribe_market_data(
    channel: Literal["ticker", "book", "ohlc", "trades"],
    symbol: list[str],
    interval: Optional[int] = None,
    depth: Optional[int] = None,
) -> dict:
    """
    Subscribes to a live market data channel for the given symbols (e.g. ["BTC/USD"]).
    'ohlc' requires interval in minutes (1, 5, 15, 30, 60, 240, 1440); 'book' accepts
    optional depth (10, 25, 100, 500, 1000). Subscribe to 'ticker' and 'ohlc' to feed
    the indicator engine: ticker drives the rolling 24h stats, ohlc drives the
    candle-based moving averages at the chosen interval.
    """
    body: dict = {"symbol": symbol}
    if channel == "ohlc":
        body["interval"] = interval or 15
    if channel == "book" and depth:
        body["depth"] = depth
    return _post(f"/subscribe/{channel}", body)


@mcp.tool()
def unsubscribe_market_data(
    channel: Literal["ticker", "book", "ohlc", "trades"],
    symbol: list[str],
    interval: Optional[int] = None,
) -> dict:
    """Unsubscribes from a market data channel. 'ohlc' requires the interval used when subscribing."""
    body: dict = {"symbol": symbol}
    if channel == "ohlc":
        body["interval"] = interval or 15
    return _post(f"/unsubscribe/{channel}", body)


# ---------------------------------------------------------------------------
# Indicators, conditions, alerts
# ---------------------------------------------------------------------------

@mcp.tool()
def get_indicators(symbol: Optional[str] = None) -> dict:
    """
    Returns computed rolling statistics per symbol. Tick-based metrics: last,
    mean_24h, std_24h, high_24h, low_24h, zscore_24h (z-score of last price vs the
    24h rolling mean). Candle-based metrics per subscribed ohlc interval:
    sma_20@15, std_20@15, zscore_20@15 (20-period SMA on 15-minute candles).
    Null values mean the window is still warming up; check the sample counts.
    Requires an active ticker (for 24h stats) and/or ohlc (for SMA stats) subscription.
    """
    return _get("/indicators", {"symbol": symbol} if symbol else None)


@mcp.tool()
def register_condition(
    symbol: str,
    metric: str,
    operator: Literal["lt", "lte", "gt", "gte", "crosses_above", "crosses_below"],
    threshold: float,
    mode: Literal["one_shot", "rearm"] = "one_shot",
    cooldown_seconds: float = 0.0,
) -> dict:
    """
    Registers a condition evaluated against live indicator values on every market
    data update. When it trips, an alert appears in get_alerts. Metric names match
    get_indicators keys, e.g. metric="zscore_24h", operator="lt", threshold=-2
    fires when price drops more than 2 standard deviations below its 24h mean.
    'one_shot' fires once then deactivates; 'rearm' keeps firing at most once per
    cooldown_seconds. 'crosses_above'/'crosses_below' fire only on the crossing.
    Returns the condition with its id for later deletion.
    """
    return _post("/conditions", {
        "symbol": symbol, "metric": metric, "operator": operator,
        "threshold": threshold, "mode": mode, "cooldown_seconds": cooldown_seconds,
    })


@mcp.tool()
def list_conditions() -> dict:
    """Lists registered conditions; tripped one-shot conditions show active=false."""
    return _get("/conditions")


@mcp.tool()
def delete_condition(condition_id: int) -> dict:
    """Removes a registered condition by id."""
    return _delete(f"/conditions/{condition_id}")


@mcp.tool()
def get_alerts(since_id: int = 0) -> dict:
    """
    Returns alerts from tripped conditions, oldest first. Pass the highest alert id
    you have already processed as since_id to receive only new alerts.
    """
    return _get("/alerts", {"since_id": since_id})


# ---------------------------------------------------------------------------
# Trading
# ---------------------------------------------------------------------------

@mcp.tool()
def add_order(
    symbol: str,
    side: Literal["buy", "sell"],
    order_type: Literal[
        "limit", "market", "iceberg", "stop-loss", "stop-loss-limit", "take-profit",
        "take-profit-limit", "trailing-stop", "trailing-stop-limit", "settle-position",
    ],
    order_qty: Optional[float] = None,
    limit_price: Optional[float] = None,
    time_in_force: Optional[Literal["gtc", "gtd", "ioc", "fok"]] = None,
    expire_time: Optional[str] = None,
    post_only: Optional[bool] = None,
    cl_ord_id: Optional[str] = None,
    validate: Optional[bool] = None,
) -> dict:
    """
    Places an order. For a limit order that expires after a duration, set
    time_in_force="gtd" and expire_time to an RFC3339 timestamp, e.g. one hour
    from now. Set validate=true to check an order without executing it. The engine
    acknowledgement (order_id) and fills arrive over the websocket, not in this
    response — this returns the queued status only.
    """
    return _post("/trading/add_order", {
        "symbol": symbol, "side": side, "order_type": order_type,
        "order_qty": order_qty, "limit_price": limit_price,
        "time_in_force": time_in_force, "expire_time": expire_time,
        "post_only": post_only, "cl_ord_id": cl_ord_id, "validate": validate,
    })


@mcp.tool()
def amend_order(
    order_id: Optional[str] = None,
    cl_ord_id: Optional[str] = None,
    order_qty: Optional[float] = None,
    limit_price: Optional[float] = None,
) -> dict:
    """Amends an open order in place (identified by order_id or cl_ord_id), retaining queue priority where possible."""
    return _post("/trading/amend_order", {
        "order_id": order_id, "cl_ord_id": cl_ord_id,
        "order_qty": order_qty, "limit_price": limit_price,
    })


@mcp.tool()
def cancel_order(
    order_id: Optional[list[str]] = None,
    cl_ord_id: Optional[list[str]] = None,
) -> dict:
    """Cancels one or more open orders by Kraken order_id or client cl_ord_id."""
    return _post("/trading/cancel_order", {"order_id": order_id, "cl_ord_id": cl_ord_id})


@mcp.tool()
def cancel_all() -> dict:
    """Cancels all open orders on the account."""
    return _post("/trading/cancel_all", {})


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
