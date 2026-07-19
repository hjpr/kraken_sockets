# kraken-sockets

---

Access Kraken's WebSocket API v2 for real-time market information and trading data. Kraken-sockets is intended to be used in conjunction with the REST API
client along with an LLM agent to create a fully featured trading bot. Organization and naming scheme for responses/requests follows Kraken API structure.

https://docs.kraken.com/api/docs/websocket-v2/add_order

---

## Quick Start

```python
import asyncio

async def main():

    # 1. Initialize the websocket client.
    from kraken_sockets.api import KrakenWebSocketAPI
    kraken = KrakenWebSocketAPI()

    # 2. Decide which channels to listen to.
    from kraken_sockets.schema.requests.market_data_requests import (
        TickerSubscriptionRequest,
        TradesSubscriptionRequest,
        OHLCSubscriptionRequest
    )
    subscriptions = [
        TickerSubscriptionRequest(["ETH/USD"]),
        TradesSubscriptionRequest(["BTC/USD"]),
        OHLCSubscriptionRequest(["ETH/USD"], 1)
    ]

    # 3. Use the decorator to handle those channel messages as they are broadcast
    from kraken_sockets.schema.responses import (
        TickerUpdateResponse,
        TradesUpdateResponse,
        OHLCUpdateResponse
    )
    @kraken.trigger(TickerUpdateResponse)
    async def ticker_handler(response: TickerUpdateResponse) -> None:
        kraken.log(f"Last price {response.symbol}: ${response.last}", "info")

    @kraken.trigger(TradesUpdateResponse)
    async def trades_handler(response: TradesUpdateResponse) -> None:
        for trade in response.trades:
            kraken.log(f"{trade.symbol} {trade.side.upper()} {trade.price} @ {trade.qty}", "info")

    @kraken.trigger(OHLCUpdateResponse)
    async def ohlc_handler(response: OHLCUpdateResponse) -> None:
        kraken.log(f"{response.timestamp} - {response.candles}", "info")
    
    # 4. Run the async listener loop for those subscriptions
    await kraken.run(subscriptions)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Available Subscriptions

Subscribe to an available channel to listen for responses on that channel. Typically channels broadcast a response each time an update occurs on that channel, and for many channels can optionally specify broadcasting a snapshot when channel is subscribed to to recieve an immediate update.

#### Admin

`kraken_sockets.schema.requests.admin_requests`

- `PingRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/ping/

#### Market Data

`kraken_sockets.schema.requests.market_data_requests`

- `TickerSubscriptionRequest`

- `TickerUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/ticker/

- `BookSubscriptionRequest`

- `BookUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/book/

- `OHLCSubscriptionRequest`

- `OHLCUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/ohlc/

- `TradesSubscriptionRequest`

- `TradesUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/trade/

- `InstrumentSubscriptionRequest`

- `InstrumentUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/instrument/

- `OrdersSubscriptionRequest`

- `OrdersUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/level3/

#### User Data

`kraken_sockets.schema.requests.user_data_requests`

- `BalancesSubscriptionRequest`

- `BalancesUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/balances/

- `ExecutionSubscriptionRequest`

- `ExecutionUnsubscribeRequest`
  
  - https://docs.kraken.com/api/docs/websocket-v2/executions

#### Trading

`kraken_sockets.schema.requests.trading_requests`

- `AddOrderRequest` — https://docs.kraken.com/api/docs/websocket-v2/add_order
- `AmendOrderRequest` — https://docs.kraken.com/api/docs/websocket-v2/amend_order
- `EditOrderRequest` — https://docs.kraken.com/api/docs/websocket-v2/edit_order
- `CancelOrderRequest` — https://docs.kraken.com/api/docs/websocket-v2/cancel_order
- `CancelAllRequest` — https://docs.kraken.com/api/docs/websocket-v2/cancel_all
- `CancelAllOrdersAfterRequest` — https://docs.kraken.com/api/docs/websocket-v2/cancel_after
- `BatchAddRequest` — https://docs.kraken.com/api/docs/websocket-v2/batch_add
- `BatchCancelRequest` — https://docs.kraken.com/api/docs/websocket-v2/batch_cancel

Trading requests are not subscriptions — send them at runtime with `await kraken.trade(request)`, or over HTTP via the Control API. The session token is injected automatically and the private websocket connects on demand.

---

## Available Responses

#### Admin

- `HeartbeatResponse`
- `PingResponse`
- `StatusResponse`

#### Market Data

- Book
  
  - `BookSnapshotResponse`
  
  - `BookUpdateResponse`

- Ticker
  
  - `TickerSnapshotResponse`
  
  - `TickerUpdateResponse`

- Trades
  
  - `TradesSnapshotResponse` 
  
  - `TradesUpdateResponse`

- OHLC
  
  - `OHLCSnapshotResponse`
  
  - `OHLCUpdateResponse`

- Instruments
  
  - `InstrumentsSnapshotResponse`
  
  - `InstrumentsUpdateResponse`

- Order
  
  - `OrderSnapshotResponse`
  
  - `OrderUpdateResponse`

#### User Data

- Executions
  
  - `ExecutionsSnapshotResponse` — open orders and recent fills at subscribe time
  
  - `ExecutionsUpdateResponse` — real-time order lifecycle events (`exec_type`: new, trade, filled, canceled, amended, ...)

- Balances
  
  - `BalancesSnapshotResponse` — every asset held, with per-wallet breakdown
  
  - `BalancesUpdateResponse` — account ledger transactions as they occur (trades settling, deposits, withdrawals, transfers)

#### Subscription

- `SubscriptionResponse`
- `UnsubscribeResponse`

#### Trading

Engine acknowledgements for trading requests. All inherit from `TradingResponse`, which carries `success`, `result`/`error`, `warnings`, engine timestamps, and the echoed `req_id`.

- `AddOrderResponse`
- `AmendOrderResponse`
- `EditOrderResponse`
- `CancelOrderResponse`
- `CancelAllResponse`
- `CancelAllOrdersAfterResponse`
- `BatchAddResponse`
- `BatchCancelResponse`

---

## Available Decorators

Wrap a function in decorators so that it will be registered in the async loop and conditionally fire depending on the behavior of the decorator.

#### Trigger

`@kraken.trigger(ResponseType)`

- Execute function each time a specific response type is received. Check the response types above for the available classes. One function per response type.
- Dispatch is subclass-aware: a trigger on a base class such as `TradingResponse` fires for every trading acknowledgement, but the most specific registered trigger wins — only one trigger runs per message.
- Subscription acks share one class across channels. To react to a particular channel being subscribed (e.g. "run when ticker is subscribed"), filter inside the function:

```python
from kraken_sockets.schema.responses import SubscriptionResponse

@kraken.trigger(SubscriptionResponse)
async def on_subscribe(response: SubscriptionResponse) -> None:
    if not response.success:
        kraken.log(f"Subscribe failed: {response.error}", "warning")
    elif response.channel == "ticker":
        ...  # ticker channel is now live
```

- Triggers are awaited inline by the message processor — keep them fast, or hand slow work to a queue/task so a busy trigger does not delay the stream behind it.

#### Message handler

`@kraken.user_message_handler`

- Register a single catch-all coroutine that receives every message before any trigger fires. Wrapped function receives two arguments: the raw message as a dict, and the parsed response instance (or `None` if the message matched no known schema). This is the intended hook for persisting the full stream, e.g. building a historical dataset.

#### Logger

`@kraken.user_logger`

- Register a custom logging handler. Wrapped function receives two arguments: the log string, and its priority (one of `debug`, `info`, `warning`, `error`, `critical`).

#### Custom tasks

`@kraken.user_task`

- Register a coroutine to be started once as a task when `run()` is called, alongside the websocket listeners. Use it for long-running or periodic work — e.g. computing rolling volatility or highs/lows on an interval — managing your own loop and sleep inside the function.

---

## Control API

Run the client with an optional local REST API to manage subscriptions at runtime — no restart required. This is the intended integration point for agentic trading: keep the websocket loop always on with your triggers registered, and let an LLM agent (or any HTTP client) subscribe, unsubscribe, and check status by calling local endpoints.

#### Enabling

Pass `controls=True` to `run()`. The server runs inside the same asyncio loop as the websocket listeners, and the public websocket connects even with no initial subscriptions.

```python
import asyncio
from kraken_sockets.api import KrakenWebSocketAPI

async def main():
    kraken = KrakenWebSocketAPI()

    # Register triggers for the channels your agent may subscribe to
    from kraken_sockets.schema.responses import TickerUpdateResponse

    @kraken.trigger(TickerUpdateResponse)
    async def ticker_handler(response: TickerUpdateResponse) -> None:
        kraken.log(f"Last price {response.symbol}: ${response.last}", "info")

    # Start with no subscriptions — the agent adds them over HTTP at runtime
    await kraken.run(controls=True, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
```

Interactive OpenAPI docs are served at `http://127.0.0.1:8000/docs` — useful for exploring request bodies, and the schema can be handed directly to an agent as its tool definition.

#### Endpoints

**Admin**

| Method | Path      | Body example             | Description                                    |
| ------ | --------- | ------------------------ | ---------------------------------------------- |
| GET    | `/status` | —                        | List currently active channel subscriptions   |
| POST   | `/ping`   | `{"target": "public"}`   | Ping the public or private websocket          |

**Market Data**

| Method | Path                      | Body example                                |
| ------ | ------------------------- | ------------------------------------------- |
| POST   | `/subscribe/ticker`       | `{"symbol": ["BTC/USD"]}`                   |
| POST   | `/subscribe/book`         | `{"symbol": ["BTC/USD"], "depth": 10}`      |
| POST   | `/subscribe/ohlc`         | `{"symbol": ["BTC/USD"], "interval": 1}`    |
| POST   | `/subscribe/trades`       | `{"symbol": ["BTC/USD"]}`                   |
| POST   | `/subscribe/instrument`   | `{}`                                        |
| POST   | `/subscribe/orders`       | `{"symbol": ["BTC/USD"], "depth": 10}`      |

Each channel has a matching `/unsubscribe/...` endpoint taking the same identifying fields (e.g. `POST /unsubscribe/ticker` with `{"symbol": ["BTC/USD"]}`).

**User Data**

| Method | Path                      | Body example |
| ------ | ------------------------- | ------------ |
| POST   | `/subscribe/executions`   | `{}`         |
| POST   | `/subscribe/balances`     | `{}`         |
| POST   | `/unsubscribe/executions` | `{}`         |
| POST   | `/unsubscribe/balances`   | `{}`         |

**Trading**

| Method | Path                              | Body example                                                                          |
| ------ | --------------------------------- | ------------------------------------------------------------------------------------- |
| POST   | `/trading/add_order`              | `{"symbol": "BTC/USD", "side": "buy", "order_type": "limit", "order_qty": 0.001, "limit_price": 50000}` |
| POST   | `/trading/amend_order`            | `{"order_id": "OXM2QD-EALR2-YBAVEU", "limit_price": 49500}`                           |
| POST   | `/trading/edit_order`             | `{"order_id": "OXM2QD-EALR2-YBAVEU", "symbol": "BTC/USD", "order_qty": 0.002}`        |
| POST   | `/trading/cancel_order`           | `{"order_id": ["OXM2QD-EALR2-YBAVEU"]}`                                               |
| POST   | `/trading/cancel_all`             | `{}`                                                                                  |
| POST   | `/trading/cancel_all_orders_after`| `{"timeout": 60}`                                                                     |
| POST   | `/trading/batch_add`              | `{"symbol": "BTC/USD", "orders": [{...}, {...}]}`                                     |
| POST   | `/trading/batch_cancel`           | `{"orders": ["OXM2QD-EALR2-YBAVEU", "OJF3GE-9EJRK-KF8BCA"]}`                          |

Trading endpoints queue the request and return immediately — the engine acknowledgement arrives over the websocket as the matching `...Response` (e.g. `AddOrderResponse`) and fires any trigger registered for it, or for the `TradingResponse` base class as a catch-all. `add_order`, `edit_order`, and `batch_add` accept `"validate": true` to test a request without executing it.

#### Example

```bash
# Subscribe to a ticker channel
curl -X POST http://127.0.0.1:8000/subscribe/ticker \
     -H "Content-Type: application/json" \
     -d '{"symbol": ["BTC/USD"]}'

# Check which channels are active
curl http://127.0.0.1:8000/status

# Unsubscribe when done
curl -X POST http://127.0.0.1:8000/unsubscribe/ticker \
     -H "Content-Type: application/json" \
     -d '{"symbol": ["BTC/USD"]}'
```

#### Notes

- Endpoint responses return `{"status": "queued"}` — the command has been placed on the outbound queue, not yet confirmed by Kraken. Confirmation arrives over the websocket as a `SubscriptionResponse` / `UnsubscribeResponse` and fires any trigger you registered for it. Your agent should treat the websocket stream, not the HTTP response, as the source of truth.
- The server binds to `127.0.0.1` by default and has no authentication. Keep it local; do not expose it to a network.
- User Data endpoints (`executions`, `balances`) and `orders` require authentication. The first private command automatically fetches a session token and connects the private websocket — no private subscription is needed at startup, only the `KRAKEN_REST_API_*` environment variables.

---

## Analytics & Alerts

When the control server is enabled, an indicator engine runs alongside the websocket listeners, computing rolling statistics from any subscribed `ticker` and `ohlc` streams. It attaches via an internal observer hook, so all of your `@kraken.trigger` slots stay free.

**Metrics per symbol** (visible at `GET /indicators`):

| Metric                                             | Source                     | Meaning                                                          |
| -------------------------------------------------- | -------------------------- | ---------------------------------------------------------------- |
| `last`                                             | ticker                     | Last traded price                                                |
| `mean_24h`, `std_24h`, `high_24h`, `low_24h`       | ticker (24h rolling window)| Rolling stats over the last 24 hours of ticks                    |
| `zscore_24h`                                       | ticker                     | Std devs of `last` from `mean_24h`                               |
| `sma_20@15`, `std_20@15`, `zscore_20@15`           | ohlc (per interval)        | 20-period SMA / std / z-score on 15-minute candles               |
| `samples_24h`, `candles@15`                        | —                          | Warm-up progress; stat values are `null` until their window fills |

Defaults are SMA window 20 and a 24h tick window. Override by constructing the engine before `run()`:

```python
from kraken_sockets.analytics import IndicatorEngine
kraken.analytics = IndicatorEngine(kraken, ma_windows=(20, 50), time_window_hours=24.0)
```

**Conditions** are declarative rules an agent (or any HTTP client) registers at runtime. They are evaluated against fresh metric values on every market data update — no polling loop. When one trips, an alert is appended to a queue the agent polls.

| Method | Path                | Body / params example                                                                  |
| ------ | ------------------- | -------------------------------------------------------------------------------------- |
| GET    | `/indicators`       | `?symbol=BTC/USD` (optional)                                                           |
| POST   | `/conditions`       | `{"symbol": "BTC/USD", "metric": "zscore_24h", "operator": "lt", "threshold": -2}`     |
| GET    | `/conditions`       | —                                                                                      |
| DELETE | `/conditions/{id}`  | —                                                                                      |
| GET    | `/alerts`           | `?since_id=42` — only alerts newer than id 42                                          |

Operators: `lt`, `lte`, `gt`, `gte`, `crosses_above`, `crosses_below` (crossings fire only when the value moves across the threshold between updates). Modes: `one_shot` (default — fires once, then deactivates) and `rearm` (fires at most once per `cooldown_seconds` while the condition holds).

---

## MCP Server

`kraken-mcp` exposes the control API as MCP tools, letting an LLM agent watch computed indicators, register conditions, poll alerts, and execute trades. It runs as a separate process over stdio and forwards to the control server (`KRAKEN_CONTROL_URL`, default `http://127.0.0.1:8000`).

```json
{
  "mcpServers": {
    "kraken": {
      "command": "kraken-mcp",
      "env": {"KRAKEN_CONTROL_URL": "http://127.0.0.1:8000"}
    }
  }
}
```

Tools: `get_status`, `subscribe_market_data`, `unsubscribe_market_data`, `get_indicators`, `register_condition`, `list_conditions`, `delete_condition`, `get_alerts`, `add_order`, `amend_order`, `cancel_order`, `cancel_all`.

**Example agent strategy loop** — *"when price approaches within 1 std dev of the 20MA, place a buy at the 20MA expiring in 1 hour; alert me if price loses 2 std dev of its rolling 24h mean"*:

1. `subscribe_market_data(channel="ticker", symbol=["LINEA/USD"])` and `subscribe_market_data(channel="ohlc", symbol=["LINEA/USD"], interval=15)`
2. `register_condition(symbol="LINEA/USD", metric="zscore_20@15", operator="crosses_below", threshold=1.0)` — approaching the 20MA from above
3. `register_condition(symbol="LINEA/USD", metric="zscore_24h", operator="lt", threshold=-2.0)` — the 24h drawdown tripwire
4. Poll `get_alerts(since_id=...)` on its own cadence; when the approach condition fires, read `get_indicators(symbol="LINEA/USD")` for the current `sma_20@15`
5. `add_order(symbol="LINEA/USD", side="buy", order_type="limit", order_qty=..., limit_price=<sma_20@15>, time_in_force="gtd", expire_time=<now+1h RFC3339>)`
6. Confirm via the executions channel (register a trigger, or watch `get_status`) — the HTTP response only confirms queueing.

---

## Private Endpoints

For authenticated endpoints (private channels and trading), run the interactive setup from the project root:

```bash
python setup_env.py
```

It prompts for your Kraken API key pair, writes them to a gitignored `.env` file with owner-only permissions, and optionally validates them against the Kraken API by requesting a websocket token. Create keys at https://pro.kraken.com/app/settings/api with the "WebSocket interface" permission, plus order permissions if you intend to trade.

Alternatively, set the environment variables yourself:

- `KRAKEN_REST_API_KEY`
- `KRAKEN_REST_API_PRIVATE_KEY`

For complete API documentation, see [Kraken WebSocket API v2 docs](https://docs.kraken.com/api/docs/websocket-v2/).