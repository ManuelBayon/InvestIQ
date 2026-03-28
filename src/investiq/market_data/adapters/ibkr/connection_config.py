from dataclasses import dataclass
from enum import Enum, auto


class TradingMode(Enum):
    LIVE = auto()
    PAPER = auto()


@dataclass(frozen=True)
class ConnectionConfig:
    host: str
    port: int
    client_id: int
    mode: TradingMode

    @classmethod
    def paper(cls) -> "ConnectionConfig":
        return cls(
            host="127.0.0.1",
            port=7497,
            client_id=1,
            mode=TradingMode.PAPER,
        )

    @classmethod
    def live(cls) -> "ConnectionConfig":
        return cls(
            host="127.0.0.1",
            port=7496,
            client_id=2,
            mode=TradingMode.LIVE,
        )