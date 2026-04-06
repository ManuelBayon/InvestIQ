from collections.abc import Iterable
from dataclasses import dataclass
from typing import NewType

import pandas as pd

from investiq.api.features import FeatureView
from investiq.api.instruments import Instrument
from investiq.api.market import MarketDataEvent, MarketView
from investiq.api.portfolio import PortfolioView

RunId = NewType("RunId", str)

@dataclass(frozen=True)
class BacktestInput:
    instrument: Instrument
    events: Iterable[MarketDataEvent]

@dataclass(frozen=True)
class BacktestView:
    """
    """
    market_view: MarketView
    features_view: FeatureView
    portfolio_view: PortfolioView