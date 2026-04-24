from collections.abc import Sequence
from typing import FrozenSet

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.filter import Filter
from investiq.api.strategy import Strategy


class DecisionPipeline:

    def __init__(
            self,
            strategy: Strategy,
            filters: Sequence[Filter] | None = None,
    ):
        self._strategy = strategy
        self._filters = list(filters) if filters else []

    def run(self, bt_view: BacktestView) -> Decision:

        # 1. Execute strategy with current context
        decision = self._strategy.decide(
            backtest_view=bt_view
        )

        # 2. Execute sequentially each filter by passing them the last decision
        for f in self._filters:
            decision = f.apply(
                view=bt_view,
                decision=decision
            )

        # 3. Return the decision after filters
        return Decision(
            timestamp=decision.timestamp,
            target_position=decision.target_position,
            execution_price=decision.execution_price,
        )