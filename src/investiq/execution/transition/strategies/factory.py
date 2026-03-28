from investiq.execution.transition.enums import TransitionType
from investiq.execution.transition.strategies.api import TransitionStrategy
from investiq.execution.transition.strategies.registry import TransitionStrategyRegistry


class TransitionStrategyFactory:
    @staticmethod
    def create(transition_type: TransitionType) -> TransitionStrategy:
        cls_ = TransitionStrategyRegistry.get(transition_type)
        return cls_()