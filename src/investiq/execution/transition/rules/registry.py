from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar, TypeVar

from investiq.execution.transition.rules.api import TransitionKey, TransitionRule

class TransitionRuleRegistry:
    _rules: ClassVar[dict[TransitionKey, type[TransitionRule]]] = {}

    @classmethod
    def register(cls, rule_cls: type[TransitionRule]) -> None:
        key = rule_cls.KEY
        if key in cls._rules:
            raise KeyError(f"Rule already registered for {key}")
        cls._rules[key] = rule_cls

    @classmethod
    def get(cls, key: TransitionKey) -> type[TransitionRule]:
        try:
            return cls._rules[key]
        except KeyError as e:
            available = ", ".join(map(str, cls._rules.keys()))
            raise KeyError(f"Unsupported transition {key}. Available: {available}") from e

    @classmethod
    def clear(cls) -> None:
        cls._rules.clear()

T = TypeVar("T", bound=TransitionRule)
def register_rule() -> Callable[[type[T]], type[T]]:
    def decorator(rule_cls: type[T]) -> type[T]:
        TransitionRuleRegistry.register(rule_cls)
        return rule_cls
    return decorator