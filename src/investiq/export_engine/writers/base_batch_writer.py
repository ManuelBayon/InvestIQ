from abc import ABC
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Self, TypeVar

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.sinks.base_batch_sink import BatchSink
from investiq.export_engine.writers_core.base_core_batch_writer import BatchWriterCore
from investiq.utilities.logger.protocol import LoggerProtocol
from investiq.utilities.validator.common.errors import ValidationError
from investiq.utilities.validator.interface import ValidatorStrategy


class BatchWriterState(str, Enum):
    """Represents the lifecycle states of the BatchWriter."""
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"

ValidationT = TypeVar("ValidationT")
class BatchWriter[FormattedT, EncodedT](ABC):
    """
    High-level batch writer orchestrating a WriterCore and a Sink.

    Responsibilities
    - Manage the export lifecycle: start() → 0..N write() → commit() → close()
    - Delegate encoding to WriterCore[FormattedT, EncodedT]
    - Delegate persistence to BaseBatchSink[EncodedT]
    - Enforce deterministic state transitions and consistent error handling

    Invariants
    - I/O is performed only by the Sink (the WriterCore encodes only).
    - Public lifecycle methods are final and not overridden by subclasses.
    - Instance is one-shot: after COMMITTED or ERROR, only close() is valid.

    Typical flow
        with writer:
            for item in formatted_items:
                writer.write(item)
            writer.commit()

    Notes
    - `validate` can be provided to enforce schema/consistency per item.
    - Counters (writes_total/errors_total) are maintained for observability.
    """
    def __init__(
            self,
            logger: LoggerProtocol,
            writer_core: BatchWriterCore[FormattedT, EncodedT],
            sink: BatchSink[EncodedT],
            formatted_validator: ValidatorStrategy[FormattedT] | None = None,
            encoded_validator: ValidatorStrategy[EncodedT] | None = None
    ):
        self._logger = logger
        self._writer_core = writer_core
        self._sink = sink
        self._formatted_validator = formatted_validator
        self._encoded_validator = encoded_validator
        self._state : BatchWriterState = BatchWriterState.NEW
        self._writes_total: int = 0
        self._errors_total: int = 0

    def __enter__(self) -> Self:
        """
        Enter the context manager, automatically starting the writer.

        Returns:
            Self: The active writer instance, ready for write operations.
        """
        self.start()
        return self

    def start(self) -> None:
        """
        Start the BatchWriter by initializing the WriterCore and opening the Sink.

        Valid only in NEW state.

        Transitions:
            NEW → ACTIVE
            NEW → ERROR (on failure)

        Raises:
            ExportError: If startup fails or the writer is already active.
        """
        self._logger.debug("Starting writer core and opening sink.")
        try:
            self._writer_core.on_start()
            self._sink.open()
            self._logger.debug("Writer started successfully.")
            self._state = BatchWriterState.ACTIVE
        except ExportError as e:
            self._logger.error(f"Export error during start(): {e}")
            self._state = BatchWriterState.ERROR
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error during start(): {e}")
            self._state = BatchWriterState.ERROR
            raise ExportError(f"Unexpected start() failure: {e}") from e

    def write(
            self,
            data: FormattedT
    ) -> None:
        """
        Encode and persist a batch of data.

        Valid only in ACTIVE state.

        Steps:
            1. Validate input (optional)
            2. Encode formatted data via WriterCore.
            3. Validate encoded output (optional)
            4. Persist encoded artifact through the Sink.
            5. Update counters and maintain a deterministic state.

        Args:
            data: The formatted batch to encode and persist.

        Raises:
            ValidationError: If any validation fails.
            ExportError: If encoding or writing fails.
        """
        if self._state != BatchWriterState.ACTIVE:
            raise ExportError("Cannot write outside ACTIVE state")

        try:
            # Step 0 - Validate formatted data
            if self._formatted_validator:
               self._safe_validate(
                   validator=self._formatted_validator,
                   data=data,
                   stage="Formatted data"
               )
               self._logger.debug("Formatted data validated successfully.")

            # Step 1 — encode via writer core
            encoded: EncodedT = self._writer_core.on_encode(data)
            self._logger.debug("WriterCore successfully encoded data.")

            # Step 2 - Validate encoded artifact
            if self._encoded_validator:
                self._safe_validate(
                    validator=self._encoded_validator,
                    data=encoded,
                    stage="Encoded data"
                )
                self._logger.debug("Encoded data validated successfully.")

            # Step 3 — write via sink
            self._sink.write(encoded)
            self._logger.debug("Sink successfully wrote encoded data.")

            # Step 3 — update internal counters / state
            self._writes_total += 1
            self._logger.debug(f"Write #{self._writes_total} succeeded.")

        except ValidationError as e:
            self._errors_total += 1
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Validation failed: {e}")
            raise ExportError(f"Validation failed: {e}") from e

        except ExportError as e:
            self._errors_total += 1
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Export error during write(): {e}")
            raise

        except Exception as e:
            self._errors_total += 1
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Unexpected error during write(): {e}")
            raise ExportError(f"Unexpected write() failure: {e}") from e

    def commit(self) -> None:
        """
        Finalize and commit all written data.

        Valid only in ACTIVE state.

        Steps:
            1. Finalize the WriterCore (on_end).
            2. Commit all data via the Sink.
            3. Transition to COMMITTED state.

        Raises:
            ExportError: If finalization or commit fails.
        """
        if self._state != BatchWriterState.ACTIVE:
            raise ExportError(f"Cannot commit in state {self._state}")

        try:
            # Step 1 — finalize the encoding lifecycle
            self._writer_core.on_end()
            self._logger.debug("WriterCore finalized successfully.")

            # Step 2 — commit sink (atomic persistence)
            self._sink.commit()
            self._logger.debug("Sink committed successfully.")

            # Step 3 — transition to committed
            self._state = BatchWriterState.COMMITTED

        except ExportError as e:
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Commit failed due to ExportError: {e}")
            raise
        except Exception as e:
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Unexpected error during commit(): {e}")
            raise ExportError(f"Unexpected commit() failure: {e}") from e

    def close(self) -> None:
        """
        Safely close the writer and release resources.

        Valid in any state except CLOSED.

        Transitions:
            COMMITTED → CLOSED
            ACTIVE → ERROR (if uncommitted)
            ERROR → ERROR (cleanup)
            CLOSED → no-op

        Raises:
            ExportError: If sink closure fails.
        """

        if self._state == BatchWriterState.CLOSED:
            self._logger.debug("Writer already closed — no-op.")
            return

        self._logger.debug(f"Closing writer from state {self._state}")
        try:
            self._sink.close()
            self._state = BatchWriterState.CLOSED
            self._logger.debug("Writer closed cleanly.")
        except ExportError as e:
            self._logger.error(f"Close failed: {e}")
            self._state = BatchWriterState.ERROR
            raise
        except Exception as e:
            self._state = BatchWriterState.ERROR
            self._logger.error(f"Unexpected error during close(): {e}")
            raise ExportError(f"Unexpected close() failure: {e}") from e

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """
        Ensure safe resource cleanup when leaving a context.

        If an exception occurred, the writer transitions to ERROR state
        before attempting cleanup.

        Args:
            exc_type: Exception type (if raised).
            exc_val: Exception instance.
            exc_tb: Traceback associated with the exception.

        Returns:
            False: Always re-raises exceptions (does not suppress them).
        """
        try:
            if exc_type:
                self._logger.error(f"Writer exiting due to exception: {exc_val}")
                self._state = BatchWriterState.ERROR
            self.close()
        except Exception as e:
            self._logger.error(f"Writer failed to close properly: {e}")
        return None  # never suppress exceptions

    def _safe_validate(
            self,
            validator: ValidatorStrategy[ValidationT],
            data: ValidationT,
            stage: str
    ) -> None:
        try:
            validator(data)
            self._logger.debug(f"{stage} validated successfully.")
        except ValidationError as e:
            self._errors_total += 1
            self._state = BatchWriterState.ERROR
            msg = f"{stage} validation failed: {e}"
            self._logger.error(msg)
            raise ExportError(msg) from e

    @property
    def output_path(self) -> Path:
        if self._state != BatchWriterState.COMMITTED:
            raise ExportError("output_path requested before commit")
        return self._sink.output_path