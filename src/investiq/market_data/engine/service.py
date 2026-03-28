import pandas as pd

from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.domain.requests.base import RequestSpec
from investiq.market_data.engine.loader import HistoricalDataLoader
from investiq.market_data.ports.data_source import HistoricalDataSource
from investiq.utilities.logger.protocol import LoggerProtocol


class HistoricalDataService:

    def __init__(
        self,
        logger: LoggerProtocol,
        data_source: HistoricalDataSource,
    ):
        self._logger = logger
        self._data_source = data_source
        self._loader = HistoricalDataLoader(data_source)

    def load(
        self,
        instrument: ProviderInstrumentSpec,
        request: RequestSpec,
    ) -> pd.DataFrame:

        self._logger.debug("Connecting data source...")
        self._data_source.connect()

        try:
            df = self._loader.load(instrument, request)
        finally:
            self._logger.debug("Disconnecting data source...")
            self._data_source.disconnect()

        if "date" in df.columns:
            df = df.rename(columns={"date": "timestamp"})

        return df