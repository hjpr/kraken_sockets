import asyncio

from kraken_ws.api import KrakenWebSocketAPI
from schema.market_data_subscriptions import (
    BookSubscriptionMessage,
    InstrumentsSubscriptionMessage,
    OHLCSubscriptionMessage,
    OrdersSubscriptionMessage,
    TickerSubscriptionMessage,
    TradesSubscriptionMessage,
)

async def main():
    # 1. Initialize the socket class
    kraken_ws = KrakenWebSocketAPI()

    # 2. Add your custom handler wrapped with the module handler decorator
    @kraken_ws.message_handler
    async def custom_message_handler(message: dict) -> None:
        """
        Wrap your custom message_handler function in the message_handler decorator.
        Each new message in the queue will trigger your custom_message_handler to execute.
        """
        print(message)

    # 3. Build your subscriptions
    subscriptions = [
        # BookSubscriptionMessage(["BTC/USD"])
        # InstrumentsSubscriptionMessage()
        # OHLCSubscriptionMessage(["BTC/USD"], 15)
        # OrdersSubscriptionMessage(["BTC/USD"])
        TickerSubscriptionMessage(["BTC/USD", "ETH/USD"])
        # TradesSubscriptionMessage(["BTC/USD"])
    ]

    # 4. Run the program
    await kraken_ws.run(subscriptions=subscriptions)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUser exited with Ctrl+C")
