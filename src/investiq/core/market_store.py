from investiq.api.market import MarketDataEvent, MarketHistoryReader, MarketView
from investiq.api.errors import ContextNotInitializedError

class InMemoryMarketHistoryReader(MarketHistoryReader):
    """
    Reads-only facade over internal market history storage.
    No full-history copy on each read using latest() or window().
    """
    def __init__(
            self,
            history: list[MarketDataEvent]
    ) -> None:
        self._history = history

    def latest(self) -> MarketDataEvent:
        if not self._history:
            raise ValueError("No enough data for n=0")
        return self._history[-1]

    def window(self, n: int) -> tuple[MarketDataEvent, ...]:
        if n <= 0:
            raise ValueError(f"n={n} must be > 0")
        seq = self._history[-n:]
        if not seq:
            raise ValueError(f"No enough data for n={n}")
        return tuple(seq)

    def series(self) -> tuple[MarketDataEvent, ...]:
        seq = self._history
        if not seq:
            raise ValueError(f"No enough data.")
        return tuple(seq)

    def __len__(self) -> int:
        return len(self._history)

class MarketStateStore:
    """
    Internal mutable runtime store for market state.
    """
    def __init__(self):
        self._history: list[MarketDataEvent] = []
        self._history_view = InMemoryMarketHistoryReader(self._history)

    def ingest(self, event: MarketDataEvent) -> None:
        self._history.append(event)

    @property
    def view(self) -> MarketView:
        if not self._history:
            raise ContextNotInitializedError("No MarketEvent processed yet")
        return MarketView(self._history_view)