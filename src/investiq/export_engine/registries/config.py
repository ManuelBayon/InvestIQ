from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from investiq.export_engine.formatters.base_batch_formatter import BatchFormatter
from investiq.export_engine.sinks.base_batch_sink import BatchSink
from investiq.export_engine.writers.base_batch_writer import BatchWriter
from investiq.export_engine.writers_core.base_core_batch_writer import BatchWriterCore


class ExportKey(str, Enum):
    EXCEL = "EXCEL"

@dataclass(frozen=True)
class BatchExportBinding[RawT, FormattedT, EncodedT]:
    """
    Static binding
    Typical pair (Formatter, WriterCore, Sink)
    """
    formatter_cls: type[BatchFormatter[RawT, FormattedT]]
    writer_core_cls: type[BatchWriterCore[FormattedT, EncodedT]]
    sink_cls: type[BatchSink[EncodedT]]
    writer_cls: type[BatchWriter[FormattedT, EncodedT]] | None = None

@dataclass
class ExportOptions:
    """
    Optional configuration layer to inject dynamic parameters
    into formatter, writer_core, and sink.
    """
    formatter: dict[str, object] = field(default_factory=dict)
    writer_core: dict[str, object] = field(default_factory=dict)
    sink: dict[str, object] = field(default_factory=dict)

    global_output_dir: Path | None = None