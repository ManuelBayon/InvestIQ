from investiq.export_engine.formatters.components.ExecutionLogEntryToDataFrame import BacktestDataFrameFormatter
from investiq.export_engine.registries.components.backtest import BacktestExportRegistry
from investiq.export_engine.registries.config import ExportKey
from investiq.export_engine.sinks.components.file_batch_sink import FileBatchSink
from investiq.export_engine.writers_core.components.ExcelWriterCore import ExcelWriterCore

@BacktestExportRegistry.bind(
    key=ExportKey.EXCEL,
)
class BacktestExcelPipeline:
    formatter_cls = BacktestDataFrameFormatter
    writer_core_cls = ExcelWriterCore
    sink_cls = FileBatchSink