import asyncio

from kraken_sockets.api import KrakenWebSocketAPI
from schema.responses import TickerUpdateResponse, TradesUpdateResponse
from schema.requests.market_data_requests import TickerSubscriptionRequest, TradesSubscriptionRequest

"""
Utilize triggers
"""

async def main():

    # 1. Initialize the sockets
    kraken = KrakenWebSocketAPI()

    # 2. Set your triggers to listen for specific responses.
    @kraken.trigger(TickerUpdateResponse)
    async def ticker_trigger(response: TickerUpdateResponse) -> None:
        kraken.log(f"Last price: ${response.last}", "info")

    @kraken.trigger(TradesUpdateResponse)
    async def trade_trigger(response: TradesUpdateResponse) -> None:
        for trade in response.trades:
            kraken.log(f"{trade.side.title()} ({trade.ord_type.title()}): Price - {trade.price}, Qty - {trade.qty}", "info")

    # 3. Subscribe to channels
    subscriptions = [
        TickerSubscriptionRequest(["ETH/USD"]),
        TradesSubscriptionRequest(["ETH/USD"], snapshot=True)
    ]

    # 4. Run the async loop
    await kraken.run(subscriptions)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUser exited with Ctrl+C")