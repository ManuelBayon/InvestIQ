from collections.abc import Sequence

from investiq.api.market import MarketDataEvent, MarketField, MarketHistoryReader, MarketSateView
from investiq.api.errors import ContextNotInitializedError

class InMemoryMarketHistoryView(MarketHistoryReader):
    """
    Reads-only facade over internal market history storage.
    No full-history copy on each read.
    """
    def __init__(self, history: dict[MarketField, list[float]]) -> None:
        self._history = history

    def latest(self, field: MarketField) -> float:
        seq = self._history.get(field)
        if seq is None:
            raise KeyError(f"No data for field={field}")
        return seq[-1]

    def window(self, field: MarketField, n: int) -> tuple[float, ...]:
        if n <= 0:
            raise IndexError(f"n={n} must be > 0")
        seq = self._history.get(field)
        if seq is None:
            raise KeyError(f"No data for field={field}")
        return tuple(seq[-n:])

    def series(self, field: MarketField) -> Sequence[float]:
        seq = self._history.get(field)
        if seq is None:
            raise KeyError(f"No data for field={field}")
        return tuple(seq)

    def __len__(self) -> int:
        if not self._history:
            return 0
        first = next(iter(self._history.values()))
        return len(first)

class MarketStateStore:
    """
    Internal mutable runtime store for market state.
    """
    def __init__(self):
        self._snapshot: MarketDataEvent | None = None
        self._history: dict[MarketField, list[float]] = {}
        self._history_view = InMemoryMarketHistoryView(self._history)

    def ingest(self, event: MarketDataEvent) -> None:
        self._snapshot = event
        for k, v in event.bar.items():
            self._history.setdefault(MarketField(k), []).append(v)

    def view(self) -> MarketSateView:
        if self._snapshot is None:
            raise ContextNotInitializedError("No MarketEvent processed yet")
        return MarketSateView(
            snapshot=self._snapshot,
            history=self._history_view,
        )