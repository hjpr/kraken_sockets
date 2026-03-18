
# Example of how to use the decorator to handle specific responses
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