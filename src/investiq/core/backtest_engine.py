import time

import pandas as pd

from investiq.api.backtest import BacktestView, BacktestInput
from investiq.api.execution import RunResult
from investiq.api.market import MarketDataEvent
from investiq.api.errors import BacktestInvariantError
from investiq.core.features import FeatureStore
from investiq.core.market_store import MarketStateStore
from investiq.execution.transition.enums import FIFOSide
from investiq.utilities.logger.factory import LoggerFactory
from investiq.execution.portfolio.portfolio import Portfolio
from investiq.execution.transition.transition_engine import TransitionEngine
from investiq.core.decision_pipeline import DecisionPipeline
from investiq.runs.audit import StepRecord
from investiq_app.config import backtest_config


class BacktestEngine:

    def __init__(
            self,
            logger_factory: LoggerFactory,
            decision_pipeline: DecisionPipeline,
            transition_engine: TransitionEngine,
            portfolio: Portfolio,
            market_store: MarketStateStore | None = None,
            feature_store: FeatureStore | None = None,
    ):
        self._logger = logger_factory.child("BacktestEngine").get()
        self._decision_pipeline = decision_pipeline
        self._transition_engine = transition_engine
        self._portfolio = portfolio
        self._market_store = market_store or MarketStateStore()
        self._feature_store = feature_store or FeatureStore()

    def _build_view(self) -> BacktestView:
        return BacktestView(
            market_view=self._market_store.view(),
            features_view=self._feature_store.view(),
            portfolio_view=self._portfolio.view(),
        )

    def _build_metrics(self) -> dict[str, float]:
        portfolio_view = self._portfolio.view()
        market_view = self._market_store.view()

        last_price = market_view.bar.close

        unrealized_pnl = self._compute_unrealized_pnl(market_price=last_price)
        net_liquidation_value = portfolio_view.cash + unrealized_pnl

        return {
            "Initial Cash" : float(self._portfolio.initial_cash),
            "Final Cash": float(portfolio_view.cash),
            "Final Position": float(portfolio_view.current_position),
            "Net Liquidation Value": float(net_liquidation_value),
            "Realized PnL": float(portfolio_view.realized_pnl),
            "Unrealized PnL": float(unrealized_pnl),
        }

    def _compute_unrealized_pnl(self, market_price: float) -> float:
        total = 0.0

        for side, positions in self._portfolio.fifo_queues.items():
            for pos in positions:
                if not pos.is_active:
                    continue

                direction = 1.0 if pos.side == FIFOSide.LONG else -1.0
                pnl = (
                    (market_price - pos.price)
                    * pos.quantity
                    * self._portfolio.instrument.contract_multiplier
                    * direction
                )
                total += pnl

        return total


    def step(self, event: MarketDataEvent) -> StepRecord:

        # 1. Update runtime stores
        self._market_store.ingest(event=event)
        self._feature_store.ingest(market_store=self._market_store)

        # 2. Build pre-trade read-only view
        view_before: BacktestView = self._build_view()

        # 3. Run decision pipeline
        decision = self._decision_pipeline.run(view=view_before)

        # 5. Pure transition computation
        ops = self._transition_engine.process(
            decision=decision,
            portfolio_view=view_before.portfolio_view,
        )

        # 6. Mutate portfolio
        self._portfolio.apply_operations(ops)

        # 7.Step record
        view_after = self._build_view()
        return StepRecord(
            timestamp=view_before.market_view.timestamp,
            event=event,
            decision=decision,
            transition_result=ops,
            portfolio_view=view_after.portfolio_view,
            diagnostics={
                "decision":decision.diagnostics,
            },
        )

    def run(self, bt_input: BacktestInput) -> RunResult:

        # 1. Initialization
        start_time = time.perf_counter()
        first_ts: pd.Timestamp | None = None
        last_ts: pd.Timestamp | None = None
        event_count: int = 0

        # 2. Main loop over the events
        self._logger.info("Running ...")
        for event in bt_input.events:
            event_count += 1
            step_record = self.step(event=event)
            if first_ts is None:
                first_ts = step_record.timestamp
            last_ts = step_record.timestamp

        # 3. Invariants
        if first_ts is None or last_ts is None:
            raise BacktestInvariantError("No events provided")

        # 4. Final State
        final_view = self._build_view()
        end_time = time.perf_counter()
        runtime_duration = end_time - start_time
        self._logger.info("Run success.")

        # 5. Export run artefact
        return RunResult(
            run_id="run_id",
            instrument=bt_input.instrument,
            start=first_ts,
            end=last_ts,
            event_count=event_count,
            runtime_duration=runtime_duration,
            metrics=self._build_metrics(),
            fill_log=final_view.portfolio_view.fill_log,
            diagnostics={}
        )