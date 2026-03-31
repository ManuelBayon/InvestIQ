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

    def run(
            self,
            *,
            view: BacktestView
    ) -> Decision:

        d = self._strategy.decide(backtest_view=view)

        diagnostics = {
            "strategy": {self._strategy.metadata.name: d.diagnostics},
            "filters": []
        }

        for f in self._filters:
            d = f.apply(view=view, decision=d)
            diagnostics["filters"].append({f.metadata.name: d.diagnostics})

        return Decision(
            timestamp=d.timestamp,
            target_position=d.target_position,
            execution_price=d.execution_price,
            diagnostics=diagnostics,
        )