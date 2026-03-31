from __future__ import annotations

from typing import ClassVar, Final

from investiq.api.portfolio import PositionBookReader
from investiq.core.transition_engine.enums import (
    AtomicActionType,
    FIFOSide,
    FIFOOperationType,
)
from investiq.core.transition_engine.types import AtomicAction, FIFOOperation
from .registry import register_fifo_resolve_strategy


_EPS: Final[float] = 0.0

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)

def _require_price(price: float, name: str) -> None:
    _require(price > 0.0, f"[{name}] execution_price must be > 0, got {price}")

def _require_qty(qty: float, name: str) -> None:
    _require(qty > _EPS, f"[{name}] quantity must be > 0, got {qty}")


@register_fifo_resolve_strategy(AtomicActionType.OPEN_LONG)
class OpenLongFIFO:
    NAME: ClassVar[str] = "OpenLongFIFO"
    ACTION: ClassVar[AtomicActionType] = AtomicActionType.OPEN_LONG

    def resolve(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader, # Not used for opening a new position.
        execution_price: float,
    ) -> list[FIFOOperation]:
        _require(action.type == self.ACTION, f"[{self.NAME}] unexpected action.type={action.type}")
        _require_price(execution_price, self.NAME)
        _require_qty(action.quantity, self.NAME)

        return [
            FIFOOperation(
                id=FIFOOperation.next_id(),
                timestamp=action.timestamp,
                type=FIFOOperationType.OPEN,
                side=FIFOSide.LONG,
                quantity=action.quantity,
                execution_price=execution_price,
                linked_position_id=None,
            )
        ]


@register_fifo_resolve_strategy(AtomicActionType.OPEN_SHORT)
class OpenShortFIFO:
    NAME: ClassVar[str] = "OpenShortFIFO"
    ACTION: ClassVar[AtomicActionType] = AtomicActionType.OPEN_SHORT

    def resolve(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader, # Not used for opening a new position.
        execution_price: float,
    ) -> list[FIFOOperation]:
        _require(action.type == self.ACTION, f"[{self.NAME}] unexpected action.type={action.type}")
        _require_price(execution_price, self.NAME)
        _require_qty(action.quantity, self.NAME)

        return [
            FIFOOperation(
                id=FIFOOperation.next_id(),
                timestamp=action.timestamp,
                type=FIFOOperationType.OPEN,
                side=FIFOSide.SHORT,
                quantity=action.quantity,
                execution_price=execution_price,
                linked_position_id=None,
            )
        ]

def _close_from_fifo(
    *,
    name: str,
    side: FIFOSide,
    action: AtomicAction,
    position_book: PositionBookReader,
    execution_price: float,
) -> list[FIFOOperation]:
    _require_price(execution_price, name)
    _require_qty(action.quantity, name)

    fifo = position_book.active(side=side)
    remaining = action.quantity
    ops: list[FIFOOperation] = []

    for pos in fifo:
        if not pos.is_active:
            continue
        if pos.quantity <= 0:
            continue

        close_qty = min(remaining, pos.quantity)
        ops.append(
            FIFOOperation(
                id=FIFOOperation.next_id(),
                timestamp=action.timestamp,
                type=FIFOOperationType.CLOSE,
                side=side,
                quantity=close_qty,
                execution_price=execution_price,
                linked_position_id=pos.id,
            )
        )
        remaining -= close_qty
        if remaining <= 0:
            break

    _require(remaining <= 0, f"[{name}] insufficient FIFO capacity: missing={remaining}")
    return ops


@register_fifo_resolve_strategy(AtomicActionType.CLOSE_LONG)
class CloseLongFIFO:
    NAME: ClassVar[str] = "CloseLongFIFO"
    ACTION: ClassVar[AtomicActionType] = AtomicActionType.CLOSE_LONG

    def resolve(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader,
        execution_price: float,
    ) -> list[FIFOOperation]:
        _require(action.type == self.ACTION, f"[{self.NAME}] unexpected action.type={action.type}")
        return _close_from_fifo(
            name=self.NAME,
            side=FIFOSide.LONG,
            action=action,
            position_book=position_book,
            execution_price=execution_price,
        )


@register_fifo_resolve_strategy(AtomicActionType.CLOSE_SHORT)
class CloseShortFIFO:
    NAME: ClassVar[str] = "CloseShortFIFO"
    ACTION: ClassVar[AtomicActionType] = AtomicActionType.CLOSE_SHORT

    def resolve(
        self,
        *,
        action: AtomicAction,
        position_book: PositionBookReader,
        execution_price: float,
    ) -> list[FIFOOperation]:
        _require(action.type == self.ACTION, f"[{self.NAME}] unexpected action.type={action.type}")
        return _close_from_fifo(
            name=self.NAME,
            side=FIFOSide.SHORT,
            action=action,
            position_book=position_book,
            execution_price=execution_price,
        )