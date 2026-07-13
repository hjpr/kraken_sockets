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

#### Subscription

- `SubscriptionResponse`
- `UnsubscribeResponse`

---

## Available Decorators

Wrap a function in decorators so that it will be registered in the async loop and conditionally fire depending on the behavior of the decorator.

#### Trigger

`@kraken.trigger(ResponseType)`

- Execute function when specific response type is received. Check the response types above for a list of available

#### Logger

`@kraken.user_logger`

- Register a custom logging handler. Wrapped function recieves the

#### Custom tasks

`@kraken.user_task`

- Add function as a custom task to the async loop. These tasks will be run with each loop. Control the execution using your own logic.

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

## Private Endpoints

For authenticated endpoints, set environment variables:

- `KRAKEN_REST_API_KEY`
- `KRAKEN_REST_API_PRIVATE_KEY`

For complete API documentation, see [Kraken WebSocket API v2 docs](https://docs.kraken.com/api/docs/websocket-v2/).