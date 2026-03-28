from investiq.execution.transition.enums import AtomicActionType
from .api import FIFOResolveStrategy
from .registry import FIFOResolveRegistry


class FIFOResolveFactory:
    @staticmethod
    def create(action_type: AtomicActionType) -> FIFOResolveStrategy:
        cls_ = FIFOResolveRegistry.get(action_type)
        return cls_()
