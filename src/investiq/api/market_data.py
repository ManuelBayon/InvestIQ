from dataclasses import dataclass
from datetime import datetime

from investiq.market_data import BarSize, WhatToShow


@dataclass
class MarketDataRequest:
    bar_size: BarSize
    duration: str
    what_to_show: WhatToShow = WhatToShow.TRADES
    end_date_time: datetime | str = ""
