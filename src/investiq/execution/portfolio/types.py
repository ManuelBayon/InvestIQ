from dataclasses import dataclass
from typing import Optional

import pandas as pd

from investiq.execution.transition.enums import FIFOOperationType, FIFOSide, ExecutionSide


@dataclass(frozen=True)
class PortfolioSignal:
    timestamp: pd.Timestamp
    price: float
    target_position: float

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