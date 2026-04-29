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
    value: float

@dataclass(frozen=True)
class FeatureComputationResult:
    calculator_id: str
    timestamp: datetime
    value: float | None

@dataclass(frozen=True)
class FeatureComputedEvent:
    run_id: str
    event_id: str
    timestamp: datetime
    computations: dict[str, FeatureComputationResult]

class FeatureStore:
    """
    """
    def __init__(
            self,
            calculators: Sequence[FeatureCalculator]
    ) -> None:

        # 1. Check calculator_id unicity
        seen = set()
        duplicates = set()
        for calc in calculators:
            if calc.calculator_id in seen:
                duplicates.add(calc.calculator_id)
            seen.add(calc.calculator_id)
        if duplicates:
            raise ValueError(
                f"Duplicate keys where found at initialization:"
                f"Duplicates={duplicates}")

        # 2. Initializes variables
        self._calculators: tuple[FeatureCalculator, ...] = tuple(calculators)
        self._history: dict[str, list[FeaturePoint]] ={}
        self._last_processed_timestamp: datetime | None = None
        self._last_processed_step_sequence: int = -1
        self._last_processed_event_id: str | None = None

        # 3. Initialize empty list for each calculator
        for calc in self._calculators:
            self._history[calc.calculator_id] = []

    def update(
            self,
            context: StepContext,
            market_view: tuple[MarketDataEvent, ...]
    ) -> FeatureComputedEvent:


        #######################################################################################
        ################                 1. INVARIANTS VALIDATION              ################
        #######################################################################################

        ## 1.1 Market View should not be empty
        if not market_view:
            raise ContextNotInitializedError(f"market_view is empty: market_view={market_view}")

        ## 1.2 Last timestamp in market_view must equal timestamp in step_context
        if context.timestamp != market_view[-1].timestamp:
            raise ValueError(
                f"Timestamp mismatch: "
                f"context={context.timestamp} != market_view={market_view[-1].timestamp}"
            )

        ## 1.3 Context timestamp must be strictly greater than last processed timestamp
        if self._last_processed_timestamp is not None:
            if context.timestamp <= self._last_processed_timestamp:
                raise ValueError(
                    f"StepContext timestamp must be greater than last processed: "
                    f"StepContext.timestamp={context.timestamp}, "
                    f"last_processed={self._last_processed_timestamp}."
                )

        ## 1.4 Context and market_view event_id must be the same
        if context.event_id != market_view[-1].event_id:
            raise ValueError(
                f"Event_id mismatch: "
                f"context={context.event_id} != market_view={market_view[-1].event_id}"
            )

        ## 1.5 Context event_id must be different from last processed event_id
        if self._last_processed_event_id is not None:
            if context.event_id == self._last_processed_event_id:
                raise ValueError(
                    f"StepContext event_id must be different from last processed: "
                    f"StepContext.event_id={context.event_id}, "
                    f"last_processed={self._last_processed_event_id}."
                )

        ## 1.6 Context step sequence must equal expected step sequence
        expected_step_sequence = self._last_processed_step_sequence + 1
        if context.step_sequence != expected_step_sequence:
            raise ValueError(
                f"StepContext step sequence must equal last_processed_step_sequence + 1. "
                f"StepContext.step_sequence={context.step_sequence}, "
                f"last_processed={self._last_processed_step_sequence}."
            )


        #######################################################################################
        ################                      2. PROCESS LOOP                  ################
        ################            Iterates over FeatureCalculators           ################
        #######################################################################################

        computations: dict[str, FeatureComputationResult] = {}
        temporary_history: dict[str, FeaturePoint] ={}

        for calc in self._calculators:
            result = calc.calculate(market_view=market_view)
            computation_result = FeatureComputationResult(
                calculator_id=calc.calculator_id,
                timestamp=context.timestamp,
                value=result,
            )
            if computation_result.value is not None:
                point = FeaturePoint(
                    calculator_id=calc.calculator_id,
                    timestamp=context.timestamp,
                    value=result
                )
                temporary_history[calc.calculator_id] = point
            computations[calc.calculator_id] = computation_result


        #######################################################################################
        ################                 3. ATOMIC STATE MUTATION              ################
        #######################################################################################
        for key, value in temporary_history.items():
            self._history[key].append(value)

        self._last_processed_timestamp = context.timestamp
        self._last_processed_event_id = context.event_id
        self._last_processed_step_sequence = context.step_sequence


        #######################################################################################
        ################            4. RETURNS FEATURE COMPUTED EVENT          ################
        #######################################################################################
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