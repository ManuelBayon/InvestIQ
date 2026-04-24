from typing import Protocol, ClassVar

import pandas as pd

from investiq.api.types import AtomicAction


class TransitionStrategy(Protocol):
    NAME: ClassVar[str]
    def resolve(
        self,
        timestamp: pd.Timestamp,
        current_position: float,
        target_position: float,
    ) -> list[AtomicAction]:
        ...