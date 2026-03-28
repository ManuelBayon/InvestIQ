from __future__ import annotations

from typing import Callable, TypeVar, cast

from investiq.execution.transition.enums import AtomicActionType
from .api import FIFOResolveStrategy

S = TypeVar("S", bound=type)  # classe concrète (OpenLongFIFO, CloseLongFIFO, ...)


class FIFOResolveRegistry:
    _registry: dict[AtomicActionType, type] = {}  # <- important: pas type[FIFOResolveStrategy]

    @classmethod
    def register(cls, key: AtomicActionType, strategy_cls: type) -> None:
        if key in cls._registry:
            raise KeyError(f"{key} already registered")

        if not hasattr(strategy_cls, "NAME"):
            raise TypeError(f"{strategy_cls.__name__} missing NAME: ClassVar[str]")
        if not callable(getattr(strategy_cls, "resolve", None)):
            raise TypeError(f"{strategy_cls.__name__} missing resolve(...)")

        cls._registry[key] = strategy_cls

    @classmethod
    def get(cls, key: AtomicActionType) -> type[FIFOResolveStrategy]:
        try:
            return cast(type[FIFOResolveStrategy], cls._registry[key])
        except KeyError:
            raise KeyError(f"{key} not registered; available={list(cls._registry.keys())}")


def register_fifo_resolve_strategy(key: AtomicActionType) -> Callable[[type[S]], type[S]]:
    def decorator(cls_: type[S]) -> type[S]:
        FIFOResolveRegistry.register(key, cls_)
        return cls_
    return decorator
