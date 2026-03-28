from dataclasses import dataclass

from investiq.api.filter import Filter
from investiq.api.instruments import Instrument
from investiq.api.strategy import Strategy
from investiq.market_data.domain.requests.base import MarketDataRequest


@dataclass
class BacktestConfig:
    instrument: Instrument
    market_data_request: MarketDataRequest
    strategy : Strategy
    filters : list[Filter] | None
    initial_cash : float
    debug: bool = False
