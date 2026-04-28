from datetime import datetime
from math import isclose
import pytest

from investiq.api.context import StepContext
from investiq.api.errors import ContextNotInitializedError
from investiq.api.instruments import InstrumentFactory
from investiq.api.market import MarketDataEvent, OHLCV
from investiq.core.features_store import FeatureStore, FeatureComputedEvent, FeaturePoint
from investiq.market_data.domain.enums import BarSize
from investiq.utilities.numeric import nearly_equal
from investiq_research.features.SMA import SMA

def make_market_event(
        id_: int = 1,
        close: float = 95,
) -> MarketDataEvent:
   return MarketDataEvent(
        event_id=f"event_{id_}",
        instrument=InstrumentFactory.stock("AAPL"),
        bar_size=BarSize.ONE_DAY,
        timestamp=datetime(2026,4,id_),
        bar=OHLCV(
            open=100,
            high=150,
            low=50,
            close=close,
        )
    )

def make_step_context(
        id_: int = 1
) -> StepContext:
    return StepContext(
        run_id="test_run_id",
        instrument=InstrumentFactory.stock("AAPL"),
        bar_size=BarSize.ONE_DAY,
        event_id=f"event_{id_}",
        timestamp=datetime(2026,4,id_)
    )


class TestFeatureStoreInit:

    def test_raises_value_error_on_duplicate_keys(self):
        calc_1 = SMA(10)
        calc_2 = SMA(10)

        with pytest.raises(ValueError):
            FeatureStore(
                calculators=[calc_1, calc_2],
            )

    def test_accepts_calculators_with_unique_identifiers(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store._calculators == [calc_1, calc_2]

    def test_initializes_empty_list_for_each_calculator(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store._history[calc_1.calculator_id] == []
        assert store._history[calc_2.calculator_id] == []

class TestFeatureStoreUpdate:

    def test_raises_if_market_view_is_empty(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context()
        market_view = ()
        with pytest.raises(ContextNotInitializedError):
            store.update(step_context, market_view)

    def test_raises_if_context_and_market_view_last_timestamp_diverge(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context()
        event = make_market_event(2)
        market_view = (event,)
        assert step_context.timestamp != event.timestamp
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_context_and_market_view_last_event_id_diverge(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context()
        event = make_market_event(2)
        market_view = (event,)
        assert step_context.event_id != event.event_id
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_accepts_first_market_data_event(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context()
        event = make_market_event()
        market_view = (event,)
        store.update(step_context, market_view)
        assert store._history[calc_1.calculator_id] == []
        assert store._history[calc_2.calculator_id] == []

    def test_returns_feature_computed_event(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context()
        event = make_market_event()
        market_view = (event,)
        result = store.update(step_context, market_view)
        assert result.run_id == step_context.run_id
        assert result.event_id == step_context.event_id
        assert result.timestamp == step_context.timestamp
        assert result.computations[calc_1.calculator_id] == [
            FeaturePoint(
                calculator_id=calc_1.calculator_id,
                timestamp=step_context.timestamp,
                value=None,
            )
        ]
        assert result.computations[calc_2.calculator_id] == [
            FeaturePoint(
                calculator_id=calc_2.calculator_id,
                timestamp=step_context.timestamp,
                value=None,
            )
        ]

    def test_feature_computation_result(self):
        sma_2 = SMA(2)
        sma_3 = SMA(3)
        store = FeatureStore(
            calculators=[sma_2, sma_3],
        )
        event_1 = make_market_event(id_=1, close=100)
        step_context = make_step_context(id_=1)
        market_view = (event_1,)
        store.update(step_context, market_view)

        event_2 = make_market_event(id_=2, close=120)
        step_context = make_step_context(id_=2)
        market_view = (event_1,event_2)
        store.update(step_context, market_view)

        event_3 = make_market_event(id_=3, close=115)
        step_context = make_step_context(id_=3)
        market_view = (event_1, event_2, event_3)
        result = store.update(step_context, market_view)

        assert store.latest(sma_2.calculator_id).calculator_id == sma_2.calculator_id
        assert store.latest(sma_2.calculator_id).timestamp == step_context.timestamp
        assert store.latest(sma_2.calculator_id).value == 117.5

        assert store.latest(sma_3.calculator_id).calculator_id == sma_3.calculator_id
        assert store.latest(sma_3.calculator_id).timestamp == step_context.timestamp
        assert nearly_equal(store.latest(sma_3.calculator_id).value, 111.6666, abs_tol=10e-3)

        assert result.computations[sma_2.calculator_id] == [
            FeaturePoint(
                calculator_id=sma_2.calculator_id,
                timestamp=step_context.timestamp,
                value=store.latest(sma_2.calculator_id).value,
            )
        ]
        assert result.computations[sma_3.calculator_id] == [
            FeaturePoint(
                calculator_id=sma_3.calculator_id,
                timestamp=step_context.timestamp,
                value=store.latest(sma_3.calculator_id).value,
            )
        ]