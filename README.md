# kraken-sockets

Access Kraken's WebSocket API v2 for real-time market information and trading data.

## Quick Start

1. **Initialize** the WebSocket client
2. **Create** trigger functions using the decorator
3. **Run** with your desired subscriptions

```python
import asyncio
from kraken_sockets.api import KrakenWebSocketAPI
from schema.responses import TickerUpdateResponse, TradesUpdateResponse
from schema.requests.market_data_requests import TickerSubscriptionRequest, TradesSubscriptionRequest

async def main():
    # 1. Initialize
    kraken = KrakenWebSocketAPI()

    # 2. Set trigger functions for specific response types
    @kraken.trigger(TickerUpdateResponse)
    async def ticker_handler(response: TickerUpdateResponse) -> None:
        kraken.log(f"Last price: ${response.last}", "info")

    @kraken.trigger(TradesUpdateResponse)
    async def trades_handler(response: TradesUpdateResponse) -> None:
        for trade in response.trades:
            kraken.log(f"{trade.side} {trade.price} @ {trade.qty}", "info")

    # 3. Run with subscriptions
    subscriptions = [
        TickerSubscriptionRequest(["BTC/USD", "ETH/USD"]),
        TradesSubscriptionRequest(["BTC/USD"])
    ]

    await kraken.run(subscriptions)

if __name__ == "__main__":
    asyncio.run(main())
```

## How It Works

The trigger decorator system allows you to:

1. **Initialize**: Create a `KrakenWebSocketAPI` instance
2. **Triggers**: Use `@kraken.trigger(ResponseType)` to register functions that execute when specific message types arrive
3. **Subscribe**: Choose which channels to subscribe to using request schemas
4. **Run**: Call `await kraken.run(subscriptions)` to connect and start the async loop

Each trigger function receives a parsed response object matching the specified schema type.

## Available Decorators

- `@kraken.trigger(ResponseType)` - Execute function when specific response type is received
- `@kraken.user_logger` - Register custom logging handler
- `@kraken.user_task` - Add custom tasks to the async loop

**Admin Responses:**
- `HeartbeatResponse`, `PingResponse`, `StatusResponse`

**Market Data Responses:**
- `BookSnapshotResponse`, `BookUpdateResponse`
- `TickerSnapshotResponse`, `TickerUpdateResponse`
- `TradesSnapshotResponse`, `TradesUpdateResponse`
- `OHLCSnapshotResponse`, `OHLCUpdateResponse`
- `InstrumentsSnapshotResponse`, `InstrumentsUpdateResponse`
- `OrderSnapshotResponse`, `OrderUpdateResponse`

**Subscription Responses:**
- `SubscriptionResponse`, `UnsubscribeResponse`

## Request Schemas

Request schemas are in `schema.requests`:
- Market data: `TickerSubscriptionRequest`, `TradesSubscriptionRequest`, `BookSubscriptionRequest`, etc.
- User data: `OrdersSubscriptionRequest`, `BalancesSubscriptionRequest`, `ExecutionSubscriptionRequest`

## Private Endpoints

For authenticated endpoints, set environment variables:
- `KRAKEN_REST_API_KEY`
- `KRAKEN_REST_API_PRIVATE_KEY`

For complete API documentation, see [Kraken WebSocket API v2 docs](https://docs.kraken.com/api/docs/websocket-v2/).