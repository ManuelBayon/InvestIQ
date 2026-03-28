from engine.utilities.logger.protocol import LoggerProtocol
from engine.utilities.validator.common.errors import ValidationError, NonRecoverableValidationError
from engine.utilities.validator.common.policy import ValidationPolicy
from engine.utilities.validator.interface import ValidatorStrategy

class CompositeValidator[T]:
    """
    A high-reliability composite validator that executes multiple
    validation checks with configurable policy.

    Features:
    - Deterministic execution order
    - Policy-based reaction (STRICT / LOG_ONLY / IGNORE)
    - Contextual logging
    """
    def __init__(
            self,
            logger: LoggerProtocol,
            *validators: ValidatorStrategy,
            policy: ValidationPolicy = ValidationPolicy.STRICT,
    ):
        self._logger: LoggerProtocol = logger
        self._validators: tuple[ValidatorStrategy, ...] = validators
        self._policy = policy

    def __call__(self, data: T) -> None:
        for validator in self._validators:
            try:
                validator(data)
            except ValidationError as e:
                msg = f"Validation failed in {validator.VALIDATOR_NAME}: {e}"
                match self._policy:
                    case ValidationPolicy.STRICT:
                        self._logger.error(msg)
                        raise
                    case ValidationPolicy.LOG_ONLY:
                        self._logger.warning(msg)
                        continue
                    case ValidationPolicy.IGNORE:
                        self._logger.debug(msg)
                        continue
                    case _:
                        raise NonRecoverableValidationError(
                            f"Unknown policy {self._policy}"
                        )