import os
from pathlib import Path

from investiq_app.settings.types import AppSettings, EnvType, DebugMode


def load_app_settings() -> AppSettings:

    # 1. Base dir
    base_dir_raw = os.getenv("INVESTIQ_RUN_DIR")

    if base_dir_raw:
        base_dir = Path(base_dir_raw)
    else:
        base_dir = Path(r"D:\3 - InvestIQ - Runs")

    # 2. Environnement
    env_raw = os.getenv("INVESTIQ_ENV", "DEBUG").upper()
    env = EnvType[env_raw]

    debug_raw = os.getenv("INVESTIQ_DEBUG", "ON").upper()
    debug = DebugMode[debug_raw]

    # 3. Derived variables
    engine_log_dir = base_dir / "Engine logs"
    backtest_log_dir = base_dir / "Backtest logs"

    return AppSettings(
        base_dir=base_dir,
        engine_log_dir=engine_log_dir,
        backtest_log_dir=backtest_log_dir,
        env=env,
        debug=debug,
    )