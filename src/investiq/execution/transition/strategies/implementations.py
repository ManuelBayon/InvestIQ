"""
investiq/execution/transition/strategies/builtins.py

Concrete built-in transition strategies (single-file).
Goal: onboarding-friendly, desk-grade invariants, minimal moving parts.

Contract:
- Each strategy exposes NAME: ClassVar[str]
- resolve(...) is keyword-only to avoid call-site ambiguity
- resolve returns a list[AtomicAction] representing the atomic execution plan

Registration:
- Each strategy is registered via @register_transition_strategy(TransitionType.*)
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Final

from investiq.execution.transition.enums import AtomicActionType, TransitionType
from investiq.execution.transition.strategies.api import TransitionStrategy
from investiq.execution.transition.types import AtomicAction
from investiq.execution.transition.strategies.registry import register_transition_strategy


# -----------------------------
# Internal helpers (small, explicit)
# -----------------------------

_EPS: Final[float] = 0.0  # keep exact comparisons; change to e.g. 1e-12 if you later use floats from numerics


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _close_long(*, qty: float, ts: datetime) -> AtomicAction:
    return AtomicAction(type=AtomicActionType.CLOSE_LONG, quantity=qty, timestamp=ts)


def _open_long(*, qty: float, ts: datetime) -> AtomicAction:
    return AtomicAction(type=AtomicActionType.OPEN_LONG, quantity=qty, timestamp=ts)


def _close_short(*, qty: float, ts: datetime) -> AtomicAction:
    return AtomicAction(type=AtomicActionType.CLOSE_SHORT, quantity=qty, timestamp=ts)


def _open_short(*, qty: float, ts: datetime) -> AtomicAction:
    return AtomicAction(type=AtomicActionType.OPEN_SHORT, quantity=qty, timestamp=ts)


# -----------------------------
# Concrete strategies (registered)
# -----------------------------

@register_transition_strategy(TransitionType.NO_OP)
class NoOpStrategy:
    """
    No operation: current_position already equals target_position.
    """
    NAME: ClassVar[str] = "NoOp"
    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position == target_position,
            f"[{self.NAME}] expected current_position == target_position, got current={current_position}, target={target_position}",
        )
        return []


@register_transition_strategy(TransitionType.OPEN_LONG)
class OpenLongStrategy:
    """
    Open a new long position from flat.
    """
    NAME: ClassVar[str] = "OpenLong"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position == 0.0,
            f"[{self.NAME}] expected current_position == 0, got {current_position}",
        )
        _require(
            target_position > _EPS,
            f"[{self.NAME}] expected target_position > 0, got {target_position}",
        )
        return [_open_long(qty=target_position, ts=timestamp)]


@register_transition_strategy(TransitionType.OPEN_SHORT)
class OpenShortStrategy:
    """
    Open a new short position from flat.
    """
    NAME: ClassVar[str] = "OpenShort"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position == 0.0,
            f"[{self.NAME}] expected current_position == 0, got {current_position}",
        )
        _require(
            target_position < -_EPS,
            f"[{self.NAME}] expected target_position < 0, got {target_position}",
        )
        return [_open_short(qty=abs(target_position), ts=timestamp)]


@register_transition_strategy(TransitionType.CLOSE_LONG)
class CloseLongStrategy:
    """
    Fully close an existing long position to flat.
    """
    NAME: ClassVar[str] = "CloseLong"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position > _EPS,
            f"[{self.NAME}] expected current_position > 0, got {current_position}",
        )
        _require(
            target_position == 0.0,
            f"[{self.NAME}] expected target_position == 0, got {target_position}",
        )
        return [_close_long(qty=current_position, ts=timestamp)]


@register_transition_strategy(TransitionType.CLOSE_SHORT)
class CloseShortStrategy:
    """
    Fully close an existing short position to flat.
    """
    NAME: ClassVar[str] = "CloseShort"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position < -_EPS,
            f"[{self.NAME}] expected current_position < 0, got {current_position}",
        )
        _require(
            target_position == 0.0,
            f"[{self.NAME}] expected target_position == 0, got {target_position}",
        )
        return [_close_short(qty=abs(current_position), ts=timestamp)]


@register_transition_strategy(TransitionType.INCREASE_LONG)
class IncreaseLongStrategy:
    """
    Increase an existing long position (stay long).
    """
    NAME: ClassVar[str] = "IncreaseLong"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position > _EPS,
            f"[{self.NAME}] expected current_position > 0, got {current_position}",
        )
        _require(
            target_position > current_position,
            f"[{self.NAME}] expected target_position > current_position, got target={target_position}, current={current_position}",
        )
        delta = target_position - current_position
        return [_open_long(qty=delta, ts=timestamp)]


@register_transition_strategy(TransitionType.INCREASE_SHORT)
class IncreaseShortStrategy:
    """
    Increase an existing short position (become more negative).
    """
    NAME: ClassVar[str] = "IncreaseShort"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position < -_EPS,
            f"[{self.NAME}] expected current_position < 0, got {current_position}",
        )
        _require(
            target_position < current_position,
            f"[{self.NAME}] expected target_position < current_position (more negative), got target={target_position}, current={current_position}",
        )
        delta = abs(target_position - current_position)
        return [_open_short(qty=delta, ts=timestamp)]


@register_transition_strategy(TransitionType.REDUCE_LONG)
class ReduceLongStrategy:
    """
    Reduce an existing long without closing (stay long).
    """
    NAME: ClassVar[str] = "ReduceLong"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position > _EPS,
            f"[{self.NAME}] expected current_position > 0, got {current_position}",
        )
        _require(
            target_position > _EPS,
            f"[{self.NAME}] expected target_position > 0, got {target_position}",
        )
        _require(
            current_position > target_position,
            f"[{self.NAME}] expected current_position > target_position, got current={current_position}, target={target_position}",
        )
        delta = current_position - target_position
        return [_close_long(qty=delta, ts=timestamp)]


@register_transition_strategy(TransitionType.REDUCE_SHORT)
class ReduceShortStrategy:
    """
    Reduce an existing short without closing (stay short, closer to zero).
    """
    NAME: ClassVar[str] = "ReduceShort"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position < -_EPS,
            f"[{self.NAME}] expected current_position < 0, got {current_position}",
        )
        _require(
            target_position < -_EPS,
            f"[{self.NAME}] expected target_position < 0, got {target_position}",
        )
        _require(
            target_position > current_position,
            f"[{self.NAME}] expected target_position > current_position (less negative), got target={target_position}, current={current_position}",
        )
        delta = abs(current_position - target_position)
        return [_close_short(qty=delta, ts=timestamp)]


@register_transition_strategy(TransitionType.REVERSAL_TO_LONG)
class ReversalToLongStrategy:
    """
    Reverse from short to long:
      1) close short (abs(current_position))
      2) open long (target_position)
    """
    NAME: ClassVar[str] = "ReversalToLong"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position < -_EPS,
            f"[{self.NAME}] expected current_position < 0, got {current_position}",
        )
        _require(
            target_position > _EPS,
            f"[{self.NAME}] expected target_position > 0, got {target_position}",
        )
        return [
            _close_short(qty=abs(current_position), ts=timestamp),
            _open_long(qty=target_position, ts=timestamp),
        ]


@register_transition_strategy(TransitionType.REVERSAL_TO_SHORT)
class ReversalToShortStrategy:
    """
    Reverse from long to short:
      1) close long (current_position)
      2) open short (abs(target_position))
    """
    NAME: ClassVar[str] = "ReversalToShort"

    def resolve(
        self,
        *,
        timestamp: datetime,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        _require(
            current_position > _EPS,
            f"[{self.NAME}] expected current_position > 0, got {current_position}",
        )
        _require(
            target_position < -_EPS,
            f"[{self.NAME}] expected target_position < 0, got {target_position}",
        )
        return [
            _close_long(qty=current_position, ts=timestamp),
            _open_short(qty=abs(target_position), ts=timestamp),
        ]