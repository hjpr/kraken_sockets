
# Example of how to run the control server alongside the websocket listener loop.
# The control server exposes a local REST API that can be used to subscribe and
# unsubscribe from channels at runtime without restarting the loop.
#
# Once running, visit http://127.0.0.1:8000/docs to explore all available endpoints
# via the auto-generated OpenAPI UI.
#
# Some commands to try with curl:
#
#   Subscribe to a ticker channel:
#   curl -X POST http://127.0.0.1:8000/subscribe/ticker \
#        -H "Content-Type: application/json" \
#        -d '{"symbol": ["BTC/USD"]}'
#
#   Unsubscribe from that ticker channel:
#   curl -X POST http://127.0.0.1:8000/unsubscribe/ticker \
#        -H "Content-Type: application/json" \
#        -d '{"symbol": ["BTC/USD"]}'
#
#   Ping the public websocket to verify the connection is alive:
#   curl -X POST http://127.0.0.1:8000/ping
#
#   Check which channels are currently active:
#   curl http://127.0.0.1:8000/status

import asyncio

async def main():

    # 1. Initialize the websocket client.
    from kraken_sockets.api import KrakenWebSocketAPI
    kraken = KrakenWebSocketAPI()

    # 2. Register triggers for all available update responses. Each handler fires
    #    whenever the corresponding channel broadcasts a new message. Subscribe to
    #    a channel via the control server at http://127.0.0.1:8000/docs to see
    #    the triggers below come to life.
    from kraken_sockets.schema.responses import (
        BookUpdateResponse,
        ExecutionsUpdateResponse,
        InstrumentsUpdateResponse,
        OHLCUpdateResponse,
        OrderUpdateResponse,
        PingResponse,
        TickerUpdateResponse,
        TradesUpdateResponse,
    )

    @kraken.trigger(TickerUpdateResponse)
    async def ticker_handler(response: TickerUpdateResponse) -> None:
        kraken.log(f"Ticker  | {response.symbol} last=${response.last} bid=${response.bid} ask=${response.ask}", "info")

    @kraken.trigger(BookUpdateResponse)
    async def book_handler(response: BookUpdateResponse) -> None:
        kraken.log(f"Book    | {response.symbol} best_bid={response.bids[0].price if response.bids else '-'} best_ask={response.asks[0].price if response.asks else '-'}", "info")

    @kraken.trigger(TradesUpdateResponse)
    async def trades_handler(response: TradesUpdateResponse) -> None:
        for trade in response.trades:
            kraken.log(f"Trade   | {trade.symbol} {trade.side.upper()} {trade.qty} @ {trade.price}", "info")

    @kraken.trigger(OHLCUpdateResponse)
    async def ohlc_handler(response: OHLCUpdateResponse) -> None:
        for candle in response.candles:
            kraken.log(f"OHLC    | {candle.symbol} [{candle.interval}m] O={candle.open} H={candle.high} L={candle.low} C={candle.close}", "info")

    @kraken.trigger(InstrumentsUpdateResponse)
    async def instruments_handler(response: InstrumentsUpdateResponse) -> None:
        kraken.log(f"Instruments | {len(response.assets)} asset(s) {len(response.pairs)} pair(s) updated", "info")

    @kraken.trigger(OrderUpdateResponse)
    async def order_handler(response: OrderUpdateResponse) -> None:
        kraken.log(f"Level3  | {response.symbol} {len(response.asks)} ask update(s) {len(response.bids)} bid update(s)", "info")

    @kraken.trigger(ExecutionsUpdateResponse)
    async def executions_handler(response: ExecutionsUpdateResponse) -> None:
        for execution in response.executions:
            kraken.log(f"Execution | {execution.symbol} {execution.side.upper()} {execution.exec_type} qty={execution.order_qty} status={execution.order_status}", "info")

    @kraken.trigger(PingResponse)
    async def ping_handler(response: PingResponse) -> None:
        kraken.log(f"Ping    | round_trip={response.round_trip_ms()}ms server_latency={response.server_latency_ms()}ms", "info")

    # 3. Run the loop with controls=True to start the local control server.
    #    Visit http://127.0.0.1:8000/docs to explore and test all endpoints.
    await kraken.run(controls=True)

if __name__ == "__main__":
    asyncio.run(main())
