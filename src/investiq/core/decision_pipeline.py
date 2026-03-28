from collections.abc import Sequence
from typing import FrozenSet

from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.filter import Filter
from investiq.api.strategy import Strategy


class DecisionPipeline:

    def __init__(
            self,
            available_feature_pipelines: FrozenSet[str],
            strategy: Strategy,
            filters: Sequence[Filter] | None = None,
    ):
        # 1. Configuration validation
        required = strategy.metadata.required_pipelines
        missing = required - available_feature_pipelines
        if missing:
            raise ValueError(
                f"Strategy '{strategy.metadata.name}' requires unknown pipelines: {sorted(missing)}."
                f"Available pipelines: {sorted(available_feature_pipelines)}"
            )
        self._strategy = strategy
        self._filters = list(filters) if filters else []

    def run(self, *, view: BacktestView) -> Decision:

        d0 = self._strategy.decide(view=view)

        diagnostics = {
            "strategy": {self._strategy.metadata.name: d0.diagnostics},
            "filters": []
        }

        d = d0
        for f in self._filters:
            d = f.apply(view=view, decision=d)
            diagnostics["filters"].append({f.metadata.name: d.diagnostics})

        return Decision(
            timestamp=d.timestamp,
            target_position=d.target_position,
            execution_price=d.execution_price,
            diagnostics=diagnostics,
        )