from investiq.api.market import MarketView
from investiq.core.features_store import FeatureCalculator

class SMA(FeatureCalculator):
    """
    Simple Moving Average Feature.
    Returns None during warm up.
    Returns the value when there is enough data available.
    """
    def __init__(self, window: int):
        if window <= 0:
            raise ValueError("SMA window must be greater than zero.")
        self._window = window

    @property
    def calculator_id(self) -> str:
        return f"SMA(window={self._window})"

    @property
    def key(self) -> str:
        return f"sma_{self._window}"

    def calculate(self, market_view: MarketView) -> float | None:
        close_seq = [event.bar.close for event in market_view.reader.series()]
        if len(close_seq) < self._window:
            return None
        sma = sum(close_seq[-self._window:]) / self._window
        return sma