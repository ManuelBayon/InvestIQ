from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, Optional

import pandas as pd

from investiq.api.instruments import Instrument
from investiq.core.transition_engine.enums import FIFOSide, ExecutionSide
from investiq.core.transition_engine.types import FIFOPosition

class PositionBookReader(Protocol):
    def active(self, side: FIFOSide) -> tuple[FIFOPosition, ...]: ...
    def all(self, side: FIFOSide) -> tuple[FIFOPosition, ...]: ...
    def count_active(self, side: FIFOSide) -> float: ...

@dataclass(frozen=True)
class Fill:

    timestamp: pd.Timestamp
    position_side : FIFOSide
    execution_side : ExecutionSide

    quantity : float
    execution_price : float

    position_before : float
    position_after: float
    cash_before: float
    cash_after: float

    entry_price: Optional[float]
    exit_price: Optional[float]
    realized_pnl: Optional[float]

    operation_id: int
    linked_position_id: Optional[int]

    instrument_id: Optional[str] = None

@dataclass
class PortfolioView:
    instrument: Instrument
    current_position: float
    initial_cash: float
    cash: float
    realized_pnl: float
    fifo_book: PositionBookReader
    fill_log: Sequence[Fill]