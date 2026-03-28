import pandas as pd

from investiq.market_data.ports.data_source import HistoricalDataSource
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.domain.requests.base import RequestSpec


class HistoricalDataLoader:

    def __init__(self, data_source: HistoricalDataSource):
        self._data_source = data_source

    def load(
        self,
        instrument: ProviderInstrumentSpec,
        request: RequestSpec,
    ) -> pd.DataFrame:
        return self._data_source.fetch_historical_data(instrument, request)