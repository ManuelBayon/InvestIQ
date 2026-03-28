from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.filter import Filter, FilterMetadata


class StopLoss(Filter):
    metadata: FilterMetadata
    def apply(
            self,
            view: BacktestView,
            plan: Decision
    ) -> Decision:
        """
        To complete...
        """
        ...