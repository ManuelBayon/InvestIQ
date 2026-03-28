from engine.utilities.logger.factory import LoggerFactory
from engine.utilities.logger.protocol import LoggerProtocol
from engine.utilities.logger.setup import init_base_logger
from engine.utilities.validator.common.policy import ValidationPolicy
from engine.utilities.validator.composite_validators.composite_validator import CompositeValidator
from engine.utilities.validator.validators.basics import RangeValidator
from engine.utilities.validator.validators.field_validator import FieldValidator


def main() -> None:
    init_base_logger(debug=True)
    logger_factory = LoggerFactory(
        base_name="Validation Module",
        engine_type="Demo"
    )
    logger: LoggerProtocol = logger_factory.get()

    range_validator = RangeValidator(
        logger=logger,
        min_value=0.0,
        max_value=100.0
    )
    price_range_validator = FieldValidator(
        logger=logger,
        field="price",
        validator=range_validator,
    )
    composite_validator = CompositeValidator(
        logger,
        price_range_validator,
        policy=ValidationPolicy.IGNORE
    )

    data = {"price": 42.5, "volume": 10}
    data_invalid = {"price": 9999.0, "volume": 10}

    composite_validator(data)
    composite_validator(data_invalid)

if __name__ == "__main__":
    main()