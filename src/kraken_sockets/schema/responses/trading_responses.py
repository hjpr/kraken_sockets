
from typing import Optional

from .base_responses import Response


class TradingResponse(Response):
    """
    Base class for trading method acknowledgements. Every trading response shares
    the same envelope: method, success flag, a result object on success or an error
    string on failure, engine timestamps, and the echoed req_id if one was sent.

    Attributes:
        method (str): The trading method being acknowledged e.g. 'add_order'.
        success (bool): Indicates if request was successfully processed by engine.
        result (dict | list): Result payload if success was true.
        error (str): Description of error if success was false.
        time_in (str): Timestamp when request was recieved prior to parsing data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        time_out (str): Timestamp when acknowledgement was sent prior to transmitting data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        req_id (int): Optional client originated request identifier sent as ack to response.
        warnings (list[str]): Non-fatal warnings attached to the acknowledgement.
    """
    method: str
    success: bool
    result: dict
    error: Optional[str]
    time_in: str
    time_out: str
    req_id: Optional[int]
    warnings: list

    def __init__(self, message: dict) -> None:
        self.method = message.get("method", "")
        self.success = message.get("success", False)
        self.result = message.get("result", {})
        self.error = message.get("error")
        self.time_in = message.get("time_in", "")
        self.time_out = message.get("time_out", "")
        self.req_id = message.get("req_id")
        result = self.result if isinstance(self.result, dict) else {}
        self.warnings = result.get("warnings", [])


class AddOrderResponse(TradingResponse):
    """
    Acknowledgement of an 'add_order' request. Fill and status events for the
    accepted order stream on the 'executions' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/add_order

    Attributes:
        order_id (str): Kraken generated order identifier.
        cl_ord_id (str): Client order identifier, echoed if supplied in the request.
        order_userref (int): Numeric client identifier, echoed if supplied in the request.
    """
    order_id: Optional[str]
    cl_ord_id: Optional[str]
    order_userref: Optional[int]

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.order_id = self.result.get("order_id")
        self.cl_ord_id = self.result.get("cl_ord_id")
        self.order_userref = self.result.get("order_userref")


class AmendOrderResponse(TradingResponse):
    """
    Acknowledgement of an 'amend_order' request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/amend_order

    Attributes:
        amend_id (str): Kraken generated amend identifier.
        order_id (str): Kraken order identifier, echoed if supplied in the request.
        cl_ord_id (str): Client order identifier, echoed if supplied in the request.
    """
    amend_id: Optional[str]
    order_id: Optional[str]
    cl_ord_id: Optional[str]

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.amend_id = self.result.get("amend_id")
        self.order_id = self.result.get("order_id")
        self.cl_ord_id = self.result.get("cl_ord_id")


class EditOrderResponse(TradingResponse):
    """
    Acknowledgement of an 'edit_order' request. The edited order receives a new
    order identifier.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/edit_order

    Attributes:
        order_id (str): New Kraken order identifier for the replacement order.
        original_order_id (str): Order identifier of the original order that was replaced.
    """
    order_id: Optional[str]
    original_order_id: Optional[str]

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.order_id = self.result.get("order_id")
        self.original_order_id = self.result.get("original_order_id")


class CancelOrderResponse(TradingResponse):
    """
    Acknowledgement of a 'cancel_order' request. When cancelling multiple orders,
    an individual response is streamed for each order.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_order

    Attributes:
        order_id (str): Kraken order identifier of the cancelled order.
        cl_ord_id (str): Client order identifier, echoed if supplied in the request.
    """
    order_id: Optional[str]
    cl_ord_id: Optional[str]

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.order_id = self.result.get("order_id")
        self.cl_ord_id = self.result.get("cl_ord_id")


class CancelAllResponse(TradingResponse):
    """
    Acknowledgement of a 'cancel_all' request. Individual cancellations are
    streamed on the 'executions' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_all

    Attributes:
        count (int): Number of orders cancelled.
    """
    count: int

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.count = self.result.get("count", 0)


class CancelAllOrdersAfterResponse(TradingResponse):
    """
    Acknowledgement of a 'cancel_all_orders_after' (dead man's switch) request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/cancel_after

    Attributes:
        current_time (str): Current engine timestamp in RFC3339 format.
        trigger_time (str): Timestamp when open orders will be cancelled unless the
            timer is reset, in RFC3339 format. Empty if the mechanism was deactivated.
    """
    current_time: Optional[str]
    trigger_time: Optional[str]

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.current_time = self.result.get("currentTime")
        self.trigger_time = self.result.get("triggerTime")


class BatchAddResponse(TradingResponse):
    """
    Acknowledgement of a 'batch_add' request. The result is a list of order
    confirmations whose sequence matches the request order sequence.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/batch_add

    Attributes:
        orders (list[dict]): Order confirmations, each containing 'order_id' and,
            if supplied in the request, 'cl_ord_id', 'order_userref', and 'warnings'.
    """
    orders: list

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.orders = self.result if isinstance(self.result, list) else []


class BatchCancelResponse(TradingResponse):
    """
    Acknowledgement of a 'batch_cancel' request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/batch_cancel

    Attributes:
        count (int): Number of orders cancelled.
    """
    count: int

    def __init__(self, message: dict) -> None:
        super().__init__(message)
        self.count = self.result.get("count", 0) if isinstance(self.result, dict) else 0
