from collections.abc import Mapping

from investiq.api.config import BacktestConfig
from investiq.api.execution import RunResult
from investiq.core.transition_engine.enums import FIFOSide


def line(label: str, value: str, width: int = 25) -> str:
    return f"{label:<{width}}: {value}"

def count_entries(result: RunResult) -> dict[FIFOSide, int]:
    long_entries = 0
    short_entries = 0

    for fill in result.fill_log:
        is_open = fill.entry_price is not None and fill.exit_price is None
        if not is_open:
            continue
        if fill.position_side == FIFOSide.LONG:
            long_entries += 1
        elif fill.position_side == FIFOSide.SHORT:
            short_entries += 1
    return {
        FIFOSide.LONG: long_entries,
        FIFOSide.SHORT: short_entries,
    }

def count_closed_trades(result: RunResult) -> dict[FIFOSide, int]:
    long_trades = 0
    short_trades = 0

    for fill in result.fill_log:
        is_close = fill.entry_price is not None and fill.exit_price is not None
        if not is_close:
            continue
        if fill.position_side == FIFOSide.LONG:
            long_trades += 1
        elif fill.position_side == FIFOSide.SHORT:
            short_trades += 1
    return {
        FIFOSide.LONG: long_trades,
        FIFOSide.SHORT: short_trades,
    }

def compute_data_duration(start, end):
    delta = end - start

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days}d {hours}h {minutes}m {seconds}s"

def format_parameters(params: Mapping[str, object]) -> list[str]:
    if not params:
        return ["None"]
    lines = []
    for key in sorted(params.keys()):
        value = params[key]
        lines.append(line(f"  {key}", repr(value)))
    return lines

def print_backtest_summary(
        result: RunResult,
        config: BacktestConfig
) -> None:

    # Header
    print("\n========== BACKTEST RUN ==========\n")

    print(line("Symbol", result.instrument.symbol))
    print(line("Asset Type", result.instrument.asset_type.name))
    print(line("Exchange", result.instrument.exchange.name))
    print(line("Currency", result.instrument.currency.name))
    print(line("Tick Size", str(result.instrument.tick_size)))
    print(line("Lot Size", str(result.instrument.lot_size)))
    print(line("Multiplier", str(result.instrument.contract_multiplier)))

    print("")
    duration = compute_data_duration(result.start, result.end)
    print(line("Start Date", f"{result.start.strftime("%Y-%m-%d %H:%M:%S %Z")}"))
    print(line("End Date", f"{result.end.strftime("%Y-%m-%d %H:%M:%S %Z")}"))
    print(line("Data Duration", f"{duration}"))
    runtime_ms = result.runtime_duration * 1000

    print("")
    print(line("Events", str(result.event_count)))
    print(line("Runtime", f"{result.runtime_duration:.2f}s ({runtime_ms:.2f} ms)"))

    print("")
    print(line("Strategy", config.strategy.metadata.name))
    print(line("Version", config.strategy.metadata.version))
    print(line("Nb. Parameters", str(len(config.strategy.metadata.parameters))))
    for param_line in format_parameters(config.strategy.metadata.parameters):
        print(param_line)
    print(line("Required Pipelines", ", ".join(config.strategy.metadata.required_feature_names)))


    print("")
    if not config.filters:
        print(line("Nb. Filters", "0"))
    else:
        print(line("Nb. Filters", str(len(config.filters))))
        for f in config.filters:
            print("")
            print(line("Filter", f.metadata.name))
            print(line("Version", f.metadata.version))
            print(line("Nb. Parameters", str(len(f.metadata.parameters))))
            for param_line in format_parameters(f.metadata.parameters):
                print(param_line)

    # Summary
    print("\n========== BACKTEST SUMMARY ==========\n")
    entries = count_entries(result)
    print(line("Long Entries", f"{entries[FIFOSide.LONG]}"))
    print(line("Short Entries", f"{entries[FIFOSide.SHORT]}"))

    print("")
    trades = count_closed_trades(result)
    print(line("Long Trades", f"{trades[FIFOSide.LONG]}"))
    print(line("Short Trades", f"{trades[FIFOSide.SHORT]}"))

    print("")
    print(line("Final Position", f"{result.metrics['Final Position']:.2f}"))

    print("")
    print(line("Initial Cash", f"{result.metrics['Initial Cash']:.2f}"))
    print(line("Final Cash", f"{result.metrics['Final Cash']:.2f}"))
    print(line("Net Liquid. Value", f"{result.metrics['Net Liquidation Value']:.2f}"))

    print("")
    print(line("Realized PnL", f"{result.metrics['Realized PnL']:.2f}"))
    print(line("Unrealized PnL", f"{result.metrics['Unrealized PnL']:.2f}"))