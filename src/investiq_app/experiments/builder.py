from dataclasses import dataclass
from datetime import datetime

from investiq.api.config import BacktestConfig

from investiq.api.backtest import BacktestInput
from investiq.core.backtest_engine import BacktestEngine

from investiq.export_engine.registries.config import ExportKey, ExportOptions
from investiq.export_engine.runner import BacktestExportRunner
from investiq.market_data.adapters.ibkr.connection_config import ConnectionConfig
from investiq.market_data.adapters.ibkr.data_source import IBKRHistoricalDataSource
from investiq.market_data.adapters.ibkr.tws_connection import TWSConnection
from investiq.market_data.domain.requests.historical import HistoricalRequestSpec
from investiq.market_data.engine.service import HistoricalDataService
from investiq.market_data.feeds.dataframe_feed import DataFrameBacktestFeed

from investiq.utilities.logger.factory import LoggerFactory
from investiq.utilities.logger.setup import init_base_logger
from investiq.runs.builder import bootstrap_backtest_engine
from investiq_app.experiments.instrument_mapper import to_provider_instrument


@dataclass
class BacktestBundle:
    logger_factory: LoggerFactory
    backtest_input: BacktestInput
    backtest_engine: BacktestEngine
    exporter: BacktestExportRunner


class FutureCME:
    pass


def build_experiment(config: BacktestConfig) -> BacktestBundle:

    # 0. Init base logger
    init_base_logger(debug=config.debug)
    logger_factory = LoggerFactory(
        engine_type="Backtest",
        run_id="0841996",
    )

    # 1. Configure and load historical data (V2)
    instrument_spec = to_provider_instrument(config.instrument)

    request_spec = HistoricalRequestSpec(
        duration=config.market_data_request.duration,
        bar_size=config.market_data_request.bar_size,
        what_to_show=config.market_data_request.what_to_show,
    )

    tws_connection = TWSConnection(
        logger=logger_factory.child("TWS Connection").get(),
        config=ConnectionConfig.paper(),
    )

    data_source = IBKRHistoricalDataSource(
        logger=logger_factory.child("InteractiveBroker DataSource").get(),
        connection=tws_connection,
    )

    data_service = HistoricalDataService(
        logger=logger_factory.child("Historical Data Service").get(),
        data_source=data_source,
    )

    df = data_service.load(instrument_spec, request_spec)

    # 2. Bootstrap Backtest Engine
    backtest_engine: BacktestEngine = bootstrap_backtest_engine(
        logger_factory=logger_factory,
        instrument=config.instrument,
        feature_calculators=config.feature_calculators,
        strategy=config.strategy,
        filters=config.filters,
        initial_cash=config.initial_cash
    )

    # 3. Create event feed from data frame and initialize backtest input
    feed = DataFrameBacktestFeed(
        logger=logger_factory.child("BacktestFeed").get(),
        df=df,
        instrument=config.instrument,
        bar_size=config.market_data_request.bar_size,
    )
    bt_input = BacktestInput(
        instrument=config.instrument,

        events=feed
    )

    # 4. Exporter configuration
    export_runner = BacktestExportRunner(
        logger_factory=logger_factory,
        export_key=ExportKey.EXCEL,
        export_options=ExportOptions(
            sink={
                "filename": "MNQ" + datetime.now().strftime("_%Y-%m-%d_%Hh%M"),
            }
        )
    )

    # 5. Return BacktestBundle
    return BacktestBundle(
        logger_factory=logger_factory,
        backtest_input=bt_input,
        backtest_engine=backtest_engine,
        exporter=export_runner
    )