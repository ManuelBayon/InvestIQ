from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.strategy import StrategyMetadata

class MovingAverageCrossStrategy:

    def __init__(
            self,
            fast_window: int = 20,
            slow_window: int = 100
    ):
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError("fast_window and slow_window must be positive")
        if fast_window >= slow_window:
            raise ValueError("fast_window must be < slow_window for a classic MA cross")

        self.metadata = StrategyMetadata(
            name="MovingAverageCross",
            version="1.0.0",
            description="...",
            parameters={
                "fast_window": fast_window,
                "slow_window": slow_window
            },
            required_feature_names=(
                f"sma_{fast_window}",
                f"sma_{slow_window}"
            )
        )
        self._fast_window = fast_window
        self._slow_window = slow_window

    def decide(
            self,
            backtest_view: BacktestView
    ) -> Decision:

        ts = backtest_view.market_view.timestamp
        close = backtest_view.market_view.bar.close
        diagnostics = {}

        if not backtest_view.features_view.has(self.metadata.required_feature_names[0]):
            diagnostics[f"sma_{self._fast_window}"] = "Not available"
            return Decision(
                timestamp=ts,
                target_position=0.0,
                execution_price=close,
                diagnostics=diagnostics
            )
        elif not backtest_view.features_view.has():
            diagnostics[f"sma_{self._slow_window}"] = "Not available"
            return Decision(
                timestamp=ts,
                target_position=0.0,
                execution_price=close,
                diagnostics=diagnostics
            )

        ma_fast = backtest_view.features_view.require(f"sma_{self._fast_window}")
        ma_slow = backtest_view.features_view.require(f"sma_{self._slow_window}")

        if ma_fast > ma_slow:
            target = 1.0
        elif ma_fast < ma_slow:
            target = -1.0
        else:
            target = 0.0

        return Decision(
            timestamp=ts,
            target_position=target,
            execution_price=close,
            diagnostics={
                "ma_fast": ma_fast,
                "ma_slow": ma_slow,
            },
        )