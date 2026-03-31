from investiq.core.transition_engine.enums import AtomicActionType
from .api import FIFOResolveStrategy
from .registry import FIFOResolveRegistry


class FIFOResolveFactory:
    @staticmethod
    def create(action_type: AtomicActionType) -> FIFOResolveStrategy:
        cls_ = FIFOResolveRegistry.get(action_type)
        return cls_()
