from pathlib import Path
from typing import BinaryIO

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.sinks.base_batch_sink import BatchSink
from investiq.utilities.logger.protocol import LoggerProtocol

from investiq_app.settings.load_app_settings import load_app_settings

class FileBatchSink(BatchSink[bytes]):
    """
    Concrete sink for persisting encoded artifacts (bytes) to a file.
    Ensures atomic commit semantics and safe cleanup on failure.
    """

    def __init__(
            self,
            logger: LoggerProtocol,
            filename: str,
            suffix: str = ".xlsx",
            temp_suffix: str = ".tmp"
    ):
        super().__init__(logger)
        self._file: BinaryIO | None = None
        self._filepath: Path | None = load_app_settings().backtest_log_dir
        self._path, self._temp_path = self._resolve_paths(
            output_dir=self._filepath,
            filename=filename,
            suffix=suffix,
            temp_suffix=temp_suffix
        )

    def _open(self) -> None:
        """Open a temporary file for staged writes."""
        try:
            self._logger.debug(f"Opening temporary sink at: {self._temp_path}")
            self._temp_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )
            self._file = open(self._temp_path, "wb")
        except Exception as e:
            raise ExportError(f"Failed to open sink: {e}") from e

    def _write(
            self,
            data: bytes
    ) -> None:
        """Write encoded bytes to the temporary file."""
        if not self._file:
            raise ExportError("File sink no open.")
        try:
            self._file.write(data)
            self._logger.debug(f"Wrote {len(data)} bytes to sink.")
        except Exception as e:
            raise ExportError(f"Failed to write to sink: {e}") from e

    def _commit(self) -> None:
        """Atomically persist staged file by renaming it."""
        if not self._file:
            raise ExportError("Cannot commit: no file handle.")
        try:
            self._file.close()
            self._file = None
            self._temp_path.replace(self._path)
            self._logger.debug(f"Committed sink file to {self._path}")
        except Exception as e:
            raise ExportError(f"Failed to commit sink file: {e}") from e

    def _rollback(self) -> None:
        """Discard the temporary file on rollback."""
        if self._file is not None:
            try:
                self._file.close()
            except Exception as e:
                self._logger.warning(f"Failed to close file during rollback: {e}")
        self._file = None

        if self._temp_path.exists():
            try:
                self._temp_path.unlink()
                self._logger.warning(f"Rolled back sink file {self._temp_path}")
            except Exception as e:
                raise ExportError(f"Failed to rollback file: {e}") from e

    def _finalize_resources(self) -> None:
        """Ensure clean resource closure after successful commit."""
        self._file = None
        self._logger.debug("FileBatchSink finalized successfully.")

    def _cleanup_after_error(self) -> None:
        """Best-effort cleanup after an unrecoverable error."""
        if self._file:
            try:
                self._file.close()
            except Exception as e:
                self._logger.error(f"Failed to close file after error: {e}")
                pass
        if self._temp_path.exists():
            try:
                self._temp_path.unlink()
                self._logger.warning(f"Removed temp file after error: {self._temp_path}")
            except Exception as e:
                self._logger.error(f"Failed to clean temp file {self._temp_path}: {e}")

    @staticmethod
    def _resolve_paths(
            output_dir: Path,
            filename: str,
            suffix: str,
            temp_suffix: str
    ) -> tuple[Path, Path]:
        """
        Normalize and resolve final + temp paths for atomic writes.
        """

        if not suffix.startswith("."):
            suffix = f".{suffix}"

        if not temp_suffix.startswith("."):
            temp_suffix = f".{temp_suffix}"

        # Ensure the directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build final and temporary file paths
        final_path = output_dir / f"{filename}{suffix}"
        temp_path = output_dir / f"{filename}{suffix}{temp_suffix}"

        return final_path, temp_path

    @property
    def output_path(self) -> Path:
        """
        Final committed artefact path.
        Valid only after a successful commit.
        """
        return self._path