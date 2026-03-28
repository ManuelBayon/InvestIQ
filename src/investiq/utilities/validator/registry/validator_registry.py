from typing import Callable

from engine.utilities.validator.protocol import ValidatorProtocol


class ValidatorRegistry:

    _registry: dict[str, Callable[..., ValidatorProtocol[object]]]

    @classmethod
    def register(
            cls,
            name: str
    ) -> None:
        ...