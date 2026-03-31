from dataclasses import dataclass
from typing import Protocol, ClassVar

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
    NAME: ClassVar[str]
    @property
    def key(self) -> str:...
    def calculate(self, market_view: MarketView) -> float | None:...

class FeatureHistoryReader(Protocol):
    def latest(self, key: str) -> FeaturePoint:...
    def window(self,  key: str, n: int) -> tuple[FeaturePoint, ...]:...
    def series(self,  key: str) -> tuple[FeaturePoint, ...]:...
    def __len__(self) -> int:...

@dataclass(frozen=True)
class FeatureView:
    history: FeatureHistoryReader