from abc import ABC, abstractmethod
from enum import Enum

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.common.protocols import WriterCore
from investiq.utilities.logger.protocol import LoggerProtocol


class BatchWriterCoreState(str, Enum):
    NEW = "NEW"
    STARTED = "STARTED"
    ENCODED = "ENCODED"
    ENDED = "ENDED"
    ERROR = "ERROR"

class BatchWriterCore[FormattedT, EncodedT](WriterCore[FormattedT, EncodedT], ABC):
    """
    Abstract base class for batch-oriented writers_core.

    Implements WriterCore[FormattedT, EncodedT].

    Characteristics:
    - Processes a *bounded* set of data (single-shot write).
    - Suitable for backtests, daily exports, or offline jobs.
    - Produces one EncodedT artifact per on_write() call.

    Responsibilities:
    - Encode entire datasets (e.g., JSON, CSV, Parquet, Arrow).
    - Manage optional internal buffers or compression state.
    - Must not perform I/O (handled by Sink).

    Lifecycle:
    - on_start() → prepare state
    - on_encode(data) → encode batch
    - on_end() → finalize encoder
    """

    def __init__(
            self,
            logger: LoggerProtocol
    ) -> None:
        self._logger = logger
        self._state = BatchWriterCoreState.NEW

    def on_start(self) -> None:
        if self._state != BatchWriterCoreState.NEW:
            raise ExportError(f"Cannot start core_writer from state {self._state}")
        try:
            self._start()
            self._logger.debug("Writer core started.")
            self._state =BatchWriterCoreState.STARTED
        except ExportError as e:
            self._state = BatchWriterCoreState.ERROR
            self._logger.error(f"Writer core failed to start: {e}")
            raise ExportError(f"Failed to start writer core: {e}") from e

    def on_encode(self, data: FormattedT) -> EncodedT:
        """Encode the given batch into an EncodedT artifact."""
        if self._state != BatchWriterCoreState.STARTED:
            raise ExportError(f"Cannot encode data in state {self._state}")
        try:
            encoded: EncodedT = self._encode(data)
            self._logger.debug("BatchCoreWriter encoded data.")
            self._state = BatchWriterCoreState.ENCODED
            return encoded
        except ExportError as e:
            self._state = BatchWriterCoreState.ERROR
            raise ExportError(f"Encoding failed: {e}") from e

    def on_end(self) -> None:
        """
        Finalize the core writer safely according to its current state.

        Transitions:
            NEW -> Error (invalid)
            STARTED -> Warn (no data encoded)
            ENCODED -> Normal finalize
            ENDED -> Idempotent no-op
            ERROR -> Cleanup after failure
        """
        match self._state:
            case BatchWriterCoreState.NEW:
                self._handle_close_from_new()
            case BatchWriterCoreState.STARTED:
                self._handle_close_from_started()
            case BatchWriterCoreState.ENCODED:
                self._handle_close_from_encoded()
            case BatchWriterCoreState.ENDED:
                self._handle_close_from_ended()
            case BatchWriterCoreState.ERROR:
                self._handle_close_from_error()
            case _:
                raise ExportError(f"Invalid writer core state: {self._state}")

    def _handle_close_from_new(self) -> None:
        msg = "Cannot end writer core that was never started."
        self._logger.error(msg)
        raise ExportError(msg)

    def _handle_close_from_started(self) -> None:
        self._logger.warning("Finalizing empty core writer, no data encoded")
        try:
            self._finalize_empty()
            self._state = BatchWriterCoreState.ENDED
        except ExportError as e:
            self._state = BatchWriterCoreState.ERROR
            raise ExportError(f"Failed to finalize empty writer: {e}") from e

    def _handle_close_from_encoded(self) -> None:
        self._logger.debug("Finalizing writer core with encoded data.")
        try:
            self._finalize()
            self._state = BatchWriterCoreState.ENDED
        except ExportError as e:
            self._state = BatchWriterCoreState.ERROR
            raise ExportError(f"Failed to finalize encoded writer: {e}") from e

    def _handle_close_from_ended(self) -> None:
        self._logger.debug("Writer core already finalized — idempotent no-op.")

    def _handle_close_from_error(self) -> None:
        self._logger.warning("Cleaning up after writer core error.")
        try:
            self._cleanup_after_error()
        except ExportError as e:
            self._logger.error(f"Cleanup after error failed: {e}")
        finally:
            self._state = BatchWriterCoreState.ERROR

    # Abstract Hooks
    @abstractmethod
    def _start(self) -> None: ...

    @abstractmethod
    def _encode(self, data: FormattedT) -> EncodedT: ...

    @abstractmethod
    def _finalize_empty(self) -> None: ...

    @abstractmethod
    def _finalize(self) -> None: ...

    @abstractmethod
    def _cleanup_after_error(self) -> None: ...
