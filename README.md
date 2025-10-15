# kraken-sockets

Access Kraken's WebSocket API v2 for real-time market information and trading data.

## Quick Start

1. **Initialize** the WebSocket client
2. **Create** a message handler using the decorator
3. **Run** with your desired subscriptions

```python
import asyncio
from kraken_ws.api import KrakenWebSocketAPI
from schema.market_data_subscriptions import TickerSubscriptionMessage

async def main():
    # 1. Initialize
    kraken_ws = KrakenWebSocketAPI()

    # 2. Wrap your handler
    @kraken_ws.message_handler
    async def my_handler(message: dict) -> None:
        print(message)

    # 3. Run with subscriptions, alternatively you can call .subscribe() during your own execution
    subscriptions = [TickerSubscriptionMessage(["BTC/USD", "ETH/USD"])]
    await kraken_ws.run(subscriptions=subscriptions)

if __name__ == "__main__":
    asyncio.run(main())
```

## How It Works

The `example.py` demonstrates the three-step process:

1. **Initialize**: Create a `KrakenWebSocketAPI` instance
2. **Handler**: Use `@kraken_ws.message_handler` decorator on your async function to process incoming messages.
3. **Run**: Call `await kraken_ws.run(subscriptions=[...])` to connect and start receiving data

Your handler function receives a pre parsed JSON -> python dictionary. See Kraken docs for the response schema.

## Message Structure

For complete documentation on message formats and available subscriptions, see the [Kraken WebSocket API v2 docs](https://docs.kraken.com/api/docs/websocket-v2/add_order).

## Private Endpoints

For authenticated endpoints, set environment variables by replacing .env.example with your .env with keys.:
- `KRAKEN_REST_API_KEY`
- `KRAKEN_REST_API_PRIVATE_KEY`