from typing import Final

from investiq.api.enums import TransitionType
from investiq.api.execution import Decision
from investiq.api.portfolio import PortfolioView
from investiq.api.types import AtomicAction
from investiq.core.transition_strategies import STRATEGY_BY_TRANSITION

EPS: Final[float] = 1e-12
def _is_zero(value: float) -> bool:
    return abs(value) < EPS

def classify_transition(
        current_position: float,
        target_position: float
) -> TransitionType:
    """
    For each couple (current_position, target_position) valid,
    returns exactly one TransitionType

    Args:
        current_position:
        target_position:

    Returns:
        TransitionType.
    """
    # Current = Target
    if _is_zero(current_position - target_position):
        return TransitionType.NO_OP

    # Current == 0
    elif _is_zero(current_position):
        if target_position > 0:
            return TransitionType.OPEN_LONG
        else:
            return TransitionType.OPEN_SHORT

    # Current > 0
    elif current_position > 0.0:
        if _is_zero(target_position):
            return TransitionType.CLOSE_LONG
        elif 0.0 < current_position < target_position:
            return TransitionType.INCREASE_LONG
        elif 0.0 < target_position < current_position:
            return TransitionType.REDUCE_LONG
        else:
            return TransitionType.REVERSAL_TO_SHORT

    # Curent < 0
    elif current_position < 0.0:
        if _is_zero(target_position):
            return TransitionType.CLOSE_SHORT
        elif current_position < target_position < 0.0:
            return TransitionType.REDUCE_SHORT
        elif target_position < current_position < 0.0:
            return TransitionType.INCREASE_SHORT
        else:
            return TransitionType.REVERSAL_TO_LONG

    else:
        raise AssertionError(
            "Unhandled transition classification: "
            f"current_position={current_position}, "
            f"target_position={target_position}"
        )

def resolve_transition(
        decision: Decision,
        portfolio_view: PortfolioView,
) -> tuple[AtomicAction, ...]:

    transition_type = classify_transition(
        current_position=portfolio_view.current_position,
        target_position=decision.target_position,
    )

    atomic_actions = STRATEGY_BY_TRANSITION[transition_type]().resolve(
        timestamp=decision.timestamp,
        current_position=portfolio_view.current_position,
        target_position=decision.target_position,
    )
    return tuple(atomic_actions)