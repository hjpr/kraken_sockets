
import time

from datetime import datetime, timezone
from typing import Literal

from schema.responses.base_responses import Response


class HeartbeatResponse(Response):
    """
    Channel 'heartbeat' sends out a constant response approx 1 per second in the
    absence of any other channel updates.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/heartbeat
    """
    time_received: str

    def __init__(self) -> None:
        self.time_received = datetime.now(timezone.utc).isoformat()


class PingResponse(Response):
    """
    Response following a ping request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ping

    Attr:
        time_sent (int): UNIX ns timestamp for when request was sent to server.
        time_in (str): Timestamp when request was recieved on the wire, prior to parsing data.
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        time_out (str): Timestamp when response was sent on the wire, prior to transmitting data.
            e.g. 2022-12-25T09:30:59.123456Z. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        time_recieved(int): UNIX ns timestamp for when request was recieved back from server.

    """
    time_sent: int
    time_in: datetime
    time_out: datetime
    time_recieved: int

    def __init__(self, message: dict) -> None:
        self.time_recieved = time.time_ns() // 1000 # UNIX time in micros
        self.time_in = datetime.fromisoformat(message["time_in"])
        self.time_out = datetime.fromisoformat(message["time_out"])
        self.time_sent = message["req_id"]

    def round_trip_ms(self) -> float:
        """Returns round trip time in ms."""
        round_trip = (self.time_recieved - self.time_sent)
        return round(round_trip /1000, 3)

    def server_latency_ms(self) -> float:
        """Returns round trip time"""
        server_latency = (self.time_out - self.time_in)
        return round(server_latency.microseconds / 1000, 3)


class StatusResponse(Response):
    """
    Provides mechanism to verify exchange status and successful initial connection.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/status

    Arg:
        data (dict): contains exchange status and connection info.

    Attr:
        system (str): status of the trading engine.
        api_version (str): websockets api version.
        connection_id (int): unique connection id for debugging.
        version (str): version of the websockets service. 
    """
    system: Literal["online", "maintenance", "cancel_only", "post_only"]
    api_version: str
    connection_id: int
    version: str

    def __init__(self, message: dict) -> None:
        self.system = message["data"][0]["system"]
        self.api_version = message["data"][0]["api_version"]
        self.connection_id = message["data"][0]["connection_id"]
        self.version = message["data"][0]["version"]
