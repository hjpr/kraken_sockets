
import itertools
import statistics
import time

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal, Optional

from kraken_sockets.schema.responses import (
    OHLCSnapshotResponse,
    OHLCUpdateResponse,
    Response,
    TickerSnapshotResponse,
    TickerUpdateResponse,
)

Operator = Literal["lt", "lte", "gt", "gte", "crosses_above", "crosses_below"]
ConditionMode = Literal["one_shot", "rearm"]

# Full recompute interval for the incremental rolling sums, to cap floating point drift
RECOMPUTE_EVERY = 5000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Condition:
    """
    A declarative trip condition evaluated against live indicator values.

    Metrics use the engine's naming: tick-based metrics are plain names
    ('last', 'zscore_24h', 'mean_24h', ...), candle-based metrics are suffixed
    with the candle interval in minutes, e.g. 'zscore_20@15' for the z-score
    against the 20-period SMA on 15 minute candles.

    Modes: 'one_shot' fires once then deactivates; 'rearm' keeps firing on each
    qualifying evaluation, at most once per cooldown_seconds. Crossing operators
    fire only on a threshold crossing between consecutive evaluations.
    """
    id: int
    symbol: str
    metric: str
    operator: Operator
    threshold: float
    mode: ConditionMode = "one_shot"
    cooldown_seconds: float = 0.0
    created_at: str = field(default_factory=_utc_now)
    active: bool = True
    _last_fired_mono: Optional[float] = None
    _prev_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "mode": self.mode,
            "cooldown_seconds": self.cooldown_seconds,
            "created_at": self.created_at,
            "active": self.active,
        }

    def check(self, value: float) -> bool:
        """Returns True if the condition should fire for this value, updating internal state."""
        prev = self._prev_value
        self._prev_value = value

        match self.operator:
            case "lt":
                met = value < self.threshold
            case "lte":
                met = value <= self.threshold
            case "gt":
                met = value > self.threshold
            case "gte":
                met = value >= self.threshold
            case "crosses_above":
                met = prev is not None and prev <= self.threshold and value > self.threshold
            case "crosses_below":
                met = prev is not None and prev >= self.threshold and value < self.threshold
            case _:
                met = False

        if not met or not self.active:
            return False
        now = time.monotonic()
        if self._last_fired_mono is not None and (now - self._last_fired_mono) < self.cooldown_seconds:
            return False
        self._last_fired_mono = now
        if self.mode == "one_shot":
            self.active = False
        return True


@dataclass
class Alert:
    """A record of a condition that tripped, kept for agents to poll."""
    id: int
    condition_id: int
    symbol: str
    metric: str
    operator: str
    threshold: float
    value: float
    fired_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "condition_id": self.condition_id,
            "symbol": self.symbol,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "value": self.value,
            "fired_at": self.fired_at,
        }


class ConditionRegistry:
    """
    Holds declarative conditions registered at runtime (e.g. by an agent over the
    control API) and the bounded log of alerts they produce when tripped.
    """

    def __init__(self, logger: Optional[Callable] = None, max_alerts: int = 1000):
        self._logger = logger
        self._conditions: dict[int, Condition] = {}
        self._alerts: deque[Alert] = deque(maxlen=max_alerts)
        self._condition_ids = itertools.count(1)
        self._alert_ids = itertools.count(1)

    def add(
        self,
        symbol: str,
        metric: str,
        operator: Operator,
        threshold: float,
        mode: ConditionMode = "one_shot",
        cooldown_seconds: float = 0.0,
    ) -> Condition:
        condition = Condition(
            id=next(self._condition_ids),
            symbol=symbol,
            metric=metric,
            operator=operator,
            threshold=threshold,
            mode=mode,
            cooldown_seconds=cooldown_seconds,
        )
        self._conditions[condition.id] = condition
        return condition

    def remove(self, condition_id: int) -> bool:
        return self._conditions.pop(condition_id, None) is not None

    def list(self) -> list[dict]:
        return [c.to_dict() for c in self._conditions.values()]

    def alerts_since(self, since_id: int = 0) -> "list[dict]":
        return [a.to_dict() for a in self._alerts if a.id > since_id]

    def evaluate(self, symbol: str, metrics: dict) -> "list[Alert]":
        """Checks every condition on this symbol against fresh metric values."""
        fired = []
        for condition in self._conditions.values():
            if condition.symbol != symbol or not condition.active:
                continue
            value = metrics.get(condition.metric)
            if value is None:
                continue
            if condition.check(value):
                alert = Alert(
                    id=next(self._alert_ids),
                    condition_id=condition.id,
                    symbol=symbol,
                    metric=condition.metric,
                    operator=condition.operator,
                    threshold=condition.threshold,
                    value=value,
                )
                self._alerts.append(alert)
                fired.append(alert)
                if self._logger:
                    self._logger(
                        f"Condition {condition.id} tripped: {symbol} {condition.metric} "
                        f"{condition.operator} {condition.threshold} (value: {value})",
                        "warning",
                    )
        return fired


class _TickWindow:
    """Time-windowed series of ticker prices with O(1) rolling mean/std via running sums."""

    def __init__(self, window_seconds: float):
        self.window_seconds = window_seconds
        self.points: deque[tuple[float, float]] = deque()
        self.total = 0.0
        self.total_sq = 0.0
        self._events = 0

    def add(self, price: float, now: Optional[float] = None) -> None:
        now = now if now is not None else time.time()
        self.points.append((now, price))
        self.total += price
        self.total_sq += price * price
        cutoff = now - self.window_seconds
        while self.points and self.points[0][0] < cutoff:
            _, old = self.points.popleft()
            self.total -= old
            self.total_sq -= old * old
        self._events += 1
        if self._events % RECOMPUTE_EVERY == 0:
            self.total = sum(p for _, p in self.points)
            self.total_sq = sum(p * p for _, p in self.points)

    def stats(self) -> dict:
        n = len(self.points)
        if n == 0:
            return {"samples": 0}
        mean = self.total / n
        variance = max(self.total_sq / n - mean * mean, 0.0)
        std = variance ** 0.5
        last = self.points[-1][1]
        prices = [p for _, p in self.points]
        return {
            "samples": n,
            "last": last,
            "mean": mean,
            "std": std,
            "high": max(prices),
            "low": min(prices),
            "zscore": (last - mean) / std if std > 0 else None,
        }


class _CandleWindow:
    """Rolling series of candle closes for one (symbol, interval), replacing the live candle in place."""

    def __init__(self, max_window: int):
        self.closes: deque[float] = deque(maxlen=max_window)
        self.last_interval_begin: Optional[str] = None

    def add(self, interval_begin: str, close: float) -> None:
        if self.last_interval_begin == interval_begin and self.closes:
            self.closes[-1] = close
        else:
            self.closes.append(close)
            self.last_interval_begin = interval_begin

    def stats(self, window: int) -> dict:
        if len(self.closes) < window:
            return {"samples": len(self.closes)}
        values = list(self.closes)[-window:]
        sma = statistics.fmean(values)
        std = statistics.pstdev(values)
        last = values[-1]
        return {
            "samples": len(self.closes),
            "sma": sma,
            "std": std,
            "zscore": (last - sma) / std if std > 0 else None,
        }


class IndicatorEngine:
    """
    Computes rolling statistics from live market data streams and evaluates
    registered conditions against them on every update.

    Consumes ticker and ohlc responses via the KrakenWebSocketAPI observer hook,
    leaving all user trigger slots free. Metrics per symbol:

    Tick-based (from ticker 'last' price, time-windowed, default 24h):
        last, mean_24h, std_24h, high_24h, low_24h, zscore_24h, samples_24h

    Candle-based (from ohlc closes, per subscribed interval, per MA window):
        sma_{n}@{interval}, std_{n}@{interval}, zscore_{n}@{interval},
        candles@{interval}

    Args:
        kraken: KrakenWebSocketAPI instance to observe. May be None for offline use;
            feed responses manually via on_response().
        ma_windows (tuple[int]): SMA window lengths computed per candle interval.
            Defaults to (20,).
        time_window_hours (float): Length of the tick-based rolling window in hours.
            Defaults to 24.
    """

    def __init__(self, kraken=None, ma_windows: tuple = (20,), time_window_hours: float = 24.0):
        self.kraken = kraken
        self.ma_windows = tuple(sorted(set(ma_windows)))
        self.time_window_hours = time_window_hours
        self._window_label = f"{time_window_hours:g}h"
        self.registry = ConditionRegistry(logger=kraken.log if kraken else None)
        self._ticks: dict[str, _TickWindow] = {}
        self._candles: dict[tuple[str, int], _CandleWindow] = {}
        self.metrics: dict[str, dict] = {}
        if kraken is not None:
            kraken.add_observer(self.on_response)

    async def on_response(self, response: Response) -> None:
        """Observer entrypoint: routes ticker and ohlc responses into the rolling windows."""
        if isinstance(response, (TickerSnapshotResponse, TickerUpdateResponse)):
            self._on_tick(response.symbol, response.last)
        elif isinstance(response, (OHLCSnapshotResponse, OHLCUpdateResponse)):
            symbols = set()
            for candle in response.candles:
                window = self._candles.setdefault(
                    (candle.symbol, candle.interval),
                    _CandleWindow(max(self.ma_windows) + 1),
                )
                window.add(candle.interval_begin, candle.close)
                symbols.add((candle.symbol, candle.interval))
            for symbol, interval in symbols:
                self._refresh_candle_metrics(symbol, interval)
                self.registry.evaluate(symbol, self.metrics[symbol])

    def _on_tick(self, symbol: str, last: float) -> None:
        if last is None:
            return
        window = self._ticks.setdefault(symbol, _TickWindow(self.time_window_hours * 3600))
        window.add(last)
        stats = window.stats()
        label = self._window_label
        symbol_metrics = self.metrics.setdefault(symbol, {})
        symbol_metrics.update({
            "last": stats.get("last"),
            f"mean_{label}": stats.get("mean"),
            f"std_{label}": stats.get("std"),
            f"high_{label}": stats.get("high"),
            f"low_{label}": stats.get("low"),
            f"zscore_{label}": stats.get("zscore"),
            f"samples_{label}": stats["samples"],
            "updated_at": _utc_now(),
        })
        self.registry.evaluate(symbol, symbol_metrics)

    def _refresh_candle_metrics(self, symbol: str, interval: int) -> None:
        window = self._candles[(symbol, interval)]
        symbol_metrics = self.metrics.setdefault(symbol, {})
        symbol_metrics[f"candles@{interval}"] = len(window.closes)
        for n in self.ma_windows:
            stats = window.stats(n)
            symbol_metrics[f"sma_{n}@{interval}"] = stats.get("sma")
            symbol_metrics[f"std_{n}@{interval}"] = stats.get("std")
            symbol_metrics[f"zscore_{n}@{interval}"] = stats.get("zscore")
        symbol_metrics["updated_at"] = _utc_now()

    def snapshot(self, symbol: Optional[str] = None) -> dict:
        """
        Returns current computed metrics, either for one symbol or all symbols.
        Metrics that have not warmed up yet are None; sample counts indicate progress.
        """
        if symbol is not None:
            return {symbol: self.metrics.get(symbol, {})}
        return dict(self.metrics)
