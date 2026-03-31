from collections.abc import Sequence

from investiq.api.features import FeatureHistoryReader, FeatureCalculator, FeatureView, FeaturePoint
from investiq.api.market import MarketView

class InMemoryFeatureHistoryView(FeatureHistoryReader):

    def __init__(self, history : dict[str, list[FeaturePoint]]) -> None:
        self._history = history

    def latest(self, key: str) -> FeaturePoint:
        seq = self._history[key]
        if len(seq) == 0:
            raise ValueError(f"Feature {key} has no published values yet.")
        return seq[-1]

    def window(self,  key: str, n: int) -> tuple[FeaturePoint, ...]:
        if n <= 0: raise ValueError(f"Window mus be > 0, got n={n}")
        seq = self._history[key]
        if len(seq) == 0:
            raise ValueError(f"Feature {key} has no published values yet.")
        return tuple(seq[-n:])

    def series(self,  key: str) -> tuple[FeaturePoint, ...]:
        seq = self._history[key]
        if len(seq) == 0:
            raise ValueError(f"Feature {key} has no published values yet.")
        return tuple(seq)

    def __len__(self) -> int:
        return len(self._history)

class FeatureStore:

    def __init__(
        self,
        calculators: Sequence[FeatureCalculator]
    ) -> None:
        self._calculators = tuple(calculators)

        keys = tuple(calc.key for calc in self._calculators)
        if len(set(keys)) != len(keys):
            raise ValueError(f"Duplicate feature keys: {keys}")

        self._history: dict[str, list[FeaturePoint]] = {
            key: [] for key in keys
        }
        self._history_view = InMemoryFeatureHistoryView(self._history)

    def update(
            self,
            market_view: MarketView,
    ) -> None:
        published_at_this_step = set()
        for calc in self._calculators:
            key = calc.key
            if key in published_at_this_step:
                raise ValueError(f"Feature {key} already published at this step.")
            published_at_this_step.add(key)
            value = calc.calculate(market_view=market_view)
            if value is None:
                continue
            timestamp = market_view.timestamp
            point = FeaturePoint(
                timestamp=timestamp,
                value=value,
            )
            self._history[key].append(point)

    def view(self) -> FeatureView:
        return FeatureView(history=self._history_view)