from __future__ import annotations

from typing import ClassVar, Protocol

from investiq.api.portfolio import PositionBookReader
from investiq.execution.transition.enums import AtomicActionType, FIFOSide
from investiq.execution.transition.types import AtomicAction, FIFOOperation, FIFOPosition


class FIFOResolveStrategy(Protocol):
    """
    Static contract for resolving one AtomicAction into FIFOOperations.
    Implementations must be duck-typed (do NOT inherit from this Protocol).
    """
    NAME: ClassVar[str]
    ACTION: ClassVar[AtomicActionType]

    def resolve(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader,
        execution_price: float,
    ) -> list[FIFOOperation]:
        ...