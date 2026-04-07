from dataclasses import dataclass

from investiq.market_data.domain.enums import AssetType, Exchange, Currency


@dataclass(frozen=True)
class Instrument:
    asset_type: AssetType
    symbol: str
    exchange: Exchange
    tick_size: float
    lot_size: float
    contract_multiplier: float
    currency: Currency

class InstrumentFactory:
    @staticmethod
    def cont_future(
            symbol: str,
            exchange: Exchange = Exchange.CME,
            tick_size: float = 0.25,
            lot_size: float = 1.0,
            contract_multiplier: float = 2.0,
            currency: Currency = Currency.USD,
    ) -> Instrument:
        return Instrument(
            asset_type=AssetType.CONT_FUTURE,
            symbol=symbol,
            exchange=exchange,
            tick_size=tick_size,
            lot_size=lot_size,
            contract_multiplier=contract_multiplier,
            currency=currency,
        )

    @staticmethod
    def stock(
            symbol: str,
            exchange: Exchange = Exchange.SMART,
            tick_size: float = 0.01,
            lot_size: float = 1.0,
            contract_multiplier: float = 1.0,
            currency: Currency = Currency.USD,
    ) -> Instrument:
        return Instrument(
            asset_type=AssetType.STOCK,
            symbol=symbol,
            exchange=exchange,
            tick_size=tick_size,
            lot_size=lot_size,
            contract_multiplier=contract_multiplier,
            currency=currency,
        )

    @staticmethod
    def forex(
            symbol: str,
            exchange: Exchange = Exchange.IDEALPRO,
            tick_size: float = 0.0001,
            lot_size: float = 1.0,
            contract_multiplier: float = 1.0,
            currency: Currency = Currency.USD,
    ) -> Instrument:
        return Instrument(
            asset_type=AssetType.FOREX,
            symbol=symbol,
            exchange=exchange,
            tick_size=tick_size,
            lot_size=lot_size,
            contract_multiplier=contract_multiplier,
            currency=currency,
        )