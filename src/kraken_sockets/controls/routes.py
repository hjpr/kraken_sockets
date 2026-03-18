
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from kraken_sockets.schema.requests.admin_requests import PingRequest
from kraken_sockets.schema.requests.market_data_requests import (
    BookSubscriptionRequest,
    BookUnsubscribeRequest,
    InstrumentsSubscriptionRequest,
    InstrumentsUnsubscribeRequest,
    OHLCSubscriptionRequest,
    OHLCUnsubscribeRequest,
    OrdersSubscriptionRequest,
    OrdersUnsubscribeRequest,
    TickerSubscriptionRequest,
    TickerUnsubscribeRequest,
    TradesSubscriptionRequest,
    TradesUnsubscribeRequest,
)
from kraken_sockets.schema.requests.user_data_requests import (
    BalancesSubscriptionRequest,
    BalancesUnsubscribeRequest,
    ExecutionSubscriptionRequest,
    ExecutionUnsubscribeRequest,
)


class TickerSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "event_trigger": "trades", "snapshot": True}})
    symbol: list[str]
    event_trigger: Literal["bbo", "trades"] = "trades"
    snapshot: bool = True
    req_id: Optional[int] = None


class TickerUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"]}})
    symbol: list[str]
    event_trigger: Optional[Literal["bbo", "trades"]] = None
    req_id: Optional[int] = None


class BookSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "depth": 10, "snapshot": True}})
    symbol: list[str]
    depth: Literal[10, 25, 100, 500, 1000] = 10
    snapshot: bool = True
    req_id: Optional[int] = None


class BookUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"]}})
    symbol: list[str]
    depth: Optional[Literal[10, 25, 100, 500, 1000]] = None
    req_id: Optional[int] = None


class OHLCSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "interval": 1, "snapshot": True}})
    symbol: list[str]
    interval: Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
    snapshot: bool = True
    req_id: Optional[int] = None


class OHLCUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "interval": 1}})
    symbol: list[str]
    interval: Optional[Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]] = None
    req_id: Optional[int] = None


class TradesSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "snapshot": False}})
    symbol: list[str]
    snapshot: bool = False
    req_id: Optional[int] = None


class TradesUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"]}})
    symbol: list[str]
    req_id: Optional[int] = None


class InstrumentsSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"include_tokenized_assets": False, "snapshot": True}})
    include_tokenized_assets: bool = False
    snapshot: bool = True
    req_id: Optional[int] = None


class InstrumentsUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})
    req_id: Optional[int] = None


class OrdersSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"], "depth": 10, "snapshot": True}})
    symbol: list[str]
    depth: Literal[10, 100, 1000] = 10
    snapshot: bool = True
    req_id: Optional[int] = None


class OrdersUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": ["BTC/USD"]}})
    symbol: list[str]
    req_id: Optional[int] = None


class ExecutionsSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"snap_trades": False, "snap_orders": True, "order_status": True, "rebased": True, "ratecounter": True}})
    snap_trades: bool = False
    snap_orders: bool = True
    order_status: bool = True
    rebased: bool = True
    ratecounter: bool = True
    users: Optional[Literal["all"]] = None
    req_id: Optional[int] = None


class ExecutionsUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})
    req_id: Optional[int] = None


class BalancesSubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"snapshot": True, "rebased": True}})
    snapshot: bool = True
    rebased: bool = True
    users: Optional[Literal["all"]] = None
    req_id: Optional[int] = None


class BalancesUnsubscribeBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})
    req_id: Optional[int] = None


class PingBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"target": "public"}})
    target: Literal["public", "private"] = "public"
    req_id: Optional[int] = None


def build_router(kraken) -> APIRouter:
    """Build the router for the control server."""
    router = APIRouter()

    admin = APIRouter(tags=["Admin"])
    market_data = APIRouter(tags=["Market Data"])
    user_data = APIRouter(tags=["User Data"])

    # ---------------------------------------------------------------------------
    # Admin
    # ---------------------------------------------------------------------------

    @admin.get("/status")
    async def status():
        """Returns the set of currently active channel subscriptions."""
        return {"active_channels": list(kraken.available_channels)}
    
    @admin.post("/ping")
    async def ping(body: PingBody):
        """
        Sends a ping to the public or private websocket. The pong response from Kraken
        will pass through _process_messages and fire any PingResponse trigger registered
        on the kraken instance.
        """
        socket = kraken.websocket_public if body.target == "public" else kraken.websocket_private
        if not socket:
            return {"status": "error", "detail": f"{body.target} websocket is not connected"}
        await PingRequest(socket).send(req_id=body.req_id)
        return {"status": "sent", "target": body.target}

    # ---------------------------------------------------------------------------
    # Market Data
    # ---------------------------------------------------------------------------

    @market_data.post("/subscribe/ticker")
    async def subscribe_ticker(body: TickerSubscribeBody):
        req = TickerSubscriptionRequest(body.symbol, body.event_trigger, body.snapshot, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "ticker", "symbol": body.symbol}

    @market_data.post("/subscribe/book")
    async def subscribe_book(body: BookSubscribeBody):
        req = BookSubscriptionRequest(body.symbol, body.depth, body.snapshot, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "book", "symbol": body.symbol}

    @market_data.post("/subscribe/orders")
    async def subscribe_orders(body: OrdersSubscribeBody):
        req = OrdersSubscriptionRequest(body.symbol, body.depth, body.snapshot, body.req_id)
        req.params["token"] = kraken._token
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "level3", "symbol": body.symbol}

    @market_data.post("/subscribe/ohlc")
    async def subscribe_ohlc(body: OHLCSubscribeBody):
        req = OHLCSubscriptionRequest(body.symbol, body.interval, body.snapshot, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "ohlc", "symbol": body.symbol}

    @market_data.post("/subscribe/trades")
    async def subscribe_trades(body: TradesSubscribeBody):
        req = TradesSubscriptionRequest(body.symbol, body.snapshot, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "trade", "symbol": body.symbol}

    @market_data.post("/subscribe/instrument")
    async def subscribe_instrument(body: InstrumentsSubscribeBody):
        req = InstrumentsSubscriptionRequest(body.include_tokenized_assets, body.snapshot, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "instrument"}

    @market_data.post("/unsubscribe/ticker")
    async def unsubscribe_ticker(body: TickerUnsubscribeBody):
        req = TickerUnsubscribeRequest(body.symbol, body.event_trigger, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "ticker", "symbol": body.symbol}

    @market_data.post("/unsubscribe/book")
    async def unsubscribe_book(body: BookUnsubscribeBody):
        req = BookUnsubscribeRequest(body.symbol, body.depth, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "book", "symbol": body.symbol}

    @market_data.post("/unsubscribe/orders")
    async def unsubscribe_orders(body: OrdersUnsubscribeBody):
        req = OrdersUnsubscribeRequest(body.symbol, kraken._token, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "level3", "symbol": body.symbol}

    @market_data.post("/unsubscribe/ohlc")
    async def unsubscribe_ohlc(body: OHLCUnsubscribeBody):
        req = OHLCUnsubscribeRequest(body.symbol, body.interval, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "ohlc", "symbol": body.symbol}

    @market_data.post("/unsubscribe/trades")
    async def unsubscribe_trades(body: TradesUnsubscribeBody):
        req = TradesUnsubscribeRequest(body.symbol, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "trade", "symbol": body.symbol}

    @market_data.post("/unsubscribe/instrument")
    async def unsubscribe_instrument(body: InstrumentsUnsubscribeBody):
        req = InstrumentsUnsubscribeRequest(body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "instrument"}

    # ---------------------------------------------------------------------------
    # User Data
    # ---------------------------------------------------------------------------

    @user_data.post("/subscribe/executions")
    async def subscribe_executions(body: ExecutionsSubscribeBody):
        req = ExecutionSubscriptionRequest(
            body.snap_trades,
            body.snap_orders,
            body.order_status,
            body.rebased,
            body.ratecounter,
            body.users,
            body.req_id,
        )
        req.params["token"] = kraken._token
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "executions"}

    @user_data.post("/subscribe/balances")
    async def subscribe_balances(body: BalancesSubscribeBody):
        req = BalancesSubscriptionRequest(body.snapshot, body.rebased, body.users, body.req_id)
        req.params["token"] = kraken._token
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "balances"}

    @user_data.post("/unsubscribe/executions")
    async def unsubscribe_executions(body: ExecutionsUnsubscribeBody):
        req = ExecutionUnsubscribeRequest(kraken._token, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "executions"}

    @user_data.post("/unsubscribe/balances")
    async def unsubscribe_balances(body: BalancesUnsubscribeBody):
        req = BalancesUnsubscribeRequest(kraken._token, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "balances"}

    router.include_router(admin)
    router.include_router(market_data)
    router.include_router(user_data)

    return router
