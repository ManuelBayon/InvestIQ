from io import BytesIO
from typing import BinaryIO

import pandas as pd

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.writers_core.base_core_batch_writer import BatchWriterCore
from investiq.utilities.logger.protocol import LoggerProtocol


class ExcelWriterCore(BatchWriterCore[pd.DataFrame, bytes]):

    def __init__(
            self,
            logger: LoggerProtocol
    ):
        super().__init__(logger)
        self._buffer: BinaryIO | None = None
        self._name: str = "ExcelWriterCore"

    def _start(self) -> None:
        self._logger.debug(f"{self._name} starting (allocating buffer).")
        self._buffer = BytesIO()

    def _encode(
            self,
            data: pd.DataFrame
    ) -> bytes:

        if self._buffer is None:
            raise ExportError(f"{self._name} not started")

        try:
            with pd.ExcelWriter(self._buffer, engine="xlsxwriter") as writer:
                data.to_excel(writer, index=False, sheet_name="Backtest Logs")

            self._logger.debug("DataFrame successfully encoded to Excel bytes.")

            if not isinstance(self._buffer, BytesIO):
                raise ExportError("Unsupported buffer type for Excel export.")

            return self._buffer.getvalue()

        except Exception as e:
            raise ExportError(f"Failed to encode DataFrame to Excel bytes: {e}") from e

    def _finalize_empty(self) -> None:
        self._logger.warning(f"Finalizing {self._name} with no data written.")

    def _finalize(self) -> None:
        self._logger.debug(f"Finalizing {self._name} and clearing buffer.")
        if self._buffer is not None:
            try:
                self._buffer.close()
            except Exception as e:
                self._logger.warning(f"Failed to close buffer: {e}")
            self._buffer = None

    def _cleanup_after_error(self) -> None:
        self._logger.warning("Cleaning up after ExcelWriterCore error.")
        if self._buffer is not None:
            try:
                self._buffer.close()
            except Exception as e:
                self._logger.warning(f"Failed to close buffer: {e}")
            self._buffer = None