from datetime import datetime
from typing import Protocol, runtime_checkable, ClassVar

from investiq.core.transition_engine.types import AtomicAction


@runtime_checkable
class TransitionStrategy(Protocol):
    NAME: ClassVar[str]
    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        ...