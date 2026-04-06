from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from investiq.api.market import MarketView



@dataclass
class FeaturePoint:
    timestamp: pd.Timestamp
    value: float

class FeatureCalculator(Protocol):
    """
    Feature calculator protocol.
    """
    @property
    def calculator_id(self) -> str:...
    @property
    def key(self) -> str:...
    def calculate(self, market_view: MarketView) -> float | None:...

class FeatureHistoryReader(Protocol):
    """
    Feature history reader protocol.
    It is a wrapper around the FeatureStore class.
    """
    def latest(self, key: str) -> FeaturePoint:...
    def window(self,  key: str, n: int) -> tuple[FeaturePoint, ...]:...
    def series(self,  key: str) -> tuple[FeaturePoint, ...]:...
    def contains(self, key: str) -> bool:...
    def has_data(self,  key: str, quantity: int = 1) -> bool:...

@dataclass(frozen=True)
class FeatureView:

    _reader: FeatureHistoryReader

    def contains(self, key: str) -> bool:
        return self._reader.contains(key)

    def is_ready(self, key: str) -> bool:
        return self._reader.has_data(key)

    def require(self, key: str) -> float:
        return self._reader.latest(key).value

    def latest_point(self, key: str) -> FeaturePoint:
        return self._reader.latest(key)

    def window(self, key: str, n: int) -> tuple[FeaturePoint, ...]:
        return self._reader.window(key, n)

    def series(self, key: str) -> tuple[FeaturePoint, ...]:
        return self._reader.series(key)

@dataclass(frozen=True)
class FeatureComputationResult:
    calculator_id: str
    key: str
    value: float | None
