from investiq.api.backtest import BacktestView
from investiq.api.execution import Decision
from investiq.api.market import MarketField
from investiq.api.strategy import StrategyMetadata
from investiq_research.features.SMA import SMAPipeline


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
            parameters={"fast_window": fast_window, "slow_window": slow_window},
            price_type=MarketField.CLOSE,
            required_fields=frozenset({MarketField.CLOSE}),
            required_pipelines=frozenset({SMAPipeline.NAME}),
            required_features=frozenset({"ma_fast", "ma_slow"}),
        )

    def decide(self, view: BacktestView) -> Decision:

        ts = view.market_view.timestamp
        close = view.market_view.bar.close
        fv = view.features_view

        pipeline = SMAPipeline.NAME

        # Gate on pipeline readiness (this tick)
        if not fv.pipeline_is_ready(pipeline):
            return Decision(
                timestamp=ts,
                target_position=0.0,
                execution_price=close,
                diagnostics={
                    "warming_up": True,
                    "pipeline": pipeline,
                },
            )

        ma_fast = fv.require("ma_fast")
        ma_slow = fv.require("ma_slow")

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