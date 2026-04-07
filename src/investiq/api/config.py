from collections.abc import Sequence
from dataclasses import dataclass

from investiq.api.filter import Filter
from investiq.api.instruments import Instrument
from investiq.api.strategy import Strategy
from investiq.core.features_store import FeatureCalculator
from investiq.market_data.domain.requests.base import MarketDataRequest


@dataclass
class BacktestConfig:
    instrument: Instrument
    market_data_request: MarketDataRequest
    feature_calculators: Sequence[FeatureCalculator]
    strategy : Strategy
    filters : Sequence[Filter] | None
    initial_cash : float
    debug: bool = False
