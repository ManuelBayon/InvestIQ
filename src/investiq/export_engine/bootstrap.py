from investiq.export_engine.registries.components.backtest import BacktestExportRegistry
from investiq.export_engine.registries.config import ExportKey
from investiq.utilities.import_tools import import_submodules
from investiq.utilities.logger.protocol import LoggerProtocol


def validate_export_registry(
        logger: LoggerProtocol,
) -> None:
    """
    Validate that all export bindings have been registered correctly.
    """

    # Force-load all modules that contain @bind declarations
    import_submodules("investiq.export_engine.services.components")

    registered = set(BacktestExportRegistry.available())
    expected = set(e for e in ExportKey)

    missing = expected - registered
    extra = registered - expected

    if missing:
        raise RuntimeError(f"Missing export bindings: {missing}")
    if extra:
        raise RuntimeError(f"Unexpected export bindings: {extra}")

    logger.debug(f"Backtest export bindings: {len(registered)} / {len(expected)} registered.")


def export_engine_bootstrap(
        logger: LoggerProtocol
) -> None:
    """
    Entry point for initializing and validating all export-related registries.
    """
    logger.debug("Initializing export engines...")
    validate_export_registry(logger)
    logger.debug("Export engines initialized successfully.")