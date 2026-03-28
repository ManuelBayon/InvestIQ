from dataclasses import dataclass

from investiq.market_data.domain.enums import (
    AssetType,
    Exchange,
    Currency,
    WhatToShow,
)
from investiq.market_data.domain.instrument_id import InstrumentID
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec


@dataclass(frozen=True)
class FutureSpec(ProviderInstrumentSpec):
    symbol: str
    local_symbol: str
    symbol_id: InstrumentID
    exchange: Exchange
    currency: Currency
    asset_type: AssetType = AssetType.FUTURE

    def default_what_to_show(self) -> WhatToShow:
        return WhatToShow.MIDPOINT

    def display_name(self) -> str:
        return self.symbol