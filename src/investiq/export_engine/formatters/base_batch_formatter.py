from abc import ABC, abstractmethod
from typing import Iterable

from investiq.export_engine.common.protocols import Formatter
from investiq.utilities.logger.protocol import LoggerProtocol
from investiq.utilities.validator.interface import ValidatorStrategy


class BatchFormatter[RawT, FormattedT](Formatter[RawT, FormattedT], ABC):
    """
    Abstract base class for batch-oriented formatters.

    Implements the Formatter[RawT, FormattedT] protocol.

    Characteristics:
    - Processes *bounded* collections of data.
    - Used for offline exports, backtests, or periodic jobs.
    - Typically transforms an entire dataset at once into a single output artifact.
    """

    def __init__(
        self,
        logger: LoggerProtocol,
        raw_validator: ValidatorStrategy[RawT] | None = None,

    ) -> None:
        self._logger = logger
        self._raw_validator = raw_validator

    def format(
        self,
        data: Iterable[RawT]
    ) -> FormattedT:
        """
        Apply optional validation before formatting the batch.
        """
        if self._raw_validator:
            self._logger.debug("Validating raw data before formatting...")
            for item in data:
                self._raw_validator(item)
            self._logger.debug("Raw data validated successfully.")

        return self._format(data)

    @abstractmethod
    def _format(
            self,
            data: Iterable[RawT]
    ) -> FormattedT:
        ...