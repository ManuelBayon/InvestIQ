from collections import defaultdict

from investiq.api.instruments import Instrument
from investiq.api.portfolio import PortfolioView
from investiq.core.portfolio.view import InMemoryPositionBookView
from investiq.utilities.logger.factory import LoggerFactory
from investiq.utilities.logger.protocol import LoggerProtocol
from investiq.core.portfolio.execution.api import PortfolioExecutionStrategy, PortfolioProtocol
from investiq.core.portfolio.execution.factory import PortfolioExecutionFactory
from investiq.api.portfolio import Fill
from investiq.core.transition_engine.enums import FIFOSide
from investiq.core.transition_engine.types import FIFOPosition, FIFOOperation


class Portfolio(PortfolioProtocol):
    """
    Internal mutable runtime portfolio store.
    """
    def __init__(
            self,
            logger_factory: LoggerFactory,
            instrument: Instrument,
            initial_cash : float
    ):
        self._logger_factory = logger_factory
        self._logger : LoggerProtocol =self._logger_factory.child("Portfolio").get()

        self.instrument = instrument

        self._fifo_exec_factory = PortfolioExecutionFactory()

        self.current_position: float = 0.0
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.realized_pnl: float = 0.0
        self.unrealized_pnl: float = 0.0

        self.fifo_queues : dict[FIFOSide, list[FIFOPosition]] = defaultdict(list)
        self.fill_log : list[Fill] = []

        self._fifo_book_view = InMemoryPositionBookView(self.fifo_queues)

    def append_log_entry(self, fill: Fill) -> None:
        self.fill_log.append(fill)

    def apply_operations(self, operations: list[FIFOOperation]) -> None:
        for op in operations:
            strategy: PortfolioExecutionStrategy = self._fifo_exec_factory.create(op_type=op.type)
            fill: Fill = strategy.apply(
                portfolio=self,
                operation=op
            )
            self.append_log_entry(fill)

    def view(self) -> PortfolioView:
        return PortfolioView(
            instrument=self.instrument,
            current_position=self.current_position,
            initial_cash = self.initial_cash,
            cash=self.cash,
            realized_pnl=self.realized_pnl,
            fifo_book=self._fifo_book_view,
            fill_log=tuple(self.fill_log),
        )