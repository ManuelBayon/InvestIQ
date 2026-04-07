from investiq.api.config import BacktestConfig
from investiq.api.instruments import InstrumentFactory
from investiq.market_data.domain.enums import BarSize
from investiq.market_data.domain.requests.base import MarketDataRequest
from investiq_research.features.SMA import SMA

from investiq_research.strategies.MovingAverageCrossStrategy import MovingAverageCrossStrategy

backtest_config = BacktestConfig(
    instrument=InstrumentFactory.cont_future(symbol="MNQ"),
    market_data_request=MarketDataRequest(
        bar_size=BarSize.ONE_HOUR,
        duration="6 M"
    ),
    feature_calculators=[
        SMA(window=20),
        SMA(window=100)
    ],
    strategy=MovingAverageCrossStrategy(
        fast_window=20,
        slow_window=100,
    ),
    filters=None,
    initial_cash=100_000
)