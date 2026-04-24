from investiq.api.feature_calculator import FeatureCalculator
from investiq.api.market import MarketDataEvent

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

    def calculate(
            self,
            market_view: tuple[MarketDataEvent, ...]
    ) -> float | None:

        close_seq = []
        for event in market_view:
            close_seq.append(event.bar.close)

        if len(close_seq) < self._window:
            return None
        sma = sum(close_seq[-self._window:]) / self._window
        return float(sma)