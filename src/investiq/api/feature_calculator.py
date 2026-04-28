from typing import Protocol

from investiq.api.market import MarketDataEvent

class FeatureCalculator(Protocol):
    """
    Feature calculator protocol.
    Preconditions:
        - market_view is non-empty
        - market_view is ordered ascending by timestamp
        - market_view is homogeneous in instrument/bar_size
    """
    @property
    def calculator_id(self) -> str:
        ...
    def calculate(
            self,
            market_view: tuple[MarketDataEvent, ...]
    ) -> float | None:
        ...