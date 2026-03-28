import re
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class InstrumentID:
    code: str

    _NORMALIZE_PATTERN = re.compile(r"[^A-Z0-9]")

    @classmethod
    def _normalize(cls, raw: str) -> str:
        if not raw or not isinstance(raw, str):
            raise ValueError("InstrumentID must be created from a non-empty string")
        upper = raw.upper()
        return cls._NORMALIZE_PATTERN.sub("", upper)

    @classmethod
    def from_symbol(cls, raw_symbol: str) -> "InstrumentID":
        return cls(code=cls._normalize(raw_symbol))

    @classmethod
    def from_enum(cls, enum_value: Enum) -> "InstrumentID":
        return cls.from_symbol(enum_value.name)

    def __str__(self) -> str:
        return self.code

    def __hash__(self) -> int:
        return hash(self.code)