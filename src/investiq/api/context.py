from dataclasses import dataclass
from datetime import datetime

from investiq.api.instruments import Instrument
from investiq.market_data.domain.enums import BarSize


@dataclass(frozen=True)
class StepContext:
    instrument: Instrument
    bar_size: BarSize
    run_id: str
    step_sequence: int
    event_id: str
    timestamp: datetime