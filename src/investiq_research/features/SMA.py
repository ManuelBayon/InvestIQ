from investiq.api.market import MarketView
from investiq.core.features_store import FeatureCalculator

class SMA(FeatureCalculator):

    def __init__(self, window: int):
        self._window = window

    @property
    def key(self) -> str:
        return f"sma_{self._window}"

    def calculate(self, market_view: MarketView) -> float | None:

        # 1. Initialization
        close_seq = [event.bar.close for event in market_view.history.series()]

        # 2. Check pre-conditions
        if self._window <= 0: raise ValueError("SMA window must be greater than zero.")
        if len(close_seq) < self._window:
            return None

        # 3. Calculate and return feature
        sma = sum(close_seq[-self._window:]) / self._window
        return sma