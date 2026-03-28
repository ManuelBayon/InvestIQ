from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Self, final

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.common.protocols import Sink
from investiq.utilities.logger.protocol import LoggerProtocol


class SinkState(str, Enum):
    NEW = "NEW"
    OPENED = "OPENED"
    COMMITTED = "COMMITTED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"

class BatchSink[EncodedT](Sink[EncodedT], ABC):
    """
        Base class for batch-oriented sinks handling encoded artifacts (EncodedT).

        Responsibilities:
        - Manage the persistence lifecycle for bounded datasets.
        - Guarantee atomic commit semantics.
        - Provide safe open/close context.
    """
    def __init__(
            self,
            logger: LoggerProtocol
    ):
        self._logger = logger
        self._state: SinkState = SinkState.NEW

    @final
    def __enter__(self) -> Self:
        self.open()
        return self

    @final
    def open(self) -> None:
        if self._state != SinkState.NEW:
            raise ExportError(f"Cannot open sink from state {self._state}")
        self._open()
        self._state = SinkState.OPENED

    @final
    def write(
        self,
        data: EncodedT
    ) -> None:
        """
        Write encoded data to the underlying sink.

        Valid only in OPENED state.
        This method delegates to the subclass hook `_write(data)`,
        which implements the actual I/O or buffering logic.

        Parameters:
        data : EncodedT
            The encoded data chunk to be persisted or staged.

        Raises:
            - RuntimeError if called outside OPENED state.
            - ExportError if subclass `_writes` fails.
        """
        if self._state != SinkState.OPENED:
            raise ExportError(f"Cannot write data in state {self._state}")

        try:
            self._write(data)
            self._logger.debug("Sink write successful.")
        except ExportError as e:
            self._logger.error(f"Sink write failed, transitioning to ERROR: {e}")
            self._state = SinkState.ERROR
            raise

    @final
    def commit(self) -> None:
        if self._state != SinkState.OPENED:
            raise ExportError(f"Cannot commit from state {self._state}")
        self._state = SinkState.COMMITTED
        self._commit()

    @final
    def close(self) -> None:
        """
        Close the sink safely, according to its current state.
        Transitions:
            NEW -> Error (invalid)
            OPENED -> Rollback or discard (warn)
            COMMITTED -> Normal closure
            CLOSED -> Idempotent no-op
            ERROR -> Cleanup after failure
        """
        match self._state:
            case SinkState.NEW:
                self._on_close_from_new()
            case SinkState.OPENED:
                self._on_close_from_opened()
            case SinkState.COMMITTED:
                self._on_close_from_committed()
            case SinkState.CLOSED:
                self._on_close_from_closed()
            case SinkState.ERROR:
                self._on_close_from_error()
            case _:
                raise ExportError(f"Unknown sink state: {self._state}")

    @final
    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """
           Ensure resource cleanup on exit, whether normal or exceptional.

           - If an exception occurred, call `on_error()` for subclass-specific handling.
           - Always call `close()` to release resources.
           - Returning False lets the exception propagate (standard behavior).
        """
        if exc_type:
            try:
                self.on_error(exc_type, exc_val, exc_tb)
            except ExportError as e:
                self._logger.error(f"on_error() failed: {e}")
        self.close()
        return None  # Never suppress exceptions

    def on_error(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """
        Optional hook invoked when an exception occurs inside the sink context.

        Called automatically by `__exit__` before `close()`.
        Intended for subclass-specific error handling such as:
          - Logging additional diagnostic context.
          - Marking failed artifacts or metrics.
          - Triggering custom rollback logic.

        Parameters
        ----------
        exc_type : type[BaseException]
            The exception type caught by the context manager.
        exc_val : BaseException
            The exception instance.
        exc_tb : TracebackType
            The traceback object associated with the exception.

        Notes
        -----
        - Must never raise further exceptions.
        - Must not modify the sink's internal state directly.
        - Default implementation logs the exception and sets the state to ERROR.
        """
        type_name = exc_type.__name__ if exc_type else "UnknownException"
        self._logger.error(
            f"Exception in sink context: {type_name}: {exc_val}",
            exc_info=(exc_type, exc_val, exc_tb),
        )
        self._state = SinkState.ERROR

    def _on_close_from_new(self) -> None:
        self._logger.error("Attempted to close sink in NEW state — invalid lifecycle.")
        raise ExportError("Cannot close sink that was never opened.")

    def _on_close_from_opened(self) -> None:
        """
        Close the sink while it is still in OPENED state.

        This indicates an aborted session (no commit occurred).
        Performs a best-effort rollback and leaves the sink in ERROR state.
        """
        self._logger.warning("Closing sink in OPENED state without commit — performing rollback.")
        try:
            self._rollback()
        except ExportError:
            self._logger.error("Rollback failed during close from OPENED state.")
        finally:
            # Even if rollback succeeded, this sink was not committed;
            # therefore, it cannot be considered a clean closure.
            self._logger.debug("Sink closed before commit — marked as ERROR (one-shot).")
            self._state = SinkState.ERROR

    def _on_close_from_committed(self) -> None:
        self._logger.debug("Closing committed sink — finalizing resources.")
        self._finalize_resources()
        self._state = SinkState.CLOSED

    def _on_close_from_closed(self) -> None:
        self._logger.debug("Sink already closed — idempotent no-op.")

    def _on_close_from_error(self) -> None:
        """
        Attempt to clean up resources after an error,
        but maintain ERROR state to signal unrecoverable failure.
        """
        self._logger.warning("Closing sink after ERROR — performing cleanup.")
        try:
            self._cleanup_after_error()
        except ExportError:
            self._logger.error("Cleanup failed after error.")
        finally:
            self._state = SinkState.ERROR

    # ---- Abstract methods which have to be implemented by the concrete classes ---- #
    @abstractmethod
    def _open(self) -> None:
        """
        Initialize or allocate the underlying persistence resource.
        Called exactly once when the sink transitions from NEW → OPENED.

        Typical responsibilities:
          - Open files, network sockets, or database connections.
          - Allocate memory buffers or temporary staging paths.
          - Initialize metadata or transactional context.

        Guarantees:
          - Must leave the sink in a valid OPENED state.
          - Must not perform any data writes.
          - Must raise a clear exception on failure (e.g., ExportError).
        """

    @abstractmethod
    def _write(self, data: EncodedT) -> None:
        """
        Write a single encoded data chunk to the underlying resource.
        Called by the public `write()` method during the OPENED state.

        Typical responsibilities:
          - Append or stage EncodedT data (bytes, str, ArrowTable, etc.).
          - Handle buffering, batching, or temporary persistence.
          - Validate schema or serialization consistency.

        Guarantees:
          - Must not alter sink state (state is managed by BaseBatchSink).
          - Must raise ExportError on recoverable I/O or integrity failures.
          - Must not commit or close the resource directly.
        """

    @abstractmethod
    def _commit(self) -> None:
        """
        Atomically persist all staged or buffered data.
        Called exactly once during OPENED → COMMITTED transition.

        Typical responsibilities:
          - Flush buffers and finalize writes.
          - Perform atomic rename, upload, or transaction commit.
          - Ensure durability (fsync, network flush, or equivalent).

        Guarantees:
          - Must be idempotent (safe to call multiple times).
          - Must guarantee data durability before returning.
          - Must raise ExportError on failure (sink moves to ERROR state).
        """

    @abstractmethod
    def _rollback(self) -> None:
        """
        Undo or discard any staged but uncommitted data.
        Called when closing a sink in OPENED state without a commit.

        Typical responsibilities:
          - Delete temporary files or incomplete uploads.
          - Abort in-flight transactions or clear buffers.
          - Remove metadata or staging directories.

        Guarantees:
          - Must not raise unless rollback itself fails.
          - Should leave no persistent side effects (idempotent cleanup).
          - Must not commit or mark as successful.
        """

    @abstractmethod
    def _finalize_resources(self) -> None:
        """
        Release or close all resources after successful commit.
        Called during COMMITTED → CLOSED transition.

        Typical responsibilities:
          - Close file handles, sockets, or DB cursors.
          - Release compression or serialization buffers.
          - Log closure or final stats.

        Guarantees:
          - Must be idempotent (safe to call multiple times).
          - Must never raise; internal errors must be logged.
          - Must not alter persisted data.
        """

    @abstractmethod
    def _cleanup_after_error(self) -> None:
        """
        Perform best-effort cleanup after unrecoverable failure.
        Called when closing a sink in ERROR state.

        Typical responsibilities:
          - Remove corrupted or partial artifacts.
          - Roll back external operations if possible.
          - Free resources still held after exception propagation.

        Guarantees:
          - Must handle all internal exceptions defensively (log instead of raise).
          - Must not alter sink state (ERROR persists for auditability).
          - Should leave the system ready for retry with a new sink instance.
        """

    @property
    @abstractmethod
    def output_path(self) -> Path:
        """
        Absolute or normalized path to the final committed artefact.
        Must be valid after commit().
        """
        raise NotImplementedError