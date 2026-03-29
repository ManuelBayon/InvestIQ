import pandas as pd

from investiq.market_data.ports.data_source import HistoricalDataSource
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.domain.requests.base import RequestSpec
from investiq.market_data.adapters.ibkr.tws_connection import TWSConnection
from investiq.market_data.adapters.ibkr.request_builder import build_ibkr_request
from investiq.market_data.adapters.ibkr.errors import TWSConnectionError
from investiq.utilities.logger.protocol import LoggerProtocol


class IBKRHistoricalDataSource(HistoricalDataSource):

    def __init__(
        self,
        logger: LoggerProtocol,
        connection: TWSConnection,
    ):
        self._logger = logger
        self._connection = connection

    def connect(self) -> None:
        self._connection.connect()

    def disconnect(self) -> None:
        self._connection.disconnect()

    def fetch_historical_data(
        self,
        instrument: ProviderInstrumentSpec,
        request: RequestSpec,
    ) -> pd.DataFrame:

        query = build_ibkr_request(instrument, request)

        try:
            self._logger.info("Fetching historical data from IBKR...")
            result = self._connection.ib.reqHistoricalData(**query)
        except Exception as e:
            raise TWSConnectionError(f"IBKR request failed: {e}") from e
        self._logger.info("Historical data loaded.")
        return pd.DataFrame(result)