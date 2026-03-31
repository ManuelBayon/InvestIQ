from collections.abc import Iterable
from dataclasses import dataclass

from investiq.api.features import FeatureView
from investiq.api.instruments import Instrument
from investiq.api.market import MarketDataEvent, MarketView
from investiq.api.portfolio import PortfolioView


@dataclass(frozen=True)
class BacktestInput:
    instrument: Instrument
    events: Iterable[MarketDataEvent]

@dataclass(frozen=True)
class BacktestView:
    """
    The ONLY object passed to strategies/orchestrator.
    Read-only contract: strategies cannot mutate the world.
    """
    market_view: MarketView
    features_view: FeatureView
    portfolio_view: PortfolioView