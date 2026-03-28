from abc import ABC, abstractmethod

from investiq.market_data.domain.enums import AssetType, WhatToShow
from investiq.market_data.domain.instrument_id import InstrumentID


class ProviderInstrumentSpec(ABC):
    asset_type: AssetType
    symbol_id: InstrumentID

    @abstractmethod
    def default_what_to_show(self) -> WhatToShow:
        ...

    @abstractmethod
    def display_name(self) -> str:
        ...