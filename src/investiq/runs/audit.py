from dataclasses import dataclass

import pandas as pd

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.market import MarketDataEvent
from investiq.api.types import FIFOOperation


@dataclass(frozen=True)
class StepRecord:
    timestamp: pd.Timestamp
    event: MarketDataEvent
    view_before: BacktestView
    view_after: BacktestView
    decision: Decision
    fills: list[FIFOOperation]