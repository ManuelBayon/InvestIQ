from typing import ClassVar

from investiq.export_engine.registries.base import BaseBatchExportRegistry
from investiq.export_engine.registries.config import ExportKey, BatchExportBinding


class BacktestExportRegistry(BaseBatchExportRegistry[ExportKey,object, object, object]
):
    """
    Concrete registry for backtest export pipelines.
    """
    _registry: ClassVar[
        dict[ExportKey, BatchExportBinding[object, object, object]]
    ] = {}

    @classmethod
    def register(
            cls,
            key: ExportKey,
            binding: BatchExportBinding[object, object, object]
    ) -> None:
        if key in cls._registry:
            raise KeyError(f"{key.value} already registered in {cls.__name__}")
        cls._registry[key] = binding

    @classmethod
    def get(
            cls,
            key: ExportKey
    ) -> BatchExportBinding[object, object, object]:
        try:
            return cls._registry[key]
        except KeyError:
            raise KeyError(
                f"{key.value} not registered in {cls.__name__}; "
                f"available={list(cls._registry.keys())}"
            )

    @classmethod
    def available(cls) -> list[ExportKey]:
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()