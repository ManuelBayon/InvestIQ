from dataclasses import dataclass

from investiq.market_data.domain.enums import BarSize, WhatToShow
from investiq.market_data.domain.requests.base import RequestSpec


@dataclass(frozen=True)
class HistoricalRequestSpec(RequestSpec):
    duration: str
    bar_size: BarSize
    what_to_show: WhatToShow