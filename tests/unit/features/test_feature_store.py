from datetime import datetime
from typing import cast

import pandas as pd
import pytest

from investiq.api.backtest import RunId
from investiq.api.events import StepContext, FeatureStepEvent
from investiq.api.features import FeatureCalculator, FeatureComputationResult
from investiq.api.instruments import InstrumentFactory
from investiq.api.market import MarketView, MarketDataEvent, OHLCV
from investiq.core.features_store import FeatureStore
from investiq.core.market_store import InMemoryMarketHistoryReader
from investiq.market_data.domain.enums import BarSize

###################   HELPERS   ###################
class DummyCalculator(FeatureCalculator):
    def __init__(self, key: str, value: float | None = None, calc_id: str = "test"):
        self._calc_id = calc_id
        self._key = key
        self._value = value
    @property
    def calculator_id(self) -> str:
        return self._calc_id
    @property
    def key(self) -> str:
        return self._key
    def calculate(self, market_view) -> float | None:
        return self._value

def make_market_view() -> MarketView:
    return MarketView(
        reader=InMemoryMarketHistoryReader(
            history=[
                MarketDataEvent(
                    event_id="abc",
                    timestamp= cast(
                        pd.Timestamp,
                        datetime(2025, 0o1, 0o1, 12,00,00)
                    ),
                    bar=OHLCV(
                        open=100.0,
                        high=102.0,
                        low=99.0,
                        close=101.0,
                    ),
                    instrument=InstrumentFactory.stock("AAPL"),
                    bar_size=BarSize.ONE_HOUR
                ),
            ]
        )
    )

def make_step_context(
        step_seq: int,
        source_event_id: str,
        ts: pd.Timestamp
) -> StepContext:
    return StepContext(
        run_id=RunId("abc"),
        step_sequence=step_seq,
        source_event_id=source_event_id,
        market_timestamp=ts,
    )

###################   INITIALISATION   ###################

def test_feature_store_init_rejects_duplicate_keys() -> None:
    calc1 = DummyCalculator("sma_20")
    calc2 = DummyCalculator("sma_20")

    with pytest.raises(ValueError):
        FeatureStore([calc1, calc2])

def test_feature_store_init_declares_all_keys_at_init() -> None:
    calc1 = DummyCalculator("sma_20")
    calc2 = DummyCalculator("sma_100")
    store = FeatureStore([calc1, calc2])
    expected_keys = {"sma_20", "sma_100"}
    assert len(store._history.keys()) == 2
    assert set(store._history.keys()) == expected_keys

def test_feature_store_init_has_empty_list_for_all_keys() -> None:
    calc1 = DummyCalculator("sma_20")
    calc2 = DummyCalculator("sma_100")
    store = FeatureStore([calc1, calc2])

    assert (all(isinstance(v, list) for v in store._history.values()))
    assert (all(len(v) == 0 for v in store._history.values()))


###################   .update() - Check pre-conditions - Step Sequence   ###################
def test_feature_store_update_first_step_valid() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    event0 = store.update(context=step0, market_view=market_view)
    assert isinstance(event0, FeatureStepEvent)
    assert event0.context == step0
    step1 = make_step_context(
        step_seq=1,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    event1 = store.update(context=step1, market_view=market_view)
    assert isinstance(event1, FeatureStepEvent)
    assert event1.context == step1


def test_feature_store_update_reject_sequence_less_than_expected() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=-1,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    with pytest.raises(ValueError):
        store.update(context=step0, market_view=market_view)

def test_feature_store_update_reject_sequence_more_than_expected() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=2,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    with pytest.raises(ValueError):
        store.update(context=step0, market_view=market_view)

def test_feature_store_update_reject_duplicate_after_valide_update() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    step1 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    with pytest.raises(ValueError):
        store.update(context=step1, market_view=market_view)

def test_feature_store_update_reject_gap_after_valide_update() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    step1 = make_step_context(
        step_seq=2,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    with pytest.raises(ValueError):
        store.update(context=step1, market_view=market_view)

###################   .update() - Check pre-conditions - Event_id   ###################
def test_feature_store_update_reject_invalid_event_id() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id="123",
        ts=market_view.timestamp,
    )
    with pytest.raises(ValueError):
        store.update(context=step0, market_view=market_view)

###################   .update() - Check pre-conditions - Timestamps   ###################
def test_feature_store_update_reject_invalid_timestamp() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=cast(
            pd.Timestamp,
            datetime(2025, 0o1, 0o1, 1,00,00)
        ),
    )
    with pytest.raises(ValueError):
        store.update(
            context=step0,
            market_view=market_view
        )


###################   .update() - Feature computations   ###################
def test_feature_store_update_skips_none_publications_and_returns_valid_result() -> None:

    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    result = store.update(
        context=step0,
        market_view=market_view
    )
    assert store._history["sma_20"] == []
    assert result.context == step0
    assert len(result.computations) == 1
    expected_result = FeatureComputationResult(
        calculator_id=calc1.calculator_id,
        key=calc1.key,
        value=None
    )
    assert result.computations[0] == expected_result

def test_feature_store_update_appends_feature_point_and_returns_valid_event_when_value_is_published () -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    result = store.update(context=step0, market_view=market_view)
    assert len(store._history[calc1.key]) == 1
    point = store._history[calc1.key][0]
    assert point.timestamp == market_view.timestamp
    assert point.value == 20.0
    assert result.context == step0
    assert len(result.computations) == 1
    expected_result = FeatureComputationResult(
        calculator_id=calc1.calculator_id,
        key=calc1.key,
        value=20.0
    )
    assert result.computations[0] == expected_result

###################   .view.contains()  ###################

def test_feature_store_view_contains_returns_true_for_declared_key() -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    assert store.view.contains(calc1.key)

def test_feature_store_view_contains_returns_false_for_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    assert not store.view.contains("unknown_key")

###################   .view.is_ready()  ###################
def test_feature_store_view_is_ready_returns_true_if_feature_published() -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    assert store.view.is_ready(calc1.key)

def test_feature_store_view_is_ready_returns_false_if_feature_not_published() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    assert not store.view.is_ready(calc1.key)

def test_feature_store_view_is_ready_rejects_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(KeyError):
        store.view.is_ready("abc")

###################   .view.require()  ###################
def test_feature_store_view_require_raises_if_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(KeyError):
        store.view.require("unknown_key")

def test_feature_store_view_require_raises_if_no_value_published() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(ValueError):
        store.view.require("sma_20")

def test_feature_store_view_require_returns_last_feature_float_value() -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    value = store.view.require("sma_20")
    assert value == 20.0

###################   .view.latest_point()  ###################
def test_feature_store_view_latest_point_raises_if_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(KeyError):
        store.view.latest_point("unknown_key")

def test_feature_store_view_latest_point_raises_if_no_value_published() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(ValueError):
        store.view.latest_point("sma_20")

def test_feature_store_view_latest_point_returns_last_feature_float_value() -> None:
    calc1 = DummyCalculator("sma_20", 20.0)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    point = store.view.latest_point("sma_20")
    assert point.value == 20.0
    assert point.timestamp == market_view.timestamp

###################   .view.window()  ###################
def test_feature_store_view_window_raises_if_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(KeyError):
        store.view.window("unknown_key", 1)

def test_feature_store_view_window_raises_if_quantity_negative() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(ValueError):
        store.view.window("sma_20", -1)

def test_feature_store_view_window_raises_if_not_enough_value_are_published() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(ValueError):
        store.view.window("sma_20", 2)

def test_feature_store_view_window_returns_asked_number_points() -> None:
    calc1 = DummyCalculator("sma_20", 20)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    step1 = make_step_context(
        step_seq=1,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step1, market_view=market_view)
    points = store.view.window("sma_20", 2)
    assert len(points) == 2

###################   .view.series()  ###################
def test_feature_store_view_series_raises_if_unknown_key() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(KeyError):
        store.view.series("unknown_key")

def test_feature_store_view_series_raises_if_no_values_published() -> None:
    calc1 = DummyCalculator("sma_20", None)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    with pytest.raises(ValueError):
        store.view.series("sma_20")

def test_feature_store_view_series_returns_all_serie() -> None:
    calc1 = DummyCalculator("sma_20", 20)
    store = FeatureStore([calc1])
    market_view = make_market_view()
    step0 = make_step_context(
        step_seq=0,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step0, market_view=market_view)
    step1 = make_step_context(
        step_seq=1,
        source_event_id=market_view.event_id,
        ts=market_view.timestamp,
    )
    store.update(context=step1, market_view=market_view)
    points = store.view.series("sma_20")
    assert len(points) == 2
