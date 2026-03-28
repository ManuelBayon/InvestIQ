from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from investiq.api.execution import Decision
from investiq.api.market import MarketDataEvent
from investiq.api.portfolio import PortfolioView
from investiq.execution.transition.types import FIFOOperation


@dataclass(frozen=True)
class StepRecord:
    timestamp: pd.Timestamp
    event: MarketDataEvent
    decision: Decision
    transition_result: list[FIFOOperation]
    portfolio_view: PortfolioView
    diagnostics: Mapping[str, object]