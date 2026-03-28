from investiq.api.config import BacktestConfig
from investiq.market_data import BarSize
from investiq.api.instruments import InstrumentFactory
from investiq.market_data.domain.requests.base import MarketDataRequest

from investiq_research.strategies.MovingAverageCrossStrategy import MovingAverageCrossStrategy

backtest_config = BacktestConfig(
    instrument= InstrumentFactory.cont_future(symbol="MNQ"),
    market_data_request= MarketDataRequest(
        bar_size=BarSize.ONE_HOUR,
        duration="1 Y"
    ),
    strategy=MovingAverageCrossStrategy(
        fast_window=10,
        slow_window=50,
    ),
    filters=None,
    initial_cash=100_000,
)