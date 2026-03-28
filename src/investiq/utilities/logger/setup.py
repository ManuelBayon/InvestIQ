import logging
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from colorlog import ColoredFormatter

from investiq_app.settings.load_app_settings import load_app_settings

class RotationType(Enum):
    SIZE = "SIZE"
    TIME = "TIME"

_base_logger: logging.Logger | None = None

def init_base_logger(
        debug: bool = False,
        rotation: RotationType = RotationType.TIME,
        log_file: Optional[Path] = None
) -> None:

    global _base_logger

    app_settings = load_app_settings()

    """Initializes the central logger (to be called only once, e.g., in main or conftest)."""
    if log_file is None:
        log_file = Path(app_settings.engine_log_dir).joinpath("output.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("InvestIQ")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler: logging.Handler

    if not logger.hasHandlers():
        if rotation is RotationType.SIZE:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=5_000_000,
                backupCount=5,
                encoding="utf-8"
            )
        elif rotation is RotationType.TIME:
            handler = TimedRotatingFileHandler(
                log_file,
                when = "midnight",
                interval = 1,
                backupCount = 30,
                encoding = "utf-8"
            )
        else:
            raise ValueError("rotation must be SIZE or TIME")

        formatter = logging.Formatter(
            fmt = "%(asctime)s.%(msecs)03d | "
                  "%(levelname)-5s | "
                  "%(engine_type)-8s | "
                  "run_id=%(run_id)-10s | "
                  "%(name)s | "
                  "%(message)-50s",
            datefmt = "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        console = logging.StreamHandler()
        formatter = ColoredFormatter(
            fmt = "%(log_color)s%(asctime)s.%(msecs)03d | "
                  "%(engine_type)-8s | "
                  "%(name)s | "
                  "%(message)s",
            datefmt = "%Y-%m-%d %H:%M:%S",
            log_colors = {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        )
        console.setFormatter(formatter)
        logger.addHandler(console)

    _base_logger = logger

def _get_base_logger_ref() -> Optional[logging.Logger]:
    """Internal: return the raw reference (maybe None)."""
    return _base_logger