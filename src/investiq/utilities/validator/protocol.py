from typing import Protocol, runtime_checkable


@runtime_checkable
class ValidatorProtocol[T](Protocol):
    """
    Common runtime interface for all validators.
    """

    def __call__(
            self,
            data: T
    ) -> None:
        """Raise a ValidationError or subclass if invalid."""
        ...