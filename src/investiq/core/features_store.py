from collections.abc import Sequence
from datetime import datetime

from investiq.api.context import StepContext
from investiq.api.events import FeatureStepEvent
from investiq.api.features import FeatureHistoryReader, FeatureCalculator, FeaturePoint
from investiq.api.market import MarketDataEvent


class InMemoryFeatureHistoryReader(FeatureHistoryReader):
    """
    Wrapper around the FeatureStore class.
    Passed by the view() method of the FeatureStore.
    """
    def __init__(self, history : dict[str, list[FeaturePoint]]) -> None:
        self._history = history

    def contains(self, key: str) -> bool:
        return key in self._history

    def has_data(self, key: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            raise ValueError(f"quantity must be positive: {quantity}")
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        seq = self._history[key]
        return len(seq) >= quantity

    def latest(self, key: str) -> FeaturePoint:
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        if not self.has_data(key):
            raise ValueError(f"Feature '{key}' has no published values yet.")
        seq = self._history[key]
        return seq[-1]

    def window(self,  key: str, n: int) -> tuple[FeaturePoint, ...]:
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        if not self.has_data(key, quantity=n):
            raise ValueError(
                f"Feature '{key}' has not enough published values yet for quantity={n}. "
                f"Has n={len(self._history[key])} values published yet."
            )
        seq = self._history[key]
        return tuple(seq[-n:])


class FeatureStore:
    """
    Stores published feature points for declared feature calculators.
    A feature remains declared with an empty history until first publication.
    """
    def __init__(
            self,
            calculators: Sequence[FeatureCalculator]
    ) -> None:

        # 1. Check pre-conditions
        self._calculators = tuple(calculators)
        calc_ids = tuple(calc.calculator_id for calc in self._calculators)
        if len(set(calc_ids)) != len(calc_ids):
            raise ValueError(f"Duplicate feature keys: {calc_ids}")

        # 2. Initialize attributes
        self._history: dict[str, list[FeaturePoint]] = {calc_id: [] for calc_id in calc_ids}
        self._history_view = InMemoryFeatureHistoryReader(history=self._history)
        self._last_processed_step_sequence : int = -1
        self._last_processed_timestamp : datetime | None = None
        self._last_processed_event_id: str | None = None


    def update(
            self,
            context: StepContext,
            market_view: tuple[MarketDataEvent, ...]
    ) -> FeatureStepEvent:

        last_event = market_view[-1]

        # 1. Check pre-conditions
        # ...

        # 2. Initialization
        computation_results: list[FeatureComputationResult] = []

        # 3.1 Update features if value is not None
        # 3.2 Append computation results to return FeatureStepEvent
        for calc in self._calculators:
            value = calc.calculate(market_view=market_view)
            if value is None:
                computation_results.append(
                    FeatureComputationResult(
                        calculator_id=calc.calculator_id,
                        value=value,
                    )
                )
                continue

            point = FeaturePoint(
                timestamp=last_event.timestamp,
                value=value
            )
            computation_results.append(
                FeatureComputationResult(
                    calculator_id=calc.calculator_id,
                    value=point.value,
                )
            )
            self._history[calc.calculator_id].append(point)

        # 4. Save last processed recorded variables
        self._last_processed_step_sequence = context.step_sequence
        self._last_processed_timestamp = last_event.timestamp
        self._last_processed_event_id = last_event.event_id

        # 5. Build step record
        return FeatureStepEvent(
            context=context,
            computations=tuple(computation_results),
        )


    def latest(self, key) -> FeaturePoint:
        ...

    def window(self) -> tuple[FeaturePoint, ...]:
        ...