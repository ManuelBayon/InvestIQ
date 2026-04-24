import pandas as pd

from dataclasses import dataclass

from investiq.api.enums import CurrentState, Event, FIFOOperationType, FIFOSide, AtomicActionType


@dataclass(frozen=True)
class TransitionLog:
    state: CurrentState
    event: Event
    current_position: float
    target_position: float
    rule_name: str
    transition_strategy: str
    transition_type: str
    actions_len: int
    fifo_ops_len: int


@dataclass(frozen=True)
class AtomicAction:
    type : AtomicActionType
    quantity : float
    timestamp: pd.Timestamp

@dataclass
class FIFOPosition:
    id : int
    is_active : bool
    timestamp : pd.Timestamp
    type : FIFOOperationType
    side : FIFOSide
    quantity : float
    price : float

    _next_id = 0

    @classmethod
    def next_id(cls) -> int:
        id_ = cls._next_id
        cls._next_id += 1
        return id_

@dataclass
class FIFOOperation:
    id : int
    timestamp : pd.Timestamp
    type : FIFOOperationType
    side : FIFOSide
    execution_price : float
    quantity : float
    linked_position_id: int | None = None
    _next_id = 0
    @classmethod
    def next_id(cls) -> int:
        id_ = cls._next_id
        cls._next_id += 1
        return id_

@dataclass(frozen=True)
class ResolveContext:
    """
    Unchanging context passed to SafeGuards transitions.
    Combines action, fifo status, and execution price for deterministic checks
    with no side effects.
    """
    action: AtomicAction
    fifo_queues: dict[FIFOSide, list[FIFOPosition]]
    execution_price: float