from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import FrozenSet, Protocol

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.market import MarketField

@dataclass(frozen=True)
class FilterMetadata:
    name: str
    version: str
    description: str

    parameters: Mapping[str, object]

    required_features: FrozenSet[str]
    required_market_fields: FrozenSet[MarketField]

    component_type: str = "FILTER"
    created_at: datetime = datetime.now()

class Filter(Protocol):
    metadata: FilterMetadata
    def apply(
            self,
            view: BacktestView,
            decision: Decision
    ) -> Decision: ...
