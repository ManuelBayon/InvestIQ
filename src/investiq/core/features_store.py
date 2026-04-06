from collections.abc import Sequence

from investiq.api.events import FeatureStepEvent, StepContext
from investiq.api.features import FeatureHistoryReader, FeatureCalculator, FeatureView, FeaturePoint, FeatureComputationResult
from investiq.api.market import MarketView

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
            raise KeyError(f"Feature '{key}' has no published values yet.")
        seq = self._history[key]
        return seq[-1]

    def window(self,  key: str, n: int) -> tuple[FeaturePoint, ...]:
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        if not self.has_data(key, quantity=n):
            raise KeyError(f"Feature '{key}' has not enough published values yet for quantity={n}.")
        seq = self._history[key]
        return tuple(seq[-n:])

    def series(self,  key: str) -> tuple[FeaturePoint, ...]:
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        if not self.has_data(key):
            raise KeyError(f"Feature '{key}' has no published values yet.")
        seq = self._history[key]
        return tuple(seq)


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
        keys = tuple(calc.key for calc in self._calculators)
        if len(set(keys)) != len(keys):
            raise ValueError(f"Duplicate feature keys: {keys}")

        # 2. Initialize attributes
        self._history: dict[str, list[FeaturePoint]] = {key: [] for key in keys}
        self._history_view = InMemoryFeatureHistoryReader(history=self._history)
        self._last_processed_step_sequence : int = -1

    def update(
            self,
            context: StepContext,
            market_view: MarketView
    ) -> FeatureStepEvent:

        # 1. Check pre-conditions
        expected_step_seq = self._last_processed_step_sequence + 1
        if context.step_sequence != expected_step_seq:
            raise ValueError(
                "StepContext.step_sequence mismatch with last_processed_step_sequence(+1) :"
                f"{context.step_sequence} != {self._last_processed_step_sequence + 1}"
            )
        if context.source_event_id != market_view.event_id:
            raise ValueError(
                "context.source_event_id mismatch with market_view.event_id :"
                f"{context.source_event_id} != {market_view.event_id}"
            )
        if context.market_timestamp != market_view.timestamp:
            raise ValueError(
                "StepContext.market_timestamp and MarketView.timestamp mismatch:"
                f"{context.market_timestamp} != {market_view.timestamp}"
            )

        # 2. Initialization
        computation_results: list[FeatureComputationResult] = []

        # 3. Update features if value is not None
        for calc in self._calculators:

            key = calc.key
            value = calc.calculate(market_view=market_view)

            if value is None:
                computation_results.append(
                    FeatureComputationResult(
                        calculator_id=calc.calculator_id,
                        key=calc.key,
                        value=value,
                    )
                )
                continue

            point = FeaturePoint(
                timestamp=market_view.timestamp,
                value=value
            )
            computation_results.append(
                FeatureComputationResult(
                    calculator_id=calc.calculator_id,
                    key=calc.key,
                    value=point.value,
                )
            )
            self._history[key].append(point)

        # 4. Save last timestamp processed
        self._last_processed_step_sequence = context.step_sequence

        # 5. Build step record
        return FeatureStepEvent(
            context=context,
            computations=tuple(computation_results),
        )


    @property
    def view(self) -> FeatureView:
        return FeatureView(_reader=self._history_view)