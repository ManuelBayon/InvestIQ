from investiq.runs.reporting import print_backtest_summary
from investiq_app.config import backtest_config
from investiq_app.experiments.builder import build_experiment

def main() -> None:

    # 1. Build experiment (bootstrap engines)
    bundle = build_experiment(config=backtest_config)

    # 2. Run the backtest
    result = bundle.backtest_engine.run(bt_input=bundle.backtest_input)

    # 3. Export fill log
    bundle.exporter.export(
        fill_log=result.fill_log,
        metrics=result.metrics
    )

    # 4. Print backtest summary
    print_backtest_summary(result, backtest_config)

if __name__ == "__main__":
    main()
