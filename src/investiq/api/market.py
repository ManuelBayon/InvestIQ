from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import pandas as pd

from investiq.api.instruments import Instrument
from investiq.market_data.domain.enums import BarSize


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
    instrument: Instrument
    bar_size: BarSize



class MarketHistoryReader(Protocol):
    def latest(self) -> MarketDataEvent:...
    def window(self, n: int) -> Sequence[MarketDataEvent]:...
    def series(self) -> Sequence[MarketDataEvent]: ...
    def __len__(self) -> int:...

@dataclass(frozen=True)
class MarketView:
    history: MarketHistoryReader
    @property
    def bar(self) -> OHLCV:
        return self.history.latest().bar
    @property
    def timestamp(self) -> pd.Timestamp:
        return self.history.latest().timestamp