from investiq.api.filter import Filter
from investiq.api.instruments import Instrument
from investiq.api.strategy import Strategy
from investiq.core.backtest_engine import BacktestEngine
from investiq.core.features import FeatureStore

from investiq.execution.portfolio.portfolio import Portfolio
from investiq.execution.transition.transition_engine import TransitionEngine
from investiq.core.decision_pipeline import DecisionPipeline
from investiq.utilities.logger.factory import LoggerFactory


def bootstrap_backtest_engine(
        logger_factory: LoggerFactory,
        instrument: Instrument,
        strategy: Strategy,
        filters: list[Filter] | None = None,
        initial_cash: float = 100_000,
) -> BacktestEngine:

    feature_store = FeatureStore()

    # 1. Build Strategy Orchestrator
    decision_pipeline = DecisionPipeline(
        available_feature_pipelines=feature_store.available_pipelines(),
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
        logger_factory=logger_factory,
        decision_pipeline=decision_pipeline,
        transition_engine=transition_engine,
        portfolio=portfolio,
    )