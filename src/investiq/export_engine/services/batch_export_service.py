from collections.abc import Iterable
from pathlib import Path

from investiq.export_engine.common.errors import ExportError
from investiq.export_engine.formatters.base_batch_formatter import BatchFormatter
from investiq.export_engine.writers.base_batch_writer import BatchWriter
from investiq.utilities.logger.protocol import LoggerProtocol
from investiq.utilities.validator.common.errors import ValidationError

class BatchExportService[RawT, FormattedT, EncodedT]:
    """
    High-level orchestration service executing an end-to-end export job.

    Responsibilities
    ----------------
    - Validate raw input data (optional)
    - Transform data via the Formatter
    - Delegate encoding and persistence to the BatchWriter
    - Ensure deterministic lifecycle and robust error handling

    Typical flow
    ------------
        service = BatchExportService(formatter, writer)
        service.export(raw_data)

    Stages
    -------
      2. Format into structured representation
      3. Write encoded batches via BatchWriter
      4. Commit and finalize
    """
    def __init__(
            self,
            logger: LoggerProtocol,
            formatter: BatchFormatter[RawT, FormattedT],
            writer: BatchWriter[FormattedT, EncodedT],
    ):
        self._logger = logger
        self._formatter = formatter
        self._writer = writer

    def export(
            self,
            raw_data: Iterable[RawT]
    ) -> Path :
        """
        Execute the end-to-end export pipeline.
        """
        self._logger.debug("Starting export pipeline")

        try:
            # Step 1 - Format raw data
            formatted_data = self._formatter.format(raw_data)

            # Step 2 - Write and commit
            with self._writer as writer:
                writer.write(formatted_data)
                writer.commit()
                path = writer.output_path

        except ValidationError as e:
            msg = f"Validation failure in pipeline: {e}"
            self._logger.error(msg)
            raise ExportError(msg) from e

        except ExportError as e:
            msg = f"ExportError during export pipeline: {e}"
            self._logger.error(msg)
            raise

        except Exception as e:
            msg = f"Unexpected error during export: {e}"
            self._logger.error(msg)  # logs traceback too
            raise ExportError(msg) from e

        self._logger.debug("Export pipeline completed successfully.")
        return path