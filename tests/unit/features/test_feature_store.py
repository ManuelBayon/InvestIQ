from datetime import datetime

import pytest

from investiq.api.context import StepContext
from investiq.api.errors import ContextNotInitializedError
from investiq.api.feature_calculator import FeatureCalculator
from investiq.api.instruments import InstrumentFactory
from investiq.api.market import MarketDataEvent, OHLCV
from investiq.core.features_store import FeatureStore, FeatureComputedEvent, FeaturePoint
from investiq.market_data.domain.enums import BarSize
from investiq.utilities.numeric import nearly_equal
from investiq_research.features.SMA import SMA

def make_market_event(
        event_id: str = f"event_1",
        timestamp: datetime = datetime(2026,1,1),
        close: float = 100.0,
) -> MarketDataEvent:
   return MarketDataEvent(
        event_id=event_id,
        instrument=InstrumentFactory.stock("AAPL"),
        bar_size=BarSize.ONE_DAY,
        timestamp=timestamp,
        bar=OHLCV(
            open=90,
            high=150,
            low=50,
            close=close,
        )
    )

def make_step_context(
        step_sequence: int = 0,
        event_id: str = f"event_1",
        timestamp: datetime = datetime(2026, 1, 1),
) -> StepContext:
    return StepContext(
        instrument=InstrumentFactory.stock("AAPL"),
        bar_size=BarSize.ONE_DAY,
        run_id="test_run_id",
        step_sequence=step_sequence,
        event_id=event_id,
        timestamp=timestamp,
    )

class RaisingCalculator(FeatureCalculator):
    @property
    def calculator_id(self) -> str:
        return "raising_calc"

    def calculate(
            self,
            market_view: tuple[MarketDataEvent, ...]
    ) -> float | None:
        raise RuntimeError("boom")


class TestFeatureStoreInit:

    def test_raises_value_error_on_duplicate_calculator_id(self):
        calc_1 = SMA(10)
        calc_2 = SMA(10)
        with pytest.raises(ValueError):
            FeatureStore(
                calculators=[calc_1, calc_2],
            )

    def test_accepts_calculators_with_unique_calculator_id(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )

    def test_last_processed_timestamp_is_none(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store._last_processed_timestamp is None

    def test_last_processed_step_sequence_is_minus_one(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store._last_processed_step_sequence == -1

    def test_last_processed_event_id_is_none(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store._last_processed_event_id is None

    def test_initialize_empty_list_for_each_calculator(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        assert store.contains(calc_1.calculator_id)
        assert not store.has_data(calc_1.calculator_id, quantity=1)

        assert store.contains(calc_2.calculator_id)
        assert not store.has_data(calc_2.calculator_id, quantity=1)


class TestFeatureStoreUpdate:

    def test_raises_if_market_view_is_empty(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        market_view = ()
        with pytest.raises(ContextNotInitializedError):
            store.update(step_context, market_view)

    def test_raises_if_context_and_market_view_timestamp_diverge(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 2),
            close=100.0,
        )
        market_view = (event_1,)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_context_timestamp_equals_last_processed_timestamp(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=1,
            event_id="event_2",
            timestamp=datetime(2026, 4, 1),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view=(event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_context_timestamp_is_less_than_last_processed_timestamp(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=1,
            event_id="event_2",
            timestamp=datetime(2026, 3, 25),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view=(event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_context_and_market_view_event_id_diverge(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_context_event_id_equals_last_processed_event_id(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=1,
            event_id="event_1",
            timestamp=datetime(2026, 4, 2),
        )
        event_2= make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=100.0,
        )
        market_view = (event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_step_sequence_equals_last_processed(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=0,
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=100.0,
        )
        market_view = (event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_step_sequence_is_less_than_last_processed_plus_one(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=-2,
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=100.0,
        )
        market_view = (event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_raises_if_step_sequence_is_greater_than_last_processed_plus_one(self):
        calc_1 = SMA(10)
        calc_2 = SMA(20)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        step_context = make_step_context(
            step_sequence=2,
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=100.0,
        )
        market_view = (event_1, event_2)
        with pytest.raises(ValueError):
            store.update(step_context, market_view)

    def test_updates_first_event_nominal_path(self):
        sma_1 = SMA(1)
        sma_2 = SMA(2)
        store = FeatureStore(calculators=[sma_1, sma_2])

        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        assert nearly_equal(store.latest(sma_1.calculator_id).value, 100.0, abs_tol=10e-3)
        assert not store.has_data(sma_2.calculator_id)

    def test_returns_feature_computed_event(self):
        calc_1 = SMA(1)
        calc_2 = SMA(2)
        store = FeatureStore(
            calculators=[calc_1, calc_2],
        )
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        result = store.update(step_context, market_view)

        assert result.run_id == step_context.run_id
        assert result.event_id == step_context.event_id
        assert result.timestamp == step_context.timestamp
        assert result.computations[calc_1.calculator_id].value == 100.0
        assert result.computations[calc_2.calculator_id].value is None

    def test_feature_computation_result(self):
        sma_2 = SMA(2)
        sma_3 = SMA(3)
        store = FeatureStore(
            calculators=[sma_2, sma_3],
        )

        # Step : 0
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)
        store.update(step_context, market_view)

        # Step : 1
        step_context = make_step_context(
            step_sequence=1,
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
        )
        event_2 = make_market_event(
            event_id="event_2",
            timestamp=datetime(2026, 4, 2),
            close=120.0,
        )
        market_view = (event_1,event_2)
        store.update(step_context, market_view)

        # Step : 2
        step_context = make_step_context(
            step_sequence=2,
            event_id="event_3",
            timestamp=datetime(2026, 4, 3),
        )
        event_3 = make_market_event(
            event_id="event_3",
            timestamp=datetime(2026, 4, 3),
            close=130.0,
        )
        market_view = (event_1, event_2, event_3)
        result = store.update(step_context, market_view)

        assert result.run_id == step_context.run_id
        assert result.event_id == step_context.event_id
        assert result.timestamp == step_context.timestamp
        assert nearly_equal(result.computations[sma_2.calculator_id].value,125.0, 10e-3)
        assert nearly_equal(result.computations[sma_3.calculator_id].value,116.66, 10e-3)

    def test_on_calculator_error_no_history_mutation(self):

        raising_calc = RaisingCalculator()
        sma_3 = SMA(1)
        store = FeatureStore(
            calculators=[sma_3, raising_calc],
        )
        # Step : 0
        step_context = make_step_context(
            step_sequence=0,
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
        )
        event_1 = make_market_event(
            event_id="event_1",
            timestamp=datetime(2026, 4, 1),
            close=100.0,
        )
        market_view = (event_1,)

        with pytest.raises(RuntimeError):
            store.update(step_context, market_view)
        assert not store.has_data(sma_3.calculator_id)
        assert not store.has_data(raising_calc.calculator_id)
        assert store._last_processed_step_sequence == -1
        assert store._last_processed_event_id is None
        assert store._last_processed_timestamp is None
