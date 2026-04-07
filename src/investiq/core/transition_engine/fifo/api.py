from typing import ClassVar, Protocol

from investiq.api.portfolio import PositionBookReader
from investiq.core.transition_engine.enums import AtomicActionType
from investiq.core.transition_engine.types import AtomicAction, FIFOOperation


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