from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import pandas as pd

from investiq.api.instruments import Instrument
from investiq.api.portfolio import Fill


@dataclass(frozen=True)
class Decision:
    timestamp: pd.Timestamp
    target_position: float
    execution_price: float
    diagnostics: dict[str, object] | None = field(default_factory=dict)


@dataclass(frozen=True)
class PortfolioStore:
    current_position: float
    cash: float
    realized_pnl: float
    unrealized_pnl: float

@dataclass(frozen=True)
class RunResult:
    run_id: str
    instrument: Instrument
    start: pd.Timestamp
    end: pd.Timestamp
    event_count: int
    runtime_duration: float


    metrics: Mapping[str, float]
    fill_log: Sequence[Fill]
    diagnostics: Mapping[str, object] = field(default_factory=dict)

@dataclass(frozen=True)
class DecisionStep:
    ...