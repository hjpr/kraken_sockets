
import json

from typing import Optional

class SubscriptionRequest:
    """
    Base structure for subscription message. Contains attributes common to all
    subscription messages. The distinction between auth channels and public channels
    is handled using the 'public' attribute. Optionally 'req_id' can be given with
    any channel subscription as a request identifier.

    Provides the serialize() method as well which automatically drops parameters
    containing None values, and converts to a JSON string for proper request formatting.
    """
    public: bool
    method: str
    params: dict
    req_id: Optional[str]

    def __init__(self):
        self.public = True
        self.method = "subscribe"
        self.params = {}
        self.req_id = None

    def serialize(self) -> str:
        message_body = {
            "method": self.method,
            "params": self.params,
            "req_id": self.req_id
        }
        message_body = {k: v for k, v in message_body.items() if v is not None}
        return json.dumps(message_body)