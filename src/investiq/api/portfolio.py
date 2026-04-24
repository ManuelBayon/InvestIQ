from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, Optional, ClassVar

import pandas as pd

from investiq.api.enums import FIFOSide, ExecutionSide
from investiq.api.instruments import Instrument
from investiq.api.types import FIFOPosition, FIFOOperation



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


class PortfolioView:
    instrument: Instrument
    current_position: float
    initial_cash: float
    cash: float
    realized_pnl: float
    #fifo_book: PositionBookReader
    fill_log: Sequence[Fill]

class PortfolioProtocol(Protocol):
    instrument: Instrument
    current_position: float
    cash: float
    realized_pnl: float
    unrealized_pnl: float
    fifo_queues: dict[FIFOSide, list[FIFOPosition]]


class PortfolioExecutionStrategy(Protocol):
    NAME: ClassVar[str]
    def apply(
        self,
        portfolio: PortfolioProtocol,
        operation: FIFOOperation,
    ) -> Fill:
        ...