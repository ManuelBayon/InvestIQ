from enum import Enum, auto


class AssetType(Enum):
    FUTURE = auto()
    CONT_FUTURE = auto()
    STOCK = auto()
    FOREX = auto()
    OPTION = auto()


class WhatToShow(str, Enum):
    TRADES = "TRADES"
    MIDPOINT = "MIDPOINT"


class Currency(str, Enum):
    USD = "USD"


class Exchange(str, Enum):
    CME = "CME"
    NYSE = "NYSE"
    IDEALPRO = "IDEALPRO"
    SMART = "SMART"


class BarSize(str, Enum):
    """
    barSizeSetting (str) – Time period of one bar. Must be one of:
    ‘1 secs’, ‘5 secs’, ‘10 secs’ 15 secs’, ‘30 secs’,
    ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’, ‘10 mins’, ‘15 mins’, ‘20 mins’, ‘30 mins’,
    ‘1 hour’, ‘2 hours’, ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’, ‘1 month’.
    """
    ONE_MINUTE = "1 min"
    FIVE_MINUTES = "5 mins"
    TEN_MINUTES = "10 mins"
    FIFTEEN_MINUTES = "15 mins"
    THIRTY_MINUTES = "30 mins"
    ONE_HOUR = "1 hour"
    TWO_HOURS = "2 hours"
    FOUR_HOURS = "4 hours"
    ONE_DAY = "1 day"
    ONE_WEEK = "1 week"
    ONE_MONTH = "1 month"