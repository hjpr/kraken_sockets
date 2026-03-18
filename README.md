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

## Private Endpoints

For authenticated endpoints, set environment variables:

- `KRAKEN_REST_API_KEY`
- `KRAKEN_REST_API_PRIVATE_KEY`

For complete API documentation, see [Kraken WebSocket API v2 docs](https://docs.kraken.com/api/docs/websocket-v2/).