import logging
from typing import Any

from investiq.utilities.logger.access import get_contextual_logger


class LoggerFactory:

    def __init__(
            self,
            base_name: str | None = None,
            engine_type: str | None = None,
            run_id: str | None = None,
            **global_extras: Any
    ) -> None:
        """
           Args:
               engine_type: Context type (e.g., "Backtest", "Live", "Simulation").
               run_id: Unique identifier for correlation across logs.
               **global_extras: Arbitrary additional fields (e.g., strategy_id, account_id).
        """
        self._base_name = base_name
        self._engine_type = engine_type
        self._run_id = run_id
        self._global_extras = global_extras

    @staticmethod
    def _compose_name(parent: str, child: str) -> str:
        """Compose hierarchical logger names safely."""
        if not parent:
            return child
        if not child:
            return parent
        return f"{parent}.{child}"

    def get(
            self,
            **local_extras: Any
    ) -> logging.LoggerAdapter[logging.Logger]:

        context = self._global_extras | local_extras

        return get_contextual_logger(
            child_name=self._base_name,
            engine_type=self._engine_type,
            run_id=self._run_id,
            **context
        )


    def child(
            self,
            child_name: str,
            **extras: Any
    ) -> "LoggerFactory":
        name = self._compose_name(self._base_name, child_name)
        return LoggerFactory(
            base_name=name,
            engine_type=self._engine_type,
            run_id=self._run_id,
            **(self._global_extras | extras)
        )