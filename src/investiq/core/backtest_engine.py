import time
from typing import List

import pandas as pd

from investiq.api.backtest import BacktestView, BacktestInput, RunId
from investiq.api.context import StepContext
from investiq.api.enums import FIFOSide
from investiq.api.execution import RunResult
from investiq.api.market import MarketDataEvent
from investiq.api.errors import BacktestInvariantError
from investiq.core.features_store import FeatureStore
from investiq.core.market_store import MarketStateStore
from investiq.core.transition_resolver import resolve_transition
from investiq.utilities.logger.factory import LoggerFactory
from investiq.core.decision_pipeline import DecisionPipeline
from investiq.runs.audit import StepRecord


class BacktestEngine:

    def __init__(
            self,
            run_id: RunId,
            logger_factory: LoggerFactory,
            market_store: MarketStateStore,
            feature_store: FeatureStore,
            decision_pipeline: DecisionPipeline,
            portfolio: Portfolio,
    ):
        self._logger = logger_factory.child("BacktestEngine").get()

        self._run_id: RunId = run_id
        self._next_step_sequence: int = 0

        self._market_store = market_store
        self._feature_store = feature_store
        self._decision_pipeline = decision_pipeline
        self._portfolio = portfolio

    def _build_view(self) -> BacktestView:
        return BacktestView(
            market_view=self._market_store.view,
            features_view=self._feature_store.view,
            portfolio_view=self._portfolio.view,
        )

    def _build_metrics(self) -> dict[str, float]:
        portfolio_view = self._portfolio.view
        market_view = self._market_store.view
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

    def _build_step_context(self, event: MarketDataEvent) -> StepContext:
        return StepContext(
            run_id=self._run_id,
            instrument=event.instrument,
            bar_size=event.bar_size,
            timestamp=event.timestamp,
        )

    def step(self, event: MarketDataEvent) -> StepRecord:

        # . Build current step context
        step_context = self._build_step_context(event)

        # . Update market store
        self._market_store.ingest(event=event)

        # . Update feature store
        feature_layer_step_record = self._feature_store.update(
            context=step_context,
            market_view=self._market_store.view,
        )

        # . Build pre-trade backtest view
        view_before: BacktestView = self._build_view()

        # . Run decision pipeline
        decision = self._decision_pipeline.run(bt_view=view_before)

        # . Resolve atomic actions from decision
        atomic_actions = resolve_transition(
            decision=decision,
            portfolio_view=view_before.portfolio_view,
        )

        ################   REFACTOR UNDER THIS LINE   ################

        # . Execution Instruction Resolver


        # . Fill simulator


        # . Accountability (portfolio)


        ################   REFACTOR ABOVE THIS LINE   ################

        # . Return step record
        view_after = self._build_view()
        return StepRecord(
            ...
        )

    def run(self, bt_input: BacktestInput) -> RunResult:

        # 1. Initialization
        start_time = time.perf_counter()
        first_ts: pd.Timestamp | None = None
        last_ts: pd.Timestamp | None = None
        step_records: List[StepRecord] = []

        # 2. Main loop over the events
        for event in bt_input.events:
            step_record = self.step(event=event)
            step_records.append(step_record)
            if first_ts is None:
                first_ts = step_record.timestamp
            last_ts = step_record.timestamp
            self._next_step_sequence+=1

        # 3. Invariants
        if first_ts is None or last_ts is None:
            raise BacktestInvariantError("No events provided")

        # 4. Final State
        final_view = self._build_view()
        stop_time = time.perf_counter()
        runtime_duration = stop_time - start_time

        # 5. Export run artefact
        return RunResult(
            run_id=RunId("#RunId"),
            instrument=bt_input.instrument,
            start=first_ts,
            end=last_ts,
            event_count=self._next_step_sequence,
            runtime_duration=runtime_duration,
            metrics=self._build_metrics(),
            fill_log=final_view.portfolio_view.fill_log,
        )