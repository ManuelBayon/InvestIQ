from ib_insync import IB

from investiq.market_data.adapters.ibkr.connection_config import ConnectionConfig
from investiq.market_data.adapters.ibkr.errors import TWSConnectionError
from investiq.utilities.logger.protocol import LoggerProtocol


class TWSConnection:

    def __init__(
        self,
        logger: LoggerProtocol,
        config: ConnectionConfig = ConnectionConfig.paper(),
    ):
        self._logger = logger
        self._config = config
        self._ib = IB()
        self._connected = False

    def connect(self) -> None:
        if self._connected:
            raise TWSConnectionError("Already connected")

        self._logger.info("Connecting to IBKR...")
        self._ib.connect(
            host=self._config.host,
            port=self._config.port,
            clientId=self._config.client_id,
        )

        if not self._ib.isConnected():
            raise TWSConnectionError("Connection failed")

        self._connected = True
        self._logger.info("Connected to IBKR.")

    def disconnect(self) -> None:
        if not self._connected:
            raise TWSConnectionError("No active connection")

        self._logger.info("Disconnecting from IBKR...")
        self._ib.disconnect()

        if self._ib.isConnected():
            raise TWSConnectionError("Disconnection failed")

        self._connected = False
        self._logger.info("Disconnected from IBKR.")

    @property
    def ib(self) -> IB:
        return self._ib

    @property
    def connected(self) -> bool:
        return self._connected