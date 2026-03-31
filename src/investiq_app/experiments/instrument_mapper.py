from investiq.api.instruments import Instrument
from investiq.market_data.domain.enums import AssetType
from investiq.market_data.domain.instrument_id import InstrumentID
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.domain.instruments.cont_future import ContFutureSpec
from investiq.market_data.domain.instruments.forex import ForexSpec
from investiq.market_data.domain.instruments.stock import StockSpec


def to_provider_instrument(instrument: Instrument) -> ProviderInstrumentSpec:
    if instrument.asset_type == AssetType.CONT_FUTURE:
        return ContFutureSpec(
            symbol=instrument.symbol,
            symbol_id=InstrumentID.from_symbol(instrument.symbol),
            exchange=instrument.exchange,
            currency=instrument.currency,
        )

    if instrument.asset_type == AssetType.STOCK:
        return StockSpec(
            symbol=instrument.symbol,
            symbol_id=InstrumentID.from_symbol(instrument.symbol),
            exchange=instrument.exchange,
            currency=instrument.currency,
            asset_type=AssetType.STOCK,
        )

    if instrument.asset_type == AssetType.FOREX:
        return ForexSpec(
            pair=instrument.symbol,
            symbol_id=InstrumentID.from_symbol(instrument.symbol),
            exchange=instrument.exchange,
        )

    raise NotImplementedError(
        f"Unsupported asset type for provider mapping: {instrument.asset_type}"
    )