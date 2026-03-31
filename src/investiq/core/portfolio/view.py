from investiq.api.portfolio import PositionBookReader
from investiq.core.transition_engine.enums import FIFOSide
from investiq.core.transition_engine.types import FIFOPosition


class InMemoryPositionBookView(PositionBookReader):
    """
    Read-only façade over internal FIFO queues.
    """

    def __init__(self, fifo_queues: dict[FIFOSide, list[FIFOPosition]]):
        self._fifo_queues = fifo_queues

    def active(self, side: FIFOSide) -> tuple[FIFOPosition, ...]:
        return tuple(
            p for p in self._fifo_queues.get(side, []) if p.is_active
        )

    def all(self, side: FIFOSide) -> tuple[FIFOPosition, ...]:
        return tuple(
            p for p in self._fifo_queues.get(side, [])
        )

    def count_active(self, side: FIFOSide) -> float:
        return sum(
            p.quantity for p in self._fifo_queues.get(side, []) if p.is_active
        )