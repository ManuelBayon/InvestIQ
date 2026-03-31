from investiq.api.execution import Decision
from investiq.api.portfolio import PortfolioView
from investiq.core.transition_engine.fifo.resolver import FIFOResolver
from investiq.utilities.logger.factory import LoggerFactory
from investiq.core.transition_engine.enums import TransitionType
from investiq.core.transition_engine.types import TransitionLog
from investiq.core.transition_engine.rules.api import TransitionRule
from investiq.core.transition_engine.rules.classifier import compute_key
from investiq.core.transition_engine.rules.factory import TransitionRuleFactory
from investiq.core.transition_engine.strategies.api import TransitionStrategy
from investiq.core.transition_engine.strategies.factory import TransitionStrategyFactory
from investiq.core.transition_engine.types import FIFOOperation, AtomicAction


class TransitionEngine:

    def __init__(
            self,
            logger_factory: LoggerFactory,
    ) -> None:
        self._logger_factory : LoggerFactory = logger_factory
        self._logger = logger_factory.child("TransitionEngine").get()
        self._transition_rule_factory =  TransitionRuleFactory()
        self._transition_strategy_factory = TransitionStrategyFactory()
        self._fifo_resolver = FIFOResolver()
        self._last_resolution : TransitionLog | None = None

    def process(
            self,
            decision: Decision,
            portfolio_view: PortfolioView,
    ) -> list[FIFOOperation]:

        # 1. Build context
        key = compute_key(
            current_position=portfolio_view.current_position,
            target_position=decision.target_position
        )
        # 2. Get the transition_engine rule and resolve transition_engine
        rule: TransitionRule = self._transition_rule_factory.create(key=key)
        transition_type: TransitionType = rule.classify(
            current_position=portfolio_view.current_position,
            target_position=decision.target_position
        )
        # 3. Get the transition_engine strategy and resolve the atomic actions
        strategy : TransitionStrategy = self._transition_strategy_factory.create(
            transition_type=transition_type
        )
        atomic_actions: list[AtomicAction] = strategy.resolve(
            current_position=portfolio_view.current_position,
            target_position=decision.target_position,
            timestamp=decision.timestamp
        )
        # 4. Resolve fifo operations
        fifo_operations: list[FIFOOperation] = self._fifo_resolver.resolve(
            actions=atomic_actions,
            position_book=portfolio_view.fifo_book,
            execution_price=decision.execution_price
        )
        # 5.Build Audit Log
        log_entry = TransitionLog(
            state=key.state,
            event=key.event,
            current_position=portfolio_view.current_position,
            target_position=decision.target_position,
            rule_name=rule.NAME,
            transition_strategy=strategy.NAME,
            transition_type=transition_type.name,
            actions_len=len(atomic_actions),
            fifo_ops_len=len(fifo_operations)
        )
        if atomic_actions:
            self._log_operation(
                log=log_entry,
                atomic_actions=atomic_actions,
                fifo_operations=fifo_operations
            )
            self._last_resolution = log_entry

        return fifo_operations

    def _format_atomic_actions(self, actions: list[AtomicAction]) -> str:
        if not actions:
            return "[]"
        parts = [
            f"{action.type}(qty={action.quantity:.2f}, timestamp={action.timestamp})"
            for action in actions
        ]
        return "[" + ", ".join(parts) + "]"

    def _format_fifo_operations(self, operations: list[FIFOOperation]) -> str:
        if not operations:
            return "[]"

        parts = []
        for operation in operations:
            linked=f"link={operation.linked_position_id}" if operation.linked_position_id else "None"
            msg = f"{operation.type}({operation.side}, qty={operation.quantity:.2f}, price={operation.execution_price}, linked_position={linked})"
            parts.append(msg)

        return "[" + ", ".join(parts) + "]"

    def _log_operation(
            self,
            log : TransitionLog,
            atomic_actions: list[AtomicAction],
            fifo_operations: list[FIFOOperation]
    ) -> None:
        self._logger.debug(
            (
                "\ncurrent=%.2f, target=%.2f"
                "\nstate=%s, event=%s"
                "\nrule=%s, transition_strategy=%s"
                "\ntransition_type=%s"
                "\natomic_actions=%s"
                "\nfifo_operations=%s"
                "\n"
            ),
            log.current_position,
            log.target_position,
            log.state.name,
            log.event.name,
            log.rule_name,
            log.transition_strategy,
            log.transition_type,
            self._format_atomic_actions(atomic_actions),
            self._format_fifo_operations(fifo_operations)
        )