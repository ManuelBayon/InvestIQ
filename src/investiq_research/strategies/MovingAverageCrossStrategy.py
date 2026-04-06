from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.strategy import StrategyMetadata

class MovingAverageCrossStrategy:

    def __init__(
            self,
            fast_window: int = 20,
            slow_window: int = 100
    ):
        if fast_window <= 0 :
            raise ValueError(
                f"fast_window must be positive, got n={fast_window}"
            )
        if slow_window <= 0:
            raise ValueError(
                f"slow window must be positive, got n={slow_window}"
            )
        if not fast_window < slow_window:
            raise ValueError(
                f"fast_window must be < slow_window, got"
                f" fast={fast_window}, "
                f" slow={slow_window}."
            )

        self._fast_sma_key = f"sma_{fast_window}"
        self._slow_sma_key = f"sma_{slow_window}"

        self.metadata = StrategyMetadata(
            name="MovingAverageCross",
            version="1.0.0",
            description="...",
            parameters={
                "fast_window": fast_window,
                "slow_window": slow_window
            },
            required_feature_names=(
                self._fast_sma_key,
                self._slow_sma_key
            )
        )

    def decide(
            self,
            backtest_view: BacktestView
    ) -> Decision:

        # 1. Initialization
        ts = backtest_view.market_view.timestamp
        close = backtest_view.market_view.bar.close
        features_view = backtest_view.features_view
        diagnostics: dict[str, object] = {}

        # 2. Warmup
        if not features_view.is_ready(self._fast_sma_key):
            diagnostics[self._fast_sma_key] = "Not available"
            return Decision(
                timestamp=ts,
                target_position=0.0,
                execution_price=close,
                diagnostics=diagnostics
            )
        if not features_view.is_ready(self._slow_sma_key):
            diagnostics[self._slow_sma_key] = "Not available"
            return Decision(
                timestamp=ts,
                target_position=0.0,
                execution_price=close,
                diagnostics=diagnostics
            )

        # 3. Get features
        ma_fast = features_view.require(self._fast_sma_key)
        ma_slow = features_view.require(self._slow_sma_key)

        # 4. Compute target position
        if ma_fast > ma_slow:
            target = 1.0
        elif ma_fast < ma_slow:
            target = -1.0
        else:
            target = 0.0

        # 5. Return Decision
        return Decision(
            timestamp=ts,
            target_position=target,
            execution_price=close,
            diagnostics={
                "ma_fast": ma_fast,
                "ma_slow": ma_slow,
            },
        )