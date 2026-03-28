from collections.abc import Sequence, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import pandas as pd

class MarketField(StrEnum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"

@dataclass(frozen=True)
class OHLCV:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __getitem__(self, key: str) -> float:
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise KeyError(key) from e

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and hasattr(self, key)

    def items(self):
        for k in ("open","high","low","close","volume"):
            yield k, getattr(self, k)

@dataclass(frozen=True)
class MarketDataEvent:
    timestamp: pd.Timestamp
    bar: OHLCV
    symbol: str | None = None
    bar_size: str | None = None

class MarketHistoryReader(Protocol):
    def latest(self, field: MarketField) -> float:...
    def window(self, field: MarketField, n: int) -> tuple[float, ...]:...
    def series(self, field: MarketField) -> Sequence[float]: ...
    def fields(self) -> tuple[MarketField, ...]:...
    def __len__(self) -> int:...

@dataclass(frozen=True)
class MarketSateView:
    snapshot: MarketDataEvent
    history: MarketHistoryReader
    @property
    def timestamp(self) -> pd.Timestamp:
        return self.snapshot.timestamp

    @property
    def bar(self) -> OHLCV:
        return self.snapshot.bar