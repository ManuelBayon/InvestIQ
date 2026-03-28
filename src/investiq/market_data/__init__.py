# ===== DOMAIN =====

from .domain.instrument_id import InstrumentID
from .domain.enums import (
    AssetType,
    Exchange,
    Currency,
    BarSize,
    WhatToShow,
)

from .domain.instruments.stock import StockSpec
from .domain.instruments.future import FutureSpec
from .domain.instruments.cont_future import ContFutureSpec
from .domain.instruments.forex import ForexSpec

from .domain.requests.base import RequestSpec
from .domain.requests.historical import HistoricalRequestSpec


# ===== ENGINE =====

from .engine.service import HistoricalDataService


# ===== PORTS =====

from .ports.data_source import HistoricalDataSource


# ===== ADAPTERS (IBKR) =====

from .adapters.ibkr.connection_config import ConnectionConfig
from .adapters.ibkr.tws_connection import TWSConnection
from .adapters.ibkr.data_source import IBKRHistoricalDataSource


# ===== FEEDS =====

from .feeds.dataframe_feed import DataFrameBacktestFeed


__all__ = [
    # domain
    "InstrumentID",
    "AssetType",
    "Exchange",
    "Currency",
    "BarSize",
    "WhatToShow",
    "StockSpec",
    "FutureSpec",
    "ContFutureSpec",
    "ForexSpec",
    "RequestSpec",
    "HistoricalRequestSpec",

    # engine
    "HistoricalDataService",

    # ports
    "HistoricalDataSource",

    # adapters
    "ConnectionConfig",
    "TWSConnection",
    "IBKRHistoricalDataSource",

    # feeds
    "DataFrameBacktestFeed",
]