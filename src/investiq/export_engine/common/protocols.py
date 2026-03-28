from collections.abc import Iterable
from types import TracebackType
from typing import Protocol, runtime_checkable, Callable, Self

@runtime_checkable
class Formatter[RawT, FormattedT](Protocol):
    """
    (-RawT, +FormattedT)
    Converts a stream of raw domain data (RawT)
    into a formatted representation (FormattedT).
    """
    def format(
            self,
            data: Iterable[RawT]
    ) -> FormattedT:
        ...

@runtime_checkable
class WriterCore[FormattedT, EncodedT](Protocol):
    """
    Converts formatted data (FormattedT) into an encoded artifact (EncodedT)
    ready for persistence or transmission.

    Responsibilities:
    - Transform structured data into a stable binary or textual representation.
    - Manage an internal write lifecycle:
        on_start() -> 0..N on_write() -> on_end()
    - Must be idempotent when possible and deterministic given identical input.
    - Must not perform I/O operations directly.

    Lifecycle:
    - on_start(): prepare internal buffers or compression context.
    - on_write(data): encode one logical unit of formatted data.
    - On_end(): flush remaining buffers and finalize internal state.

    Guarantees:
    - All outputs from on_write() must be self-contained and valid EncodedT objects.
    - Thread-safety is optional, but reentrancy must be documented.
    - Must raise explicit Recoverable / NonRecoverable exceptions if used
      within a retryable pipeline.

    Example:
        CsvWriterCore[list[dict], bytes]
        JsonWriterCore[list[dict], str]
        ParquetWriterCore[ArrowTable, bytes]
    """
    def on_start(self) -> None: ...
    def on_encode(
            self,
            data: FormattedT
    ) -> EncodedT: ...
    def on_end(self) -> None: ...

@runtime_checkable
class Sink[EncodedT](Protocol):
    """
    Abstract destination for encoded data (EncodedT).

    Responsibilities:
    - Handle persistence (filesystem, S3, DB, message bus, etc.)
    - Guarantee atomic commit semantics.
    - Be usable as a context manager.

    Contract:
    - __enter__(): initialize transactional resources.
    - write(data): append or stage encoded data.
    - commit(): atomically persist all staged data.
    - close(): release resources.
    - __exit__(): ensure rollback or safe close on error.

    Notes:
    - commit() must be idempotent.
    - close() must not imply commit unless explicitly documented.
    - Implementations should log all lifecycle transitions.

    Example:
        with FileSink[bytes]("/tmp/out.jsonl") as sink:
            for chunk in encoded_batches:
                sink.write(chunk)
            sink.commit()
    """
    def __enter__(self) -> Self: ...
    def open(self) -> None: ...
    def write(
            self,
            data: EncodedT
    ) -> None: ...
    def commit(self) -> None: ...
    def close(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> bool | None:
        ...