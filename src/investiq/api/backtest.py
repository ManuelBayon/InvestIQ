from collections.abc import Iterable
from dataclasses import dataclass

from investiq.api.instruments import Instrument
from investiq.api.market import MarketDataEvent, MarketSateView
from investiq.api.portfolio import PortfolioView
from investiq.core.features import FeatureSnapshot


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
    market_view: MarketSateView
    features_view: FeatureSnapshot
    portfolio_view: PortfolioView