from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from investiq.api.market import MarketField
from investiq.core.features import register_feature_pipeline, FeatureStore
from investiq.core.market_store import MarketStateStore


@dataclass
class _SMAState:
    """
    Incremental Simple Moving Average state.
    Maintains the rolling SMA using O(1) updates once warmup is complete.
    """
    window: int
    value: float | None = None

    def reset(self) -> None:
        """Reset internal SMA state."""
        self.value = None

    def update(self, series: Sequence[float]) -> float | None:
        """
        Update the SMA using the latest series values.

        Returns: float | None
        Current SMA if enough observations are available, otherwise None.
        """
        n = len(series)

        if n < self.window:
            self.value = None
            return None

        if self.value is None or n == self.window:
            self.value = sum(series[-self.window:]) / self.window
            return self.value

        x_t = series[-1]
        x_out = series[-self.window - 1]
        self.value = self.value + (x_t - x_out) / self.window
        return self.value


@register_feature_pipeline
class SMAPipeline:
    """
    Feature pipeline producing fast and slow SMAs from CLOSE prices.

    Output:
        ma_fast, ma_slow – rolling moving averages for the configured windows.
    """
    NAME: ClassVar[str] = "SMA_FAST_SLOW"

    def __init__(
            self,
            fast_window: int = 20,
            slow_window: int = 100
    ):
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError("fast_window and slow_window must be positive")
        if fast_window >= slow_window:
            raise ValueError("fast_window must be < slow_window")

        self._fast = _SMAState(window=fast_window)
        self._slow = _SMAState(window=slow_window)

    def reset(self) -> None:
        """
        Reset internal rolling statistics.
        """
        self._fast.reset()
        self._slow.reset()

    def update(
            self,
            *,
            market_store: MarketStateStore,
            feature_store: FeatureStore
    ) -> None:
        """
        Compute SMAs for the current tick and write features to the FeatureStore.
        Marks the pipeline ready when both averages are available.
        """
        market_view = market_store.view()
        close_seq = market_view.history.window(MarketField.CLOSE, self._slow.window)

        if close_seq is None:
            return

        closes = list(close_seq)

        ma_fast = self._fast.update(closes)
        ma_slow = self._slow.update(closes)

        if ma_fast is None or ma_slow is None:
            return

        feature_store.set_value("ma_fast", ma_fast)
        feature_store.set_value("ma_slow", ma_slow)
        feature_store.set_pipeline_ready(self.NAME)