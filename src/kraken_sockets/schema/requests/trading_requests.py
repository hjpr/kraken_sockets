
from kraken_sockets.schema.requests.base_requests import TradingRequest
from typing import Literal, Optional

OrderType = Literal[
    "limit", "market", "iceberg", "stop-loss", "stop-loss-limit", "take-profit",
    "take-profit-limit", "trailing-stop", "trailing-stop-limit", "settle-position"
]
OrderSide = Literal["buy", "sell"]
PriceType = Literal["static", "pct", "quote"]
TimeInForce = Literal["gtc", "gtd", "ioc", "fok"]
FeePreference = Literal["base", "quote"]
STPType = Literal["cancel_newest", "cancel_oldest", "cancel_both"]


class AddOrderRequest(TradingRequest):
    """
    Build 'add_order' message which submits a new order to the matching engine.
    The order acknowledgement is returned as an AddOrderResponse, while fill and
    status events stream on the 'executions' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/add_order

    Args:
        symbol (str): Currency pair e.g. "BTC/USD".
        side (str): Order direction, either 'buy' or 'sell'.
        order_type (str): One of 'limit', 'market', 'iceberg', 'stop-loss', 'stop-loss-limit',
            'take-profit', 'take-profit-limit', 'trailing-stop', 'trailing-stop-limit',
            'settle-position'.
        order_qty (float): Order quantity in terms of the base asset. Not required for
            buy market orders using cash_order_qty.
        limit_price (float): Limit price, required for limit-based order types.
        limit_price_type (str): Units of limit_price, one of 'static', 'pct', 'quote'.
            Kraken defaults to 'quote'.
        triggers (dict): Trigger definition for triggered order types, containing
            'reference' ('index' or 'last'), 'price', and 'price_type' ('static', 'pct', 'quote').
        time_in_force (str): One of 'gtc', 'gtd', 'ioc', 'fok'. Kraken defaults to 'gtc'.
        margin (bool): If true, order is funded on margin. Kraken defaults to False.
        post_only (bool): If true, order is rejected if it cannot be posted passively.
            Kraken defaults to False.
        reduce_only (bool): If true, order will only reduce an existing position.
            Kraken defaults to False.
        effective_time (str): Scheduled start time in RFC3339 format.
        expire_time (str): Expiration time in RFC3339 format, GTD orders only.
        deadline (str): RFC3339 timestamp after which the matching engine should reject
            the order, 500ms to 60s in the future.
        cl_ord_id (str): Client order identifier, UUID or free text up to 18 characters.
        order_userref (int): Non-unique numeric client identifier.
        conditional (dict): Secondary conditional close order template for OTO orders.
        display_qty (float): Visible quantity, iceberg orders only.
        fee_preference (str): Fee currency, 'base' or 'quote'.
        stp_type (str): Self-trade prevention behavior, one of 'cancel_newest',
            'cancel_oldest', 'cancel_both'. Kraken defaults to 'cancel_newest'.
        cash_order_qty (float): Order quantity in terms of the quote currency,
            buy market orders only.
        validate (bool): If true, request is validated only and not submitted to
            the matching engine. Kraken defaults to False.
        sender_sub_id (str): Sub-account identifier for institutional self-trade prevention.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        order_qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        limit_price_type: Optional[PriceType] = None,
        triggers: Optional[dict] = None,
        time_in_force: Optional[TimeInForce] = None,
        margin: Optional[bool] = None,
        post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        effective_time: Optional[str] = None,
        expire_time: Optional[str] = None,
        deadline: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
        order_userref: Optional[int] = None,
        conditional: Optional[dict] = None,
        display_qty: Optional[float] = None,
        fee_preference: Optional[FeePreference] = None,
        stp_type: Optional[STPType] = None,
        cash_order_qty: Optional[float] = None,
        validate: Optional[bool] = None,
        sender_sub_id: Optional[str] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "add_order"
        params = {
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "order_qty": order_qty,
            "limit_price": limit_price,
            "limit_price_type": limit_price_type,
            "triggers": triggers,
            "time_in_force": time_in_force,
            "margin": margin,
            "post_only": post_only,
            "reduce_only": reduce_only,
            "effective_time": effective_time,
            "expire_time": expire_time,
            "deadline": deadline,
            "cl_ord_id": cl_ord_id,
            "order_userref": order_userref,
            "conditional": conditional,
            "display_qty": display_qty,
            "fee_preference": fee_preference,
            "stp_type": stp_type,
            "cash_order_qty": cash_order_qty,
            "validate": validate,
            "sender_sub_id": sender_sub_id,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class AmendOrderRequest(TradingRequest):
    """
    Build 'amend_order' message which modifies an open order in place, retaining
    queue priority where possible. Identify the order with either order_id or cl_ord_id.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/amend_order

    Args:
        order_id (str): Kraken order identifier. Either order_id or cl_ord_id is required.
        cl_ord_id (str): Client order identifier. Either order_id or cl_ord_id is required.
        order_qty (float): New order quantity in terms of the base asset.
        display_qty (float): New visible quantity, iceberg orders only. Minimum 1/15
            of the remaining quantity.
        limit_price (float): New limit price for limit-price-supporting order types.
        limit_price_type (str): Units of limit_price, one of 'static', 'pct', 'quote'.
            Kraken defaults to 'static'.
        post_only (bool): If true, amend is rejected if the order cannot remain passive.
            Kraken defaults to False.
        trigger_price (float): New trigger price for triggered order types.
        trigger_price_type (str): Units of trigger_price, one of 'static', 'pct', 'quote'.
            Kraken defaults to 'static'.
        deadline (str): RFC3339 timestamp after which the matching engine should reject
            the amend, 500ms to 60s in the future.
        symbol (str): Currency pair, required for non-crypto pairs.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        order_id: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
        order_qty: Optional[float] = None,
        display_qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        limit_price_type: Optional[PriceType] = None,
        post_only: Optional[bool] = None,
        trigger_price: Optional[float] = None,
        trigger_price_type: Optional[PriceType] = None,
        deadline: Optional[str] = None,
        symbol: Optional[str] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "amend_order"
        params = {
            "order_id": order_id,
            "cl_ord_id": cl_ord_id,
            "order_qty": order_qty,
            "display_qty": display_qty,
            "limit_price": limit_price,
            "limit_price_type": limit_price_type,
            "post_only": post_only,
            "trigger_price": trigger_price,
            "trigger_price_type": trigger_price_type,
            "deadline": deadline,
            "symbol": symbol,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class EditOrderRequest(TradingRequest):
    """
    Build 'edit_order' message which cancels an open order and replaces it with a
    new one, returning a new order_id. Queue priority is not retained; prefer
    AmendOrderRequest when possible.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/edit_order

    Args:
        order_id (str): Kraken order identifier of the order to edit.
        symbol (str): Currency pair e.g. "BTC/USD".
        order_qty (float): New order quantity in terms of the base asset.
        limit_price (float): New limit price for supported order types.
        order_userref (int): New non-unique numeric client identifier.
        display_qty (float): New visible quantity, iceberg orders only.
        post_only (bool): If true, order is rejected if it cannot be posted passively.
            Kraken defaults to False.
        reduce_only (bool): If true, order will only reduce an existing position.
            Kraken defaults to False.
        fee_preference (str): Fee currency, 'base' or 'quote'.
        deadline (str): RFC3339 timestamp after which the matching engine should reject
            the edit, 500ms to 60s in the future.
        validate (bool): If true, request is validated only and not submitted to
            the matching engine. Kraken defaults to False.
        triggers (dict): Trigger definition for triggered order types, containing
            'reference' ('index' or 'last'), 'price', and 'price_type' ('static', 'pct', 'quote').
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        order_id: str,
        symbol: str,
        order_qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        order_userref: Optional[int] = None,
        display_qty: Optional[float] = None,
        post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        fee_preference: Optional[FeePreference] = None,
        deadline: Optional[str] = None,
        validate: Optional[bool] = None,
        triggers: Optional[dict] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "edit_order"
        params = {
            "order_id": order_id,
            "symbol": symbol,
            "order_qty": order_qty,
            "limit_price": limit_price,
            "order_userref": order_userref,
            "display_qty": display_qty,
            "post_only": post_only,
            "reduce_only": reduce_only,
            "fee_preference": fee_preference,
            "deadline": deadline,
            "validate": validate,
            "triggers": triggers,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class CancelOrderRequest(TradingRequest):
    """
    Build 'cancel_order' message which cancels one or more open orders. Identify
    orders with exactly one of order_id, cl_ord_id, or order_userref. When cancelling
    multiple orders, an individual response is streamed for each order.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_order

    Args:
        order_id (list[str]): Kraken order identifiers. Mutually exclusive with
            cl_ord_id and order_userref.
        cl_ord_id (list[str]): Client order identifiers. Mutually exclusive with
            order_id and order_userref.
        order_userref (list[int]): Numeric client identifiers. Mutually exclusive
            with order_id and cl_ord_id.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        order_id: Optional[list[str]] = None,
        cl_ord_id: Optional[list[str]] = None,
        order_userref: Optional[list[int]] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "cancel_order"
        params = {
            "order_id": order_id,
            "cl_ord_id": cl_ord_id,
            "order_userref": order_userref,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class CancelAllRequest(TradingRequest):
    """
    Build 'cancel_all' message which cancels all open orders on the account,
    including untriggered and resting orders. Individual cancellations are
    streamed on the 'executions' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_all

    Args:
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "cancel_all"
        self.params = {}
        self.req_id = req_id


class CancelAllOrdersAfterRequest(TradingRequest):
    """
    Build 'cancel_all_orders_after' message, the dead man's switch. All open orders
    are cancelled if the timer expires; keep sending new requests to reset the trigger
    time, or send a timeout of 0 to deactivate.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_after

    Args:
        timeout (int): Duration in seconds to set/extend the timer. Must be less
            than 86400. A value of 0 deactivates the mechanism.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        timeout: int,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "cancel_all_orders_after"
        self.params = {
            "timeout": timeout,
        }
        self.req_id = req_id


class BatchAddRequest(TradingRequest):
    """
    Build 'batch_add' message which submits 2 to 15 orders for a single currency
    pair in one request. The whole batch is validated before submission, but
    individual order failures after validation do not reject the batch.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/batch_add

    Args:
        symbol (str): Currency pair for all orders in the batch e.g. "BTC/USD".
        orders (list[dict]): List of 2 to 15 order definitions. Each order supports
            the same fields as AddOrderRequest excluding symbol, deadline, and validate,
            e.g. {"order_type": "limit", "side": "buy", "order_qty": 0.1, "limit_price": 50000}.
        deadline (str): RFC3339 timestamp after which the matching engine should reject
            the batch, 500ms to 60s in the future.
        validate (bool): If true, request is validated only and not submitted to
            the matching engine. Kraken defaults to False.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: str,
        orders: list[dict],
        deadline: Optional[str] = None,
        validate: Optional[bool] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "batch_add"
        params = {
            "symbol": symbol,
            "orders": orders,
            "deadline": deadline,
            "validate": validate,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class BatchCancelRequest(TradingRequest):
    """
    Build 'batch_cancel' message which cancels 2 to 50 open orders in one request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/batch_cancel

    Args:
        orders (list): List of 2 to 50 identifiers, each either a Kraken order_id
            string or a numeric client order_userref.
        cl_ord_id (list[str]): Optional list of client order identifiers to cancel.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        orders: list,
        cl_ord_id: Optional[list[str]] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.method = "batch_cancel"
        params = {
            "orders": orders,
            "cl_ord_id": cl_ord_id,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id
