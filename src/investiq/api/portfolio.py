from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from investiq.api.instruments import Instrument
from investiq.execution.transition.types import FIFOPosition
from investiq.execution.transition.enums import FIFOSide
from investiq.execution.portfolio.types import Fill

class PositionBookReader(Protocol):
    def active(self, side: FIFOSide) -> tuple[FIFOPosition, ...]: ...
    def all(self, side: FIFOSide) -> tuple[FIFOPosition, ...]: ...
    def count_active(self, side: FIFOSide) -> float: ...

@dataclass
class PortfolioView:
    instrument: Instrument
    current_position: float
    initial_cash: float
    cash: float
    realized_pnl: float
    fifo_book: PositionBookReader
    fill_log: Sequence[Fill]