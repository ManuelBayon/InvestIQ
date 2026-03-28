from __future__ import annotations

from investiq.execution.transition.enums import FIFOOperationType
from .api import PortfolioExecutionStrategy
from .registry import PortfolioExecutionRegistry


class PortfolioExecutionFactory:
    @staticmethod
    def create(op_type: FIFOOperationType) -> PortfolioExecutionStrategy:
        cls_ = PortfolioExecutionRegistry.get(op_type)
        return cls_()