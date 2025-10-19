
from dataclasses import dataclass
from typing import Literal

from schema.responses.base_responses import (
    SnapshotResponse,
    UpdateResponse
)


@dataclass
class BookAsk:
    price: float
    qty: float


@dataclass
class BookBid:
    price: float
    qty: float


@dataclass
class Candle:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    trades: int
    volume: float
    vwap: float
    interval_begin: str
    interval: int
    timestamp: str


@dataclass
class Level3Ask:
    order_id: str
    limit_price: float
    order_qty: float
    timestamp: str


@dataclass
class Level3Bid:
    order_id: str
    limit_price: float
    order_qty: float
    timestamp: str


@dataclass
class Level3AskUpdate(Level3Ask):
    event: str


@dataclass
class Level3BidUpdate(Level3Bid):
    event: str


class BookSnapshotResponse(SnapshotResponse):
    """
    Snapshot sent after successful 'book' subscription if snapshot was True.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/book

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **asks**: *(list)* list of asks
        **bids**: *(list)* list of bids
        **checksum**: *(int)* checksum of top 10 bids - asks. see guide at https://docs.kraken.com/api/docs/guides/spot-ws-book-v2
    """
    symbol: str
    asks: list[BookAsk]
    bids: list[BookBid]
    checksum: int

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.asks = [BookAsk(ask["price"], ask["qty"]) for ask in message["data"][0]["asks"]]
        self.bids = [BookBid(bid["price"], bid["qty"]) for bid in message["data"][0]["bids"]]
        self.checksum = message["data"][0]["checksum"]


class BookUpdateResponse(UpdateResponse):
    """
    Response containing updates of bids and asks for relevant symbol.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/book

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **asks**: *(list)* list of asks
        **bids**: *(list)* list of bids
        **checksum**: *(int)* checksum of top 10 bids - asks. see guide at https://docs.kraken.com/api/docs/guides/spot-ws-book-v2
    """
    symbol: str
    asks: list[BookAsk]
    bids: list[BookBid]
    checksum: int
    timestamp: str

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.asks = [BookAsk(ask["price"], ask["qty"]) for ask in message["data"][0]["asks"]]
        self.bids = [BookBid(bid["price"], bid["qty"]) for bid in message["data"][0]["bids"]]
        self.checksum = message["data"][0]["checksum"]


@dataclass
class Asset:
    id: str
    status: Literal[
        "depositonly",
        "disabled",
        "enabled",
        "fundingtemporarilydisabled",
        "withdrawalonly",
        "workinprogress"
    ]
    precision: int
    precision_display: int
    borrowable: bool
    collateral_value: float
    margin_rate: float


@dataclass
class Pair:
    symbol: str
    base: str
    quote: str
    status: Literal[
        "cancel_only",
        "delisted",
        "limit_only",
        "maintenance",
        "online",
        "post_only",
        "reduce_only",
        "work_in_progress"
    ]
    qty_precision: int
    qty_increment: int
    price_precision: int
    cost_precision: int
    marginable: bool
    has_index: bool
    cost_min: float
    margin_initial: float
    position_limit_long: int
    position_limit_short: int
    tick_size: float
    price_increment: float
    qty_min: float


class InstrumentsSnapshotResponse(SnapshotResponse):
    """
    Provides stream of reference data of all active assets and tradeable pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/instrument

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **assets**: *(list)* list of assets
        **pairs**: *(pairs)* list of pairs
    """
    assets: list[Asset]
    pairs: list[Pair]

    def __init__(self, message: dict) -> None:
        self.assets = [
            Asset(
                asset["id"],
                asset["status"],
                asset["precision"],
                asset["precision_display"],
                asset["borrowable"],
                asset["collateral_value"],
                asset["margin_rate"]
            ) for asset in message["data"]["assets"]
        ]
        self.pairs = [
            Pair(
                pair["symbol"],
                pair["base"],
                pair["quote"],
                pair["status"],
                pair["qty_precision"],
                pair["qty_increment"],
                pair["price_precision"],
                pair["cost_precision"],
                pair["marginable"],
                pair["has_index"],
                pair["cost_min"],
                pair["margin_initial"],
                pair["position_limit_short"],
                pair["position_limit_long"],
                pair["tick_size"],
                pair["price_increment"],
                pair["qty_min"]
            ) for pair in message["data"]["pairs"]
        ]


class InstrumentsUpdateResponse(UpdateResponse):
    """
    Provides updates to reference data of all active assets and tradeable pairs.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/instrument

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **assets**: *(list)* list of assets
        **pairs**: *(pairs)* list of pairs
    """
    assets: list[Asset]
    pairs: list[Pair]

    def __init__(self, message: dict) -> None:
        self.assets = [
            Asset(
                asset["id"],
                asset["status"],
                asset["precision"],
                asset["precision_display"],
                asset["borrowable"],
                asset["collateral_value"],
                asset["margin_rate"]
            ) for asset in message["data"]
        ]
        self.pairs = [
            Pair(
                pair["symbol"],
                pair["base"],
                pair["quote"],
                pair["status"],
                pair["qty_precision"],
                pair["qty_increment"],
                pair["price_precision"],
                pair["cost_precision"],
                pair["marginable"],
                pair["has_index"],
                pair["cost_min"],
                pair["margin_initial"],
                pair["position_limit_short"],
                pair["position_limit_long"],
                pair["tick_size"],
                pair["price_increment"],
                pair["qty_min"]
            ) for pair in message["data"]["pairs"]
        ]
   

class OHLCSnapshotResponse(SnapshotResponse):
    """
    Snapshot sent after successful 'ohlc' subscription is snapshot was True

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ohlc

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **timestamp**: *(str)* formatted now timestamp as a string. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        **candles**: *(list)* list of Candles containing candles at intervals specified in request.
    """
    timestamp: str
    candles: list[Candle]

    def __init__(self, message: dict) -> None:
        self.timestamp = message["timestamp"]
        self.candles = [
            Candle(
                candle["symbol"],
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle["trades"],
                candle["volume"],
                candle["vwap"],
                candle["interval_begin"],
                candle["interval"],
                candle["timestamp"]
            ) for candle in message["data"]
        ]


class OHLCUpdateResponse(UpdateResponse):
    """
    Response containing data for candles in intervals specified by 'ohlc' subscription request.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ohlc

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **timestamp**: *(str)* formatted now timestamp as a string. Format - RFC3339 - https://datatracker.ietf.org/doc/html/rfc3339
        **candles**: *(list)*:list of Candles containing candles at intervals specified in request.
    """
    timestamp: str
    candles: list[Candle]

    def __init__(self, message: dict) -> None:
        self.timestamp = message["timestamp"]
        self.candles = [
            Candle(
                candle["symbol"],
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle["trades"],
                candle["volume"],
                candle["vwap"],
                candle["interval_begin"],
                candle["interval"],
                candle["timestamp"]
            ) for candle in message["data"]
        ]


class OrderSnapshotResponse(SnapshotResponse):
    """
    Snapshot sent after successful 'level3' subscription if snapshot was True.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/level3

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **asks**: *(list)* list of asks
        **bids**: *(list)* list of bids
        **checksum**: *(int)* used to verify accuracy of orderbook
    """
    symbol: str
    asks: list[Level3Ask]
    bids: list[Level3Bid]
    checksum: int

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.asks = [
            Level3Ask(
                ask["order_id"],
                ask["limit_price"],
                ask["order_qty"],
                ask["timestamp"]
            ) for ask in message["data"][0]["asks"]
        ]
        self.bids = [
            Level3Bid(
                bid["order_id"],
                bid["limit_price"],
                bid["order_qty"],
                bid["timestamp"]
            ) for bid in message["data"][0]["bids"]
        ]


class OrderUpdateResponse(UpdateResponse):
    """
    Response containing updates in real-time to orderbook.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/level3

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **asks**: *(list)* list of asks
        **bids**: *(list)* list of bids
    """
    symbol: str
    asks: list[Level3AskUpdate]
    bids: list[Level3BidUpdate]
    checksum: int

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.asks = [
            Level3AskUpdate(
                update["order_id"],
                update["limit_price"],
                update["order_qty"],
                update["timestamp"],
                update["event"]
            ) for update in message["data"][0]["asks"]
        ]
        self.bids = [
            Level3BidUpdate(
                update["order_id"],
                update["limit_price"],
                update["order_qty"],
                update["timestamp"],
                update["event"]
            ) for update in message["data"][0]["bids"]
        ]
        self.checksum = message["data"][0]["checksum"]


class TickerSnapshotResponse(SnapshotResponse):
    """
    Snapshot sent after successful 'ticker' subscription if snapshot was True.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ticker

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **bid**: *(float)* best bid price.
        **bid_qty**: *(float)* best bid quantity.
        **ask**: *(float)* best ask price.
        **ask_qty**: *(float)* best ask quantity.
        **last**: *(float)* last traded price (only guaranteed if traded within the past 24h).
        **volume**: *(float)* 24h traded volume (base currency terms).
        **vwap**: *(float)* 24h volume weighted average price.
        **low**: *(float)* 24h lowest trade price.
        **high**: *(float)* 24h highest trade price.
        **change**: *(float)* 24h price change (in quote currency).
        **change_pct**: *(float)* 24h price change (in percentage points).
    """
    symbol: str
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float
    last: float
    volume: float
    vwap: float
    low: float
    high: float
    change: float
    change_pct: float

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.bid = message["data"][0]["bid"]
        self.bid_qty = message["data"][0]["bid_qty"]
        self.ask = message["data"][0]["ask"]
        self.ask_qty = message["data"][0]["ask_qty"]
        self.last = message["data"][0]["last"]
        self.volume = message["data"][0]["volume"]
        self.vwap = message["data"][0]["vwap"]
        self.low = message["data"][0]["low"]
        self.high = message["data"][0]["high"]
        self.change = message["data"][0]["change"]
        self.change_pct = message["data"][0]["change_pct"]


class TickerUpdateResponse(UpdateResponse):
    """
    Update sent for a ticker on a trade event.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/ticker

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **symbol**: *(str)* symbol of the currency pair.
        **bid**: *(float)* best bid price.
        **bid_qty**: *(float)* best bid quantity.
        **ask**: *(float)* best ask price.
        **ask_qty**: *(float)* best ask quantity.
        **last**: *(float)* last traded price (only guaranteed if traded within the past 24h).
        **volume**: *(float)* 24h traded volume (base currency terms).
        **vwap**: *(float)* 24h volume weighted average price.
        **low**: *(float)* 24h lowest trade price.
        **high**: *(float)* 24h highest trade price.
        **change**: *(float)* 24h price change (in quote currency).
        **change_pct**: *(float)* 24h price change (in percentage points).
    """
    symbol: str
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float
    last: float
    volume: float
    vwap: float
    low: float
    high: float
    change: float
    change_pct: float

    def __init__(self, message: dict) -> None:
        self.symbol = message["data"][0]["symbol"]
        self.bid = message["data"][0]["bid"]
        self.bid_qty = message["data"][0]["bid_qty"]
        self.ask = message["data"][0]["ask"]
        self.ask_qty = message["data"][0]["ask_qty"]
        self.last = message["data"][0]["last"]
        self.volume = message["data"][0]["volume"]
        self.vwap = message["data"][0]["vwap"]
        self.low = message["data"][0]["low"]
        self.high = message["data"][0]["high"]
        self.change = message["data"][0]["change"]
        self.change_pct = message["data"][0]["change_pct"]


@dataclass
class Trade:
    symbol: str
    side: str
    price: float
    qty: float
    ord_type: Literal["limit", "market"]
    trade_id: int
    timestamp: str


class TradesSnapshotResponse(SnapshotResponse):
    """
    Snapshot of the 50 most recent trades after successfully subscribing to 'trades'
    and requesting a snapshot.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/trade

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **trades**: *(list)* list containing trades
    """
    trades: list[Trade]

    def __init__(self, message: dict) -> None:
        self.trades = [
            Trade(
                trade["symbol"],
                trade["side"],
                trade["price"],
                trade["qty"],
                trade["ord_type"],
                trade["trade_id"],
                trade["timestamp"]
            ) for trade in message["data"]
        ]


class TradesUpdateResponse(UpdateResponse):
    """
    Response streamed after a trade event.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/trade

    Arg:
        **message**: *(dict)* dict containing response data.

    Attr:
        **trades**: *(list)* list containing trades
    """
    trades: list[Trade]

    def __init__(self, message: dict) -> None:
        self.trades = [
            Trade(
                trade["symbol"],
                trade["side"],
                trade["price"],
                trade["qty"],
                trade["ord_type"],
                trade["trade_id"],
                trade["timestamp"]
            ) for trade in message["data"]
        ]