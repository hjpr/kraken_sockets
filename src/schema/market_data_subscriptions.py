import json

from typing import Literal, Optional


class MarketDataSubscriptionMessage:
    """Base structure for subscription message going to a Market Data endpoint."""
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


class TickerSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to Ticker stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/ticker
    """
    params: dict

    def __init__(
        self,
        symbol: list[str],
        event_trigger: Literal["bbo", "trades"] = "trades",
        snapshot: bool = True,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "ticker",
            "symbol": symbol,
            "event_trigger": event_trigger,
            "snapshot": snapshot,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class BookSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to Book stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/book
    """
    params: dict

    def __init__(
        self,
        symbol: list[str],
        depth: Literal[10, 25, 100, 500, 1000] = 10,
        snapshot: bool = True,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "book",
            "symbol": symbol,
            "depth": depth,
            "snapshot": snapshot
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class OHLCSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to OHLC (Candles) stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/ohlc
    """
    params: dict
    
    def __init__(
        self,
        symbol: list [str],
        interval: Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600],
        snapshot: bool = True,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "ohlc",
            "symbol": symbol,
            "interval": interval,
            "snapshot": snapshot
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class TradesSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to Trades stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/trade
    """
    params: dict
    
    def __init__(
        self,
        symbol: list[str],
        snapshot: bool = False,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "trade",
            "symbol": symbol,
            "snapshot": snapshot
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class InstrumentsSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to Instruments stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/instrument
    """
    params: dict

    def __init__(
        self,
        include_tokenized_assets: bool = False,
        snapshot: bool = True,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "instrument",
            "include_tokenized_assets": include_tokenized_assets,
            "snapshot": snapshot
        }
        self.params = params
        self.req_id = req_id


class OrdersSubscriptionMessage(MarketDataSubscriptionMessage):
    """Structure for subscribing to the private Orders stream.
    
    https://docs.kraken.com/api/docs/websocket-v2/level3
    """
    params: dict

    def __init__(
        self,
        symbol: list[str],
        depth: Literal[10, 100, 1000] = 10,
        snapshot: bool = True,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "level3",
            "symbol": symbol,
            "depth": depth,
            "snapshot": snapshot,
        }

        self.public = False
        self.params = params
        self.req_id = req_id