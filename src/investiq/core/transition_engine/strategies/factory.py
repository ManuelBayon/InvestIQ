from investiq.core.transition_engine.enums import TransitionType
from investiq.core.transition_engine.strategies.api import TransitionStrategy
from investiq.core.transition_engine.strategies.registry import TransitionStrategyRegistry


class TransitionStrategyFactory:
    @staticmethod
    def create(transition_type: TransitionType) -> TransitionStrategy:
        cls_ = TransitionStrategyRegistry.get(transition_type)
        return cls_()