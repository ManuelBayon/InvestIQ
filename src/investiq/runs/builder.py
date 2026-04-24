from collections.abc import Sequence

from investiq.api.backtest import RunId
from investiq.api.features import FeatureCalculator
from investiq.api.filter import Filter
from investiq.api.instruments import Instrument
from investiq.api.strategy import Strategy
from investiq.core.backtest_engine import BacktestEngine
from investiq.core.features_store import FeatureStore

from investiq.core.decision_pipeline import DecisionPipeline
from investiq.core.market_store import MarketStore
from investiq.utilities.logger.factory import LoggerFactory


def bootstrap_backtest_engine(
        logger_factory: LoggerFactory,
        instrument: Instrument,
        feature_calculators: Sequence[FeatureCalculator],
        strategy: Strategy,
        filters: list[Filter] | None = None,
        initial_cash: float = 100_000,
) -> BacktestEngine:

    market_store = MarketStore()

    feature_store = FeatureStore(
        calculators=feature_calculators,
    )

    # 1. Build Strategy Orchestrator
    decision_pipeline = DecisionPipeline(
        strategy=strategy,
        filters=filters,
    )

    # 2. Build Transition Engine
    transition_engine = TransitionEngine(logger_factory=logger_factory)

    # 3. Build Portfolio
    portfolio = Portfolio(
        logger_factory=logger_factory,
        instrument=instrument,
        initial_cash=initial_cash,
    )

    # 4. Build Backtest Engine
    return BacktestEngine(
        run_id=RunId("abc"),
        logger_factory=logger_factory,
        market_store=market_store,
        feature_store=feature_store,
        decision_pipeline=decision_pipeline,
        transition_engine=transition_engine,
        portfolio=portfolio,
    )