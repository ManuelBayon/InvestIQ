from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision

@dataclass(frozen=True)
class StrategyMetadata:
    name: str
    version: str
    description: str
    parameters: Mapping[str, float]
    required_feature_names: tuple[str, ...]

    created_at: datetime = field(default_factory=datetime.now)

class Strategy(Protocol):
    metadata: StrategyMetadata
    def decide(
            self,
            backtest_view: BacktestView
    ) -> Decision:
        ...