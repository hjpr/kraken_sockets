
from typing import Optional

from .base_responses import Response


class SubscriptionResponse(Response):
    """
    Response acknowledging that a channel was subscribed to.

    Attributes:
        result (dict): Object storing channel data e.g. name of channel and confirmation of
            user-specified options sent in request.
        success (bool): Indicates if request was successfully processed by engine.
        error (str): Description of error if success was false.
        time_in (str): Timestamp when subscription was recieved prior to parsing data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        time_out (str): Timestamp when acknowledgement was sent prior to transmitting data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        req_id (int): Optional client originated request identified sent as ack to response.
    """
    channel: str
    result: dict
    success: bool
    time_in: str
    time_out: str
    error: Optional[str]
    req_id: Optional[int]

    def __init__(self, message: dict) -> None:
        self.channel = message["result"]["channel"]
        self.result = message["result"]
        self.success = message["success"]
        self.time_in = message["time_in"]
        self.time_out = message["time_out"]
        self.error = message.get("error")
        self.req_id = message.get("req_id")


class UnsubscribeResponse(Response):
    """
    Response acknowledging that a channel was unsubscribed to.

    Attributes:
        result (dict): Object storing name of channel that was unsubscribed.
        success (bool): Indicates if request was successfully processed by engine.
        error (str): Description of error if success was false.
        time_in (str): Timestamp when subscription was recieved prior to parsing data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        time_out (str): Timestamp when acknowledgement was sent prior to transmitting data,
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        req_id (int): Optional client originated request identified sent as ack to response.
    """
    channel: str
    result: dict
    success: bool
    time_in: str
    time_out: str
    error: Optional[str]
    req_id: Optional[int]

    def __init__(self, message: dict) -> None:
        self.channel = message["result"]["channel"]
        self.result = message["result"]
        self.success = message["success"]
        self.time_in = message["time_in"]
        self.time_out = message["time_out"]
        self.error = message.get("error")
        self.req_id = message.get("req_id")