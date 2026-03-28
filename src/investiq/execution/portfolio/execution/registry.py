from __future__ import annotations

from typing import Callable, TypeVar, cast

from investiq.execution.transition.enums import FIFOOperationType
from .api import PortfolioExecutionStrategy

S = TypeVar("S", bound=type)


class PortfolioExecutionRegistry:

    _registry: dict[FIFOOperationType, type] = {}

    @classmethod
    def register(cls, key: FIFOOperationType, strategy_cls: type) -> None:
        if key in cls._registry:
            raise KeyError(f"{key} already registered")

        if not hasattr(strategy_cls, "NAME"):
            raise TypeError(f"{strategy_cls.__name__} missing NAME: ClassVar[str]")
        if not callable(getattr(strategy_cls, "apply", None)):
            raise TypeError(f"{strategy_cls.__name__} missing apply(...)")

        cls._registry[key] = strategy_cls

    @classmethod
    def get(cls, key: FIFOOperationType) -> type[PortfolioExecutionStrategy]:
        try:
            return cast(type[PortfolioExecutionStrategy], cls._registry[key])
        except KeyError:
            raise KeyError(f"{key} not registered; available={list(cls._registry.keys())}")

    @classmethod
    def available(cls) -> list[FIFOOperationType]:
        return list(cls._registry.keys())


def register_execution_strategy(key: FIFOOperationType) -> Callable[[type[S]], type[S]]:
    def decorator(cls_: type[S]) -> type[S]:
        PortfolioExecutionRegistry.register(key, cls_)
        return cls_
    return decorator
