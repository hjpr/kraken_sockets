
import json

from datetime import datetime, timezone
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
            "req_id": req_id
        }
        request = {k: v for k, v in request.items() if v is not None}
        await self.socket.send(json.dumps(request))