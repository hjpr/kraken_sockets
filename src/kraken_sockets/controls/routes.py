
import warnings

from typing import Literal, Optional, Union

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

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
from kraken_sockets.schema.requests.trading_requests import (
    AddOrderRequest,
    AmendOrderRequest,
    BatchAddRequest,
    BatchCancelRequest,
    CancelAllOrdersAfterRequest,
    CancelAllRequest,
    CancelOrderRequest,
    EditOrderRequest,
)
from kraken_sockets.schema.requests.user_data_requests import (
    BalancesSubscriptionRequest,
    BalancesUnsubscribeRequest,
    ExecutionSubscriptionRequest,
    ExecutionUnsubscribeRequest,
)

# The 'validate' fields below intentionally mirror Kraken's parameter name, which
# shadows a deprecated BaseModel classmethod.
warnings.filterwarnings("ignore", message='Field name "validate"')

OrderType = Literal[
    "limit", "market", "iceberg", "stop-loss", "stop-loss-limit", "take-profit",
    "take-profit-limit", "trailing-stop", "trailing-stop-limit", "settle-position"
]
PriceType = Literal["static", "pct", "quote"]


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


class OrderTriggersBody(BaseModel):
    reference: Optional[Literal["index", "last"]] = None
    price: float
    price_type: Optional[PriceType] = None


class AddOrderBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": "BTC/USD", "side": "buy", "order_type": "limit", "order_qty": 0.001, "limit_price": 50000.0}})
    symbol: str
    side: Literal["buy", "sell"]
    order_type: OrderType
    order_qty: Optional[float] = None
    limit_price: Optional[float] = None
    limit_price_type: Optional[PriceType] = None
    triggers: Optional[OrderTriggersBody] = None
    time_in_force: Optional[Literal["gtc", "gtd", "ioc", "fok"]] = None
    margin: Optional[bool] = None
    post_only: Optional[bool] = None
    reduce_only: Optional[bool] = None
    effective_time: Optional[str] = None
    expire_time: Optional[str] = None
    deadline: Optional[str] = None
    cl_ord_id: Optional[str] = None
    order_userref: Optional[int] = None
    conditional: Optional[dict] = None
    display_qty: Optional[float] = None
    fee_preference: Optional[Literal["base", "quote"]] = None
    stp_type: Optional[Literal["cancel_newest", "cancel_oldest", "cancel_both"]] = None
    cash_order_qty: Optional[float] = None
    validate: Optional[bool] = None
    sender_sub_id: Optional[str] = None
    req_id: Optional[int] = None


class AmendOrderBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"order_id": "OXM2QD-EALR2-YBAVEU", "order_qty": 0.002, "limit_price": 49500.0}})
    order_id: Optional[str] = None
    cl_ord_id: Optional[str] = None
    order_qty: Optional[float] = None
    display_qty: Optional[float] = None
    limit_price: Optional[float] = None
    limit_price_type: Optional[PriceType] = None
    post_only: Optional[bool] = None
    trigger_price: Optional[float] = None
    trigger_price_type: Optional[PriceType] = None
    deadline: Optional[str] = None
    symbol: Optional[str] = None
    req_id: Optional[int] = None


class EditOrderBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"order_id": "OXM2QD-EALR2-YBAVEU", "symbol": "BTC/USD", "order_qty": 0.002, "limit_price": 49500.0}})
    order_id: str
    symbol: str
    order_qty: Optional[float] = None
    limit_price: Optional[float] = None
    order_userref: Optional[int] = None
    display_qty: Optional[float] = None
    post_only: Optional[bool] = None
    reduce_only: Optional[bool] = None
    fee_preference: Optional[Literal["base", "quote"]] = None
    deadline: Optional[str] = None
    validate: Optional[bool] = None
    triggers: Optional[OrderTriggersBody] = None
    req_id: Optional[int] = None


class CancelOrderBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"order_id": ["OXM2QD-EALR2-YBAVEU"]}})
    order_id: Optional[list[str]] = None
    cl_ord_id: Optional[list[str]] = None
    order_userref: Optional[list[int]] = None
    req_id: Optional[int] = None


class CancelAllBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})
    req_id: Optional[int] = None


class CancelAllOrdersAfterBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"timeout": 60}})
    timeout: int = Field(ge=0, lt=86400)
    req_id: Optional[int] = None


class BatchOrderItemBody(BaseModel):
    order_type: OrderType
    side: Literal["buy", "sell"]
    order_qty: Optional[float] = None
    limit_price: Optional[float] = None
    limit_price_type: Optional[PriceType] = None
    triggers: Optional[OrderTriggersBody] = None
    time_in_force: Optional[Literal["gtc", "gtd", "ioc", "fok"]] = None
    margin: Optional[bool] = None
    post_only: Optional[bool] = None
    reduce_only: Optional[bool] = None
    effective_time: Optional[str] = None
    expire_time: Optional[str] = None
    cl_ord_id: Optional[str] = None
    order_userref: Optional[int] = None
    conditional: Optional[dict] = None
    display_qty: Optional[float] = None
    fee_preference: Optional[Literal["base", "quote"]] = None
    stp_type: Optional[Literal["cancel_newest", "cancel_oldest", "cancel_both"]] = None
    cash_order_qty: Optional[float] = None
    sender_sub_id: Optional[str] = None


class BatchAddBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"symbol": "BTC/USD", "orders": [
        {"order_type": "limit", "side": "buy", "order_qty": 0.001, "limit_price": 49000.0},
        {"order_type": "limit", "side": "sell", "order_qty": 0.001, "limit_price": 52000.0},
    ]}})
    symbol: str
    orders: list[BatchOrderItemBody] = Field(min_length=2, max_length=15)
    deadline: Optional[str] = None
    validate: Optional[bool] = None
    req_id: Optional[int] = None


class BatchCancelBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"orders": ["OXM2QD-EALR2-YBAVEU", "OJF3GE-9EJRK-KF8BCA"]}})
    orders: list[Union[str, int]] = Field(min_length=2, max_length=50)
    cl_ord_id: Optional[list[str]] = None
    req_id: Optional[int] = None


class PingBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"target": "public"}})
    target: Literal["public", "private"] = "public"
    req_id: Optional[int] = None


class ConditionBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "symbol": "BTC/USD", "metric": "zscore_24h", "operator": "lt", "threshold": -2.0}})
    symbol: str
    metric: str
    operator: Literal["lt", "lte", "gt", "gte", "crosses_above", "crosses_below"]
    threshold: float
    mode: Literal["one_shot", "rearm"] = "one_shot"
    cooldown_seconds: float = 0.0


def build_router(kraken) -> APIRouter:
    """Build the router for the control server."""
    router = APIRouter()

    admin = APIRouter(tags=["Admin"])
    market_data = APIRouter(tags=["Market Data"])
    user_data = APIRouter(tags=["User Data"])
    trading = APIRouter(tags=["Trading"])
    analytics = APIRouter(tags=["Analytics"])

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
        await kraken.command_queue.put(req)
        return {"status": "queued", "channel": "executions"}

    @user_data.post("/subscribe/balances")
    async def subscribe_balances(body: BalancesSubscribeBody):
        req = BalancesSubscriptionRequest(body.snapshot, body.rebased, body.users, body.req_id)
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

    # ---------------------------------------------------------------------------
    # Trading
    # ---------------------------------------------------------------------------

    @trading.post("/trading/add_order")
    async def add_order(body: AddOrderBody):
        """Submits a new order. The engine ack fires any AddOrderResponse trigger."""
        req = AddOrderRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "add_order", "symbol": body.symbol}

    @trading.post("/trading/amend_order")
    async def amend_order(body: AmendOrderBody):
        """Amends an open order in place, retaining queue priority where possible."""
        if not body.order_id and not body.cl_ord_id:
            return {"status": "error", "detail": "either order_id or cl_ord_id is required"}
        req = AmendOrderRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "amend_order", "order_id": body.order_id or body.cl_ord_id}

    @trading.post("/trading/edit_order")
    async def edit_order(body: EditOrderBody):
        """Cancels and replaces an open order. The replacement receives a new order_id."""
        req = EditOrderRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "edit_order", "order_id": body.order_id}

    @trading.post("/trading/cancel_order")
    async def cancel_order(body: CancelOrderBody):
        """Cancels one or more open orders by order_id, cl_ord_id, or order_userref."""
        if not (body.order_id or body.cl_ord_id or body.order_userref):
            return {"status": "error", "detail": "one of order_id, cl_ord_id, or order_userref is required"}
        req = CancelOrderRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "cancel_order"}

    @trading.post("/trading/cancel_all")
    async def cancel_all(body: CancelAllBody):
        """Cancels all open orders on the account."""
        req = CancelAllRequest(body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "cancel_all"}

    @trading.post("/trading/cancel_all_orders_after")
    async def cancel_all_orders_after(body: CancelAllOrdersAfterBody):
        """
        Dead man's switch: cancels all open orders when the timeout expires unless
        reset by a new request. A timeout of 0 deactivates the mechanism.
        """
        req = CancelAllOrdersAfterRequest(body.timeout, body.req_id)
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "cancel_all_orders_after", "timeout": body.timeout}

    @trading.post("/trading/batch_add")
    async def batch_add(body: BatchAddBody):
        """Submits 2-15 orders for a single currency pair in one request."""
        req = BatchAddRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "batch_add", "symbol": body.symbol, "order_count": len(body.orders)}

    @trading.post("/trading/batch_cancel")
    async def batch_cancel(body: BatchCancelBody):
        """Cancels 2-50 open orders in one request."""
        req = BatchCancelRequest(**body.model_dump(exclude_none=True))
        await kraken.command_queue.put(req)
        return {"status": "queued", "method": "batch_cancel", "order_count": len(body.orders)}

    # ---------------------------------------------------------------------------
    # Analytics
    # ---------------------------------------------------------------------------

    @analytics.get("/indicators")
    async def get_indicators(symbol: Optional[str] = None):
        """
        Returns current computed metrics per symbol: tick-based rolling window stats
        (last, mean_24h, std_24h, high_24h, low_24h, zscore_24h) and candle-based
        MA stats per subscribed ohlc interval (sma_20@15, std_20@15, zscore_20@15).
        Metrics still warming up are null; sample counts indicate progress.
        """
        if kraken.analytics is None:
            return {"status": "error", "detail": "analytics engine is not running"}
        return {"status": "ok", "indicators": kraken.analytics.snapshot(symbol)}

    @analytics.post("/conditions")
    async def register_condition(body: ConditionBody):
        """
        Registers a declarative condition evaluated against live indicator values on
        every update. When it trips, an alert is appended to the queue served by
        GET /alerts. 'one_shot' conditions fire once; 'rearm' conditions fire at most
        once per cooldown_seconds while the condition holds.
        """
        if kraken.analytics is None:
            return {"status": "error", "detail": "analytics engine is not running"}
        condition = kraken.analytics.registry.add(
            body.symbol, body.metric, body.operator, body.threshold,
            body.mode, body.cooldown_seconds,
        )
        return {"status": "registered", "condition": condition.to_dict()}

    @analytics.get("/conditions")
    async def list_conditions():
        """Lists all registered conditions, including tripped one-shots (active=false)."""
        if kraken.analytics is None:
            return {"status": "error", "detail": "analytics engine is not running"}
        return {"status": "ok", "conditions": kraken.analytics.registry.list()}

    @analytics.delete("/conditions/{condition_id}")
    async def delete_condition(condition_id: int):
        """Removes a condition by id."""
        if kraken.analytics is None:
            return {"status": "error", "detail": "analytics engine is not running"}
        removed = kraken.analytics.registry.remove(condition_id)
        return {"status": "deleted" if removed else "not_found", "condition_id": condition_id}

    @analytics.get("/alerts")
    async def get_alerts(since_id: int = 0):
        """
        Returns alerts fired by tripped conditions, oldest first. Poll with
        since_id set to the highest alert id already seen to receive only new alerts.
        """
        if kraken.analytics is None:
            return {"status": "error", "detail": "analytics engine is not running"}
        return {"status": "ok", "alerts": kraken.analytics.registry.alerts_since(since_id)}

    router.include_router(admin)
    router.include_router(market_data)
    router.include_router(user_data)
    router.include_router(trading)
    router.include_router(analytics)

    return router
