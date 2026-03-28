from abc import ABC, abstractmethod

from investiq.utilities.validator.base import BaseValidator
from investiq.utilities.validator.protocol import ValidatorProtocol


class ValidatorStrategy[T](ValidatorProtocol[T], BaseValidator, ABC):
    """
    Base strategy enforcing validator naming and callable contract.
    """
    def __init_subclass__(
            cls,
            **kwargs: object
    ) -> None:
        super().__init_subclass__(**kwargs)
        if not isinstance(getattr(cls, "VALIDATOR_NAME", None), str) or not cls.VALIDATOR_NAME.strip():
            raise TypeError(f"{cls.__name__} must define a non-empty VALIDATOR_NAME")

    @abstractmethod
    def __call__(
            self,
            data: T
    ) -> None:
        ...