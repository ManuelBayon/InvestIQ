from dataclasses import dataclass

import pandas as pd

from investiq.api.backtest import RunId
from investiq.api.features import FeatureComputationResult

@dataclass(frozen=True)
class StepContext:
    run_id: RunId
    step_sequence: int
    source_event_id: str
    market_timestamp: pd.Timestamp

@dataclass(frozen=True)
class FeatureStepEvent:
    context: StepContext
    computations: tuple[FeatureComputationResult,...]