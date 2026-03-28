from abc import ABC
from typing import ClassVar

from investiq.utilities.logger.protocol import LoggerProtocol


class BaseValidator(ABC):
    """
    Base class providing logging and common validator context.
    """
    VALIDATOR_NAME: ClassVar[str]

    def __init__(
            self,
            logger: LoggerProtocol
    ):
        self.logger = logger