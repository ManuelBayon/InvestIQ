from ib_insync import Stock, Future, Forex, ContFuture, Contract

from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.domain.instruments.stock import StockSpec
from investiq.market_data.domain.instruments.future import FutureSpec
from investiq.market_data.domain.instruments.forex import ForexSpec
from investiq.market_data.domain.instruments.cont_future import ContFutureSpec


def to_ibkr_contract(spec: ProviderInstrumentSpec) -> Contract:

    if isinstance(spec, StockSpec):
        return Stock(
            symbol=spec.symbol,
            exchange=spec.exchange.value,
            currency=spec.currency.value,
        )

    if isinstance(spec, FutureSpec):
        return Future(
            symbol=spec.symbol,
            localSymbol=spec.local_symbol,
            exchange=spec.exchange.value,
            currency=spec.currency.value,
        )

    if isinstance(spec, ForexSpec):
        return Forex(
            pair=spec.pair,
            exchange=spec.exchange.value,
        )

    if isinstance(spec, ContFutureSpec):
        return ContFuture(
            symbol=spec.symbol,
            exchange=spec.exchange.value,
            currency=spec.currency.value,
        )

    raise TypeError(f"Unsupported InstrumentSpec: {type(spec)}")