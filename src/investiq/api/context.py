from dataclasses import dataclass
from datetime import datetime

from investiq.api.instruments import Instrument
from investiq.market_data.domain.enums import BarSize


@dataclass(frozen=True)
class StepContext:
    run_id: str
    instrument: Instrument
    bar_size: BarSize
    event_id: str
    timestamp: datetime