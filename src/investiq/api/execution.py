from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

from investiq.api.backtest import RunId
from investiq.api.instruments import Instrument
from investiq.api.portfolio import Fill


@dataclass(frozen=True)
class Decision:
    market_data_event_id: str
    features_id: str
    decision_id: str
    timestamp: pd.Timestamp
    target_position: float
    execution_price: float

@dataclass(frozen=True)
class RunResult:
    run_id: RunId
    instrument: Instrument
    start: pd.Timestamp
    end: pd.Timestamp
    event_count: int
    runtime_duration: float

    metrics: Mapping[str, float]
    fill_log: Sequence[Fill]

@dataclass(frozen=True)
class DecisionStep:
    ...