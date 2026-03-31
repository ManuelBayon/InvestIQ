from collections.abc import Iterator
import pandas as pd

from investiq.api.instruments import Instrument
from investiq.api.market import MarketDataEvent, OHLCV
from investiq.market_data.domain.enums import BarSize
from investiq.utilities.logger.protocol import LoggerProtocol

class DataFrameBacktestFeed:

    def __init__(
        self,
        logger: LoggerProtocol,
        df: pd.DataFrame,
        instrument: Instrument,
        bar_size: BarSize,
    ):
        # Store dependencies and input data
        self._logger = logger
        self._df = self._normalize(df)
        self._instrument = instrument
        self._bar_size = bar_size

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:

        # 1. Move timestamp columns to index if needed
        for candidate in ("timestamp", "datetime", "Datetime","date", "time"):
            if candidate in df.columns:
                df = df.set_index(candidate)
                break

        # 2.1 Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex")

        # 2.2 Ensure required columns exist
        required = {"open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        # 2.3 Reject missing timestamps
        if df.index.hasnans:
            raise ValueError("Timestamp index contains NaT")

        # 2.4 Reject duplicate timestamps
        if df.index.has_duplicates:
            duplicates = df.index[df.index.duplicated()]
            sample = duplicates[:5].tolist()
            raise ValueError(f"Duplicate timestamps found: {sample}")

        # 2.5 Reject non-monotonic order
        if not df.index.is_monotonic_increasing:
            raise ValueError("Timestamp index must be monotonic increasing")

        # 3. Return the dataframe
        return df


    def __iter__(self) -> Iterator[MarketDataEvent]:

        # Local reference to the dataframe
        df = self._df
        self._logger.info(f"FEED events={len(df)}")

        for row in df.itertuples():
            ts = row.Index
            o = float(getattr(row, "open"))
            h = float(getattr(row, "high"))
            l = float(getattr(row, "low"))
            c = float(getattr(row, "close"))

            v_raw = getattr(row, "volume", 0.0)
            v = 0.0 if v_raw is None else float(v_raw)

            if not (l <= min(o, c) and max(o, c) <= h):
                raise ValueError(f"Invalid OHLC at {ts}")

            yield MarketDataEvent(
                timestamp=ts,
                bar=OHLCV(open=o, high=h, low=l, close=c, volume=v),
                instrument=self._instrument,
                bar_size=self._bar_size,
            )