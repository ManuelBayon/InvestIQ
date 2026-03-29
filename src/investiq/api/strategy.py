from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, FrozenSet

import pandas as pd

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.market import MarketField

@dataclass(frozen=True)
class StrategyMetadata:
    name: str
    version: str
    description: str

    parameters: Mapping[str, object]

    required_features: FrozenSet[str]

    component_type: str = "STRATEGY"
    created_at: pd.Timestamp = field(default_factory=datetime.now)

class Strategy(Protocol):

    metadata: StrategyMetadata

    def decide(self, view: BacktestView) -> Decision:
        ...