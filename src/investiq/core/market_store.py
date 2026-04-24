from investiq.api.market import MarketDataEvent
from investiq.api.errors import ContextNotInitializedError, BacktestInvariantError


class MarketStore:
    """
    Internal mutable runtime store for market state.
    """
    def __init__(self):
        self._history: list[MarketDataEvent] = []

    def ingest(self, event: MarketDataEvent) -> None:
        if self._history:
            last_timestamp = self._history[-1].timestamp
            if event.timestamp <= last_timestamp:
                raise BacktestInvariantError(
                    f"Non-monotonically increasing timestamp: "
                    f"received={event.timestamp}, "
                    f"last={last_timestamp}"
                )
        self._history.append(event)

    def latest(self) -> MarketDataEvent:
        if not self._history:
            raise ContextNotInitializedError("No MarketEvent processed yet")
        return self._history[-1]

    def window(self, n: int) -> tuple[MarketDataEvent, ...]:
        if n <= 0:
            raise ValueError(f"n={n} must be > 0")
        if len(self._history) < n:
            raise ValueError(f"n={n} must be <= len(history)={len(self._history)}")
        return tuple(self._history[-n:])