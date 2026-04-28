from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from investiq.api.instruments import InstrumentFactory
from investiq.api.market import MarketDataEvent, OHLCV
from investiq.market_data.domain.enums import BarSize
from investiq_research.features.SMA import SMA

def make_market_event(
        event_id: str = "event_1",
        timestamp: datetime = datetime(2026,4,1),
        close: float = 95,
) -> MarketDataEvent:
   return MarketDataEvent(
        event_id=event_id,
        instrument=InstrumentFactory.stock("AAPL"),
        bar_size=BarSize.ONE_DAY,
        timestamp=timestamp,
        bar=OHLCV(
            open=100,
            high=102,
            low=90,
            close=close,
        )
    )

class TestFeatureCalculatorSMA:

    def test_feature_calculator_id_is_unique_among_same_type(self):
        sma_2 = SMA(2)
        sma_3 = SMA(3)
        assert sma_2.calculator_id != sma_3.calculator_id

    def test_feature_calc_does_not_mutate_OHLCV(self):
        sma_2 = SMA(2)
        event_1 = make_market_event()
        market_view = (event_1,)
        sma_2.calculate(market_view)
        with pytest.raises(FrozenInstanceError):
            market_view[0].bar.close = 999

    def test_feature_calc_does_not_mutate_timestamp(self):
        sma_2 = SMA(2)
        event_1 = make_market_event()
        market_view = (event_1,)
        sma_2.calculate(market_view)
        with pytest.raises(FrozenInstanceError):
            market_view[0].timestamp = datetime(2026, 4, 1)

    def test_feature_calc_sma_returns_none_during_warmup(self):
        sma_2 = SMA(2)
        event_1 = make_market_event()
        result = sma_2.calculate((event_1,))
        assert result is None

    def test_feature_calc_sma_multiple_call_are_deterministic(self):
        sma_2 = SMA(2)
        event_1 = make_market_event()
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
        )
        expected = 95.0
        result = [sma_2.calculate((event_1,event_2))for _ in range(3)]
        assert result == [expected, expected, expected]

    def test_feature_calc_sma_result_is_float_and_correct_once_ready(self):
        sma_2 = SMA(2)
        event_1 = make_market_event()
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=100,
        )
        event_3 = make_market_event(
            event_id="event_3",
            timestamp=datetime(2026, 4, 3),
            close=105,
        )
        result = sma_2.calculate((event_1,event_2, event_3))
        assert isinstance(result, float)
        assert result == 102.5

    def test_feature_calc_raises_if_window_invalid(self):
        with pytest.raises(ValueError):
            SMA(0)
        with pytest.raises(ValueError):
            SMA(-1)