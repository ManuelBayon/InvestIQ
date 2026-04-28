from datetime import datetime

import pytest

from investiq.api.errors import BacktestInvariantError, ContextNotInitializedError
from investiq.api.instruments import Instrument
from investiq.core.market_store import MarketStore
from investiq.api.market import MarketDataEvent, OHLCV
from investiq.market_data.domain.enums import AssetType, Exchange, Currency, BarSize


def make_instrument() -> Instrument:
    return Instrument(
        asset_type=AssetType.STOCK,
        symbol="AAPL",
        exchange=Exchange.SMART,
        tick_size=1,
        lot_size=1,
        contract_multiplier=1,
        currency=Currency.USD,
    )

def make_event(
        event_id: str = "event_01",
        timestamp: datetime = datetime(2020, 1, 1),
) -> MarketDataEvent:
    return MarketDataEvent(
        event_id=event_id,
        timestamp=timestamp,
        bar=OHLCV(
            open=100,
            high=101,
            low=98,
            close=100,
        ),
        bar_size=BarSize.ONE_DAY,
        instrument=make_instrument(),
    )

class TestMarketStoreIngest:

    # positive cases

    def test_ingest_accepts_first_event(self):
        store = MarketStore()
        event = make_event()
        store.ingest(event)
        assert store.latest() == event

    def test_ingest_accepts_strictly_increasing_timestamps(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        assert store.latest() == event_2

    def test_ingest_preserves_order(self):
        store = MarketStore()
        event_1 = make_event()
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_1)
        store.ingest(event_2)
        assert store.window(2)[0] == event_1
        assert store.window(2)[1] == event_2

    # negative cases

    def test_ingest_rejects_equal_timestamp(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_same_timestamp = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 1),
        )
        with pytest.raises(BacktestInvariantError):
            store.ingest(event_same_timestamp)

    def test_ingest_rejects_decreasing_timestamp(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_timestamp_anterior_to_previous = make_event(
            event_id="event_02",
            timestamp=datetime(2019, 1, 2),
        )
        with pytest.raises(BacktestInvariantError):
            store.ingest(event_timestamp_anterior_to_previous)


class TestMarketStoreLatest:

    def test_latest_raises_when_store_is_empty(self):
        store = MarketStore()
        with pytest.raises(ContextNotInitializedError):
            store.latest()

    def test_latest_returns_last_ingested_event(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        assert store.latest() == event_2


class TestMarketStoreWindow:

    def test_window_raises_when_n_is_negative(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        with pytest.raises(ValueError):
            store.window(-1)

    def test_window_raises_when_n_is_zero(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        with pytest.raises(ValueError):
            store.window(0)

    def test_window_raises_when_n_exceeds_history_length(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        with pytest.raises(ValueError):
            store.window(2)

    def test_window_returns_last_n_events_in_order(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        assert store.window(2)[0] == event_1
        assert store.window(2)[1] == event_2

    def test_window_returns_full_history_when_n_equals_length(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        events = store.window(2)
        assert events[0] == event_1
        assert events[1] == event_2

    def test_window_returns_single_last_event_when_n_equals_one(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        events = store.window(1)
        assert events[0] == event_1

    def test_window_one_is_consistent_with_latest(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_window = store.window(1)
        event_latest = store.latest()
        assert event_window[0] == event_latest

    def test_window_is_independent_from_future_ingestion(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        before_events = store.window(2)
        event_3 = make_event(
            event_id="event_03",
            timestamp=datetime(2020, 1, 3),
        )
        store.ingest(event_3)
        assert before_events == (event_1, event_2)

    def test_window_returns_immutable_tuple(self):
        store = MarketStore()
        event_1 = make_event()
        store.ingest(event_1)
        event_2 = make_event(
            event_id="event_02",
            timestamp=datetime(2020, 1, 2),
        )
        store.ingest(event_2)
        events = store.window(2)
        assert isinstance(events, tuple)
        with pytest.raises(TypeError):
            events[0] = make_event(
                event_id="event_03",
                timestamp=datetime(2020, 1, 3),
            )