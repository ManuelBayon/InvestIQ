from typing import ClassVar

from engine.utilities.logger.protocol import LoggerProtocol
from engine.utilities.validator.common.errors import ValidationError
from engine.utilities.validator.interface import ValidatorStrategy


class TypeValidator(ValidatorStrategy[object]):
    """
    Validates that the data matches the expected Python type.
    """

    VALIDATOR_NAME: ClassVar[str] = "type"
    
    def __init__(
            self,
            logger: LoggerProtocol,
            expected_type: type
    ):
        super().__init__(logger)
        self.expected_type = expected_type
    
    def __call__(
            self,
            data: object
    ) -> None:
        if not isinstance(data, self.expected_type):
            msg = f"Expected {self.expected_type.__name__}, got {type(data).__name__}"
            raise ValidationError(f"[{self.VALIDATOR_NAME}] {msg}")

class RangeValidator(ValidatorStrategy[float]):
    """
    Ensures that a numeric value lies within a defined inclusive range.
    """

    VALIDATOR_NAME: ClassVar[str] = "range"

    def __init__(
            self,
            logger: LoggerProtocol,
            min_value: float | None,
            max_value: float | None
    ):
        super().__init__(logger)
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, data: float) -> None:
        if not isinstance(data, (int, float)):
            msg = f"Expected numeric value, got {type(data).__name__}"
            raise ValidationError(f"[{self.VALIDATOR_NAME}] {msg}")

        if self.min_value is not None and data < self.min_value:
            msg = f"Value {data} < min {self.min_value}"
            raise ValidationError(f"[{self.VALIDATOR_NAME}] {msg}")

        if self.max_value is not None and data > self.max_value:
            msg = f"Value {data} > max {self.max_value}"
            raise ValidationError(f"[{self.VALIDATOR_NAME}] {msg}")

class SchemaValidator(ValidatorStrategy[dict]):
    """
    Validates that a mapping (typically a dict or record) conforms to an expected schema.

    The schema defines a set of required fields and their expected Python types.
    Each key in `required_fields` represents a mandatory entry that must be present
    in the input mapping and must match the declared type.
    """

    VALIDATOR_NAME: ClassVar[str] = "schema"

    def __init__(
            self,
            required_fields: dict[str, type],
            logger: LoggerProtocol
    ):
        super().__init__(logger)
        self.required_fields = required_fields

    def __call__(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise ValidationError(f"[{self.VALIDATOR_NAME}] Expected dict, got {type(data).__name__}")

        for field, expected_type in self.required_fields.items():
            if field not in data:
                raise ValidationError(f"[{self.VALIDATOR_NAME}] Missing key '{field}'")
            if not isinstance(data[field], expected_type):
                raise ValidationError(f"[{self.VALIDATOR_NAME}] Field '{field}' expected {expected_type.__name__}, got {type(data[field]).__name__}")