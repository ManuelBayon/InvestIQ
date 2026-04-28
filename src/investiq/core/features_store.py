from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from investiq.api.context import StepContext
from investiq.api.errors import ContextNotInitializedError
from investiq.api.feature_calculator import FeatureCalculator
from investiq.api.market import MarketDataEvent

@dataclass(frozen=True)
class FeaturePoint:
    calculator_id: str
    timestamp: datetime
    value: float | None

@dataclass(frozen=True)
class FeatureComputedEvent:
    run_id: str
    event_id: str
    timestamp: datetime
    computations: dict[str, list[FeaturePoint]]

class FeatureStore:
    """
    """
    def __init__(
            self,
            calculators: Sequence[FeatureCalculator]
    ) -> None:

        # Check if calculator_id are uniques
        keys = [calc.calculator_id for calc in calculators]
        seen = set()
        duplicates = set()
        for k in keys:
            if k in seen:
                duplicates.add(k)
            seen.add(k)
        if duplicates:
            raise ValueError(
                f"Duplicate keys where found at initialization:"
                f"Duplicates={seen}")
        self._calculators = calculators

        # Initialize feature history
        self._history: dict[str, list[FeaturePoint]] ={}
        for key in keys:
            self._history[key] = []

    def update(
            self,
            context: StepContext,
            market_view: tuple[MarketDataEvent, ...]
    ) -> FeatureComputedEvent:

        # Check invariants
        if not market_view:
            raise ContextNotInitializedError(f"market_view is empty: market_view={market_view}")

        if context.timestamp != market_view[-1].timestamp:
            raise ValueError(
                f"Timestamp mismatch: "
                f"context={context.timestamp} != market_view={market_view[-1].timestamp}"
            )
        if context.event_id != market_view[-1].event_id:
            raise ValueError(
                f"Event_id mismatch: "
                f"context={context.event_id} != market_view={market_view[-1].event_id}"
            )

        # Iterate over calculators
        computations: dict[str, list[FeaturePoint]] = {}
        for calc in self._calculators:
            result = calc.calculate(market_view=market_view)
            if result is None:
                point = FeaturePoint(
                    calculator_id=calc.calculator_id,
                    timestamp=context.timestamp,
                    value=None
                )
                computations.setdefault(calc.calculator_id, []).append(point)
                continue
            point = FeaturePoint(
                calculator_id = calc.calculator_id,
                timestamp = context.timestamp,
                value = result
            )
            computations.setdefault(calc.calculator_id, []).append(point)
            self._history[calc.calculator_id].append(point)

        return FeatureComputedEvent(
            run_id = context.run_id,
            event_id = context.event_id,
            timestamp = context.timestamp,
            computations= computations,
        )

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

    def window(self, key: str, n: int) -> tuple[FeaturePoint, ...]:
        if not self.contains(key):
            raise KeyError(f"Unknown key: {key}")
        if not self.has_data(key, quantity=n):
            raise ValueError(
                f"Feature '{key}' has not enough published values yet for quantity={n}. "
                f"Has n={len(self._history[key])} values published yet."
            )
        seq = self._history[key]
        return tuple(seq[-n:])