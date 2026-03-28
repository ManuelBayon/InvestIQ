from abc import ABC
from dataclasses import dataclass
from datetime import datetime

from investiq.market_data.domain.enums import BarSize, WhatToShow


@dataclass
class MarketDataRequest:
    bar_size: BarSize
    duration: str
    what_to_show: WhatToShow = WhatToShow.TRADES
    end_date_time: datetime | str = ""

@dataclass(frozen=True)
class RequestSpec(ABC):
    duration: str
    bar_size: BarSize = BarSize.ONE_DAY
    what_to_show: WhatToShow = WhatToShow.MIDPOINT