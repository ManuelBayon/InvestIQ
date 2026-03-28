from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class EnvType(Enum):
    PRODUCTION=auto()
    DEBUG=auto()

class DebugMode(Enum):
    ON=auto()
    OFF=auto()

@dataclass
class AppSettings:
    base_dir: Path
    engine_log_dir: Path
    backtest_log_dir: Path
    env: EnvType
    debug: DebugMode

