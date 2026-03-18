
import json
import time

from typing import Optional
from websockets import ClientConnection


class PingRequest:
    """
    Clients can ping the server to verify connection is alive, and servers will respond
    with a 'pong' response. Build the request and use send()
    """

    socket: ClientConnection

    def __init__(self, socket: ClientConnection) -> None:
        self.socket = socket

    async def send(self, req_id: Optional[int] = None) -> None:
        request = {
            "method": "ping",
            "req_id": req_id if req_id is not None else time.time_ns() // 1000
        }
        await self.socket.send(json.dumps(request))