from typing import Callable, TypeVar
from investiq.execution.transition.enums import TransitionType
from investiq.execution.transition.strategies.api import TransitionStrategy

T = TypeVar("T", bound=TransitionStrategy)

class TransitionStrategyRegistry:

    _registry: dict[TransitionType, type[TransitionStrategy]] = {}

    @classmethod
    def register(cls, key: TransitionType, strategy_cls: type[TransitionStrategy]) -> None:
        if key in cls._registry:
            raise KeyError(f"{key} already registered")

        if not hasattr(strategy_cls, "NAME"):
            raise TypeError(f"{strategy_cls.__name__} missing NAME: ClassVar[str]")

        if not callable(getattr(strategy_cls, "resolve", None)):
            raise TypeError(f"{strategy_cls.__name__} missing resolve(...)")

        cls._registry[key] = strategy_cls

    @classmethod
    def get(cls, key: TransitionType) -> type[TransitionStrategy]:
        try:
            return cls._registry[key]
        except KeyError:
            raise KeyError(f"{key} not registered; available={list(cls._registry.keys())}")

    @classmethod
    def available(cls) -> list[TransitionType]:
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        return cls._registry.clear()

def register_transition_strategy(key: TransitionType) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        TransitionStrategyRegistry.register(key, cls)
        return cls
    return decorator