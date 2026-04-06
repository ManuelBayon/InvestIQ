from __future__ import annotations

from investiq.api.portfolio import PositionBookReader
from investiq.core.transition_engine.types import AtomicAction, FIFOOperation
from investiq.core.transition_engine.fifo.factory import FIFOResolveFactory


class FIFOResolver:
    """
    Orchestrator: AtomicAction -> FIFOOperation(s).
    Delegates per-action resolution to registered FIFO resolve transitions.
    """

    def __init__(self) -> None:
        self._factory = FIFOResolveFactory()

    def resolve_action(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader,
        execution_price: float,
    ) -> list[FIFOOperation]:
        strategy = self._factory.create(action_type=action.type)
        return strategy.resolve(
            action=action,
            position_book=position_book,
            execution_price=execution_price
        )

    def resolve(
        self,
        *,
        actions: list[AtomicAction],
        position_book: PositionBookReader,
        execution_price: float,
    ) -> list[FIFOOperation]:
        ops: list[FIFOOperation] = []
        for a in actions:
            ops.extend(
                self.resolve_action(
                    action=a,
                    position_book=position_book,
                    execution_price=execution_price
                )
            )
        return ops
