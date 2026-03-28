import logging
from typing import Any

from investiq.utilities.logger.setup import _get_base_logger_ref


def _get_base_logger() -> logging.Logger:
    """
        Retrieve the globally configured base logger.

        This function returns the root logger instance that must have been
        initialized via `init_base_logger()`. It is the anchor point of the
        logging hierarchy used across the entire backtest engines.

        Returns:
            logging.Logger: The initialized base logger.

        Raises:
            RuntimeError: If the base logger has not been initialized yet.
                          In production, this enforces explicit logger setup
                          (fail-fast principle). Call `init_base_logger()`
                          once at application startup before using this
                          function.

        Notes:
            - All module-level loggers should be obtained as children of
              this base logger (via `_get_module_logger(name)`).
            - This guarantees consistent formatting, rotation, and handlers
              across the whole system.
    """
    if (_logger := _get_base_logger_ref()) is None:
        raise RuntimeError("Logger not initialized. Call init_base_logger() first.")
    return _logger

def _get_child_logger(child_name: str) -> logging.Logger:
    """
    Return a child logger of the base logger for a specific module/class.
    Ensures consistent naming and propagation.
    Example:
        logger = _get_module_logger("Portfolio")
        logger.info("Portfolio initialized")
    """
    return _get_base_logger().getChild(child_name)

def get_contextual_logger(
        child_name: str,
        engine_type: str | None = None,
        run_id: int | str | None = None,
        **extras : Any
) -> logging.LoggerAdapter[logging.Logger]:
    """
    Return a fully contextual logger:
    - Hierarchical name (via _get_module_logger)
    - Dynamic context (engine_type, run_id, plus any extra fields)

    Args:
        :param child_name: Hierarchical module name (e.g., "BacktestEngine.Portfolio").
        :param engine_type: Context such as "Backtest", "Live", "Simulation".
        :param run_id: Optional identifier for correlation (int, str, or None).
        **extras: Arbitrary additional context fields (dict-like unpacking).

    Returns:
        logging.LoggerAdapter: A logger enriched with hierarchical name and dynamic context.

    Example (minimal):
    logger = get_contextual_logger("Utils.CSVParser")
    logger.warning("Empty file")
    # 2025-09-18 18:16:00.456 | WARNING | InvestIQ.Utils.CSVParser | <module> | Unknown | run_id=- | Empty file

    Example:
        logger = get_contextual_logger(
            "BacktestEngine.Portfolio",
            engine_type="Backtest",
            run_id=42,
            strategy_id="mean-revert"
        )
        logger.info("Initialized")
        # 2025-09-18 18:15:00.123 | INFO | InvestIQ.BacktestEngine.Portfolio | resolve | Backtest | run_id=42 | strategy_id=mean-revert | Initialized

    """
    child_logger = _get_child_logger(child_name)
    context : dict[str, Any] = {
        "engine_type": engine_type or "Unknown",
        "run_id": run_id or "-"
    } | extras
    return logging.LoggerAdapter(child_logger, context)