from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from investiq.api.instruments import Instrument
from investiq.market_data.domain.enums import BarSize


class MarketField(StrEnum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"

@dataclass(frozen=True)
class OHLCV:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

@dataclass(frozen=True)
class MarketDataEvent:
    event_id: str
    instrument: Instrument
    bar_size: BarSize
    timestamp: datetime
    bar: OHLCV
