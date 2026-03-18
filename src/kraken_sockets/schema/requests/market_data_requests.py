
from kraken_sockets.schema.requests.base_requests import SubscriptionRequest, UnsubscribeRequest
from typing import Literal, Optional


class TickerSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'ticker' channel which streams best bid/offer
    and last trade price for requested currency pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ticker#subscribe-request

    Args:
        symbol (list[str]): List of currency pairs to subscribe to e.g. ["BTC/USD", "ETH/USD"].
        event_trigger (str): Event that triggers a ticker update, either 'bbo' (best bid/offer
            change) or 'trades' (on trade). Defaults to 'trades'.
        snapshot (bool): Request a snapshot of current ticker data after subscribing. Defaults to True.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class BookSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'book' channel which streams level 2 order book
    updates for requested currency pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/book#subscribe-request

    Args:
        symbol (list[str]): List of currency pairs to subscribe to e.g. ["BTC/USD", "ETH/USD"].
        depth (int): Number of price levels to maintain on each side of the book,
            one of 10, 25, 100, 500, 1000. Defaults to 10.
        snapshot (bool): Request a snapshot of the current order book after subscribing. Defaults to True.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class OHLCSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'ohlc' channel which streams open, high, low,
    close candle data at the specified interval for requested currency pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ohlc#subscribe-request

    Args:
        symbol (list[str]): List of currency pairs to subscribe to e.g. ["BTC/USD", "ETH/USD"].
        interval (int): Candle interval in minutes, one of 1, 5, 15, 30, 60, 240, 1440, 10080, 21600.
        snapshot (bool): Request a snapshot of recent candles after subscribing. Defaults to True.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class TradesSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'trade' channel which streams executed trades
    in real time for requested currency pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/trade#subscribe-request

    Args:
        symbol (list[str]): List of currency pairs to subscribe to e.g. ["BTC/USD", "ETH/USD"].
        snapshot (bool): If true, the 50 most recent trades are included in the snapshot. Defaults to False.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class InstrumentsSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'instrument' channel which streams reference data
    for all active assets and tradeable pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/instrument#subscribe-request

    Args:
        include_tokenized_assets (bool): If true, tokenized assets (xstocks) are included
            in the stream. Defaults to False.
        snapshot (bool): Request a snapshot of current instrument reference data after subscribing.
            Defaults to True.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class OrdersSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to public 'level3' channel which streams the full level 3
    order book including individual order IDs for requested currency pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/level3#subscribe-request

    Args:
        symbol (list[str]): List of currency pairs to subscribe to e.g. ["BTC/USD", "ETH/USD"].
        depth (int): Number of price levels to maintain on each side of the book,
            one of 10, 100, 1000. Defaults to 10.
        snapshot (bool): Request a snapshot of the current order book after subscribing. Defaults to True.
        req_id (int): Optional client originated request identifier sent as ack in response.
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


class TickerUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'ticker' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ticker#unsubscribe-request

    Args:
        symbol (list[str]): List of currency pairs to unsubscribe from e.g. ["BTC/USD", "ETH/USD"].
        event_trigger (str): Must match the event_trigger used when subscribing, either 'bbo' or 'trades'.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: list[str],
        event_trigger: Optional[Literal["bbo", "trades"]] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "ticker",
            "symbol": symbol,
            "event_trigger": event_trigger,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class BookUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'book' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/book#unsubscribe-request

    Args:
        symbol (list[str]): List of currency pairs to unsubscribe from e.g. ["BTC/USD", "ETH/USD"].
        depth (int): Must match the depth used when subscribing, one of 10, 25, 100, 500, 1000.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: list[str],
        depth: Optional[Literal[10, 25, 100, 500, 1000]] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "book",
            "symbol": symbol,
            "depth": depth,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class OHLCUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'ohlc' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ohlc#unsubscribe-request

    Args:
        symbol (list[str]): List of currency pairs to unsubscribe from e.g. ["BTC/USD", "ETH/USD"].
        interval (int): Must match the interval used when subscribing,
            one of 1, 5, 15, 30, 60, 240, 1440, 10080, 21600.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: list[str],
        interval: Optional[Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]] = None,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        params = {
            "channel": "ohlc",
            "symbol": symbol,
            "interval": interval,
        }
        self.params = {k: v for k, v in params.items() if v is not None}
        self.req_id = req_id


class TradesUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'trade' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/trade#unsubscribe-request

    Args:
        symbol (list[str]): List of currency pairs to unsubscribe from e.g. ["BTC/USD", "ETH/USD"].
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: list[str],
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.params = {
            "channel": "trade",
            "symbol": symbol,
        }
        self.req_id = req_id


class InstrumentsUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'instrument' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/instrument#unsubscribe-request

    Args:
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.params = {
            "channel": "instrument",
        }
        self.req_id = req_id


class OrdersUnsubscribeRequest(UnsubscribeRequest):
    """
    Build unsubscribe message to public 'level3' channel.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/level3#unsubscribe-request

    Args:
        symbol (list[str]): List of currency pairs to unsubscribe from e.g. ["BTC/USD", "ETH/USD"].
        token (str): Session authentication token required for private channels.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    def __init__(
        self,
        symbol: list[str],
        token: str,
        req_id: Optional[int] = None
    ) -> None:
        super().__init__()
        self.public = False
        self.params = {
            "channel": "level3",
            "symbol": symbol,
            "token": token,
        }
        self.req_id = req_id
