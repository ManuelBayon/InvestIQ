from dataclasses import dataclass

from investiq.market_data.domain.enums import (
    AssetType,
    Exchange,
    WhatToShow,
)
from investiq.market_data.domain.instrument_id import InstrumentID
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec


@dataclass(frozen=True)
class ForexSpec(ProviderInstrumentSpec):
    pair: str
    symbol_id: InstrumentID
    exchange: Exchange = Exchange.IDEALPRO
    asset_type: AssetType = AssetType.FOREX

    def default_what_to_show(self) -> WhatToShow:
        return WhatToShow.MIDPOINT

    def display_name(self) -> str:
        return self.pair