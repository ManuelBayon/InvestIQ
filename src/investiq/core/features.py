from collections import defaultdict
from collections.abc import Sequence
from typing import Protocol, ClassVar, TypeVar, Final, FrozenSet

from investiq.api.feature import FeatureHistoryReader, FeatureSnapshot
from investiq.core.market_store import MarketStateStore

class FeaturePipeline(Protocol):
    """
    FeaturePipeline protocol.
    """
    NAME: ClassVar[str]
    def reset(self) -> None:
        ...
    def update(
            self,
            *,
            market_store: MarketStateStore,
            feature_store: "FeatureStore",
    ) -> None:
        ...

class InMemoryFeatureHistoryView(FeatureHistoryReader):
    """
    Read-only façade over feature history storage.
    """
    def __init__(self, history: dict[str, list[float]]):
        self._history = history

    def latest(self, name: str) -> float:
        seq = self._history.get(name)
        if not seq:
            raise KeyError(f"No history for feature={name}")
        return seq[-1]

    def window(self, name: str, n: int) -> tuple[float, ...]:
        if n <= 0:
            raise ValueError("n must be > 0")
        seq = self._history.get(name)
        if not seq:
            raise KeyError(f"No history for feature={name}")
        return tuple(seq[-n:])

    def series(self, name: str):
        seq = self._history.get(name)
        if seq is None:
            raise KeyError(f"No history for feature={name}")
        return seq

    def names(self) -> tuple[str, ...]:
        return tuple(self._history.keys())

T = TypeVar('T', bound='FeaturePipeline')


class FeaturePipelineRegistry:

    _registry: dict[str, type[FeaturePipeline]] = {}

    @classmethod
    def register(cls, pipeline_cls: type[FeaturePipeline]) -> None:
        name = getattr(pipeline_cls, "NAME", None)
        if not isinstance(name, str) or not name:
            raise TypeError(f"{pipeline_cls.__name__}.NAME must be a non-empty str")
        if name in cls._registry:
            raise KeyError(f"FeaturePipeline {name} already registered")
        cls._registry[name] = pipeline_cls

    @classmethod
    def get(cls, name: str) -> type[FeaturePipeline]:
        try:
            return cls._registry[name]
        except KeyError as e:
            raise KeyError(
                f"FeaturePipeline {name} not registered. "
                f"Available pipelines: {list(cls._registry)}"
            ) from e

    @classmethod
    def all(cls) -> list[type[FeaturePipeline]]:
        return list(cls._registry.values())

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._registry)


def register_feature_pipeline(cls: type[T]) -> type[T]:
    FeaturePipelineRegistry.register(pipeline_cls=cls)
    return cls

class FeatureStore:
    """
    Internal mutable runtime store for feature values and optional histories.
    """
    def __init__(
            self,
            pipelines: Sequence[FeaturePipeline] | None = None,
            keep_history: bool = True,
    ):
        self.keep_history: Final[bool] = keep_history

        self._values: dict[str, float] = {}
        self._history: dict[str, list[float]] = defaultdict(list)
        self._history_view = InMemoryFeatureHistoryView(self._history)

        if pipelines is None:
            pipeline_items = [(cls_.NAME, cls_()) for cls_ in FeaturePipelineRegistry.all()]
        else:
            pipeline_items = [(p.NAME, p) for p in pipelines]

        names = [name for name, _ in pipeline_items]
        if len(names) != len(set(names)):
            dup = sorted({n for n in names if names.count(n) > 1})
            raise ValueError(f"Duplicate pipeline NAME(s): {dup}")

        self._pipelines: dict[str, FeaturePipeline] = dict(pipeline_items)
        self._pipelines_ready: dict[str, bool] = {name: False for name in self._pipelines}

    def reset(self) -> None:
        self._values.clear()
        self._history.clear()
        for name in self._pipelines_ready:
            self._pipelines_ready[name] = False
        for p in self._pipelines.values():
            p.reset()

    def set_pipeline_ready(self, pipeline: str) -> None:
        self._require_pipeline(pipeline)
        self._pipelines_ready[pipeline] = True

    def pipeline_ready(self, pipeline: str) -> bool:
        self._require_pipeline(pipeline)
        return self._pipelines_ready[pipeline]

    def global_ready(self) -> bool:
        """
        Global readiness: all pipelines warmed up.
        Neutral element: if no pipelines configured, consider store ready.
        """
        return all(self._pipelines_ready.values()) if self._pipelines_ready else True

    def set_value(self, name: str, value: float) -> None:
        v = float(value)
        self._values[name] = v
        if self.keep_history:
            self._history[name].append(v)

    def ingest(self, market_store: MarketStateStore) -> None:
        self._pipelines_ready = {k: False for k in self._pipelines_ready}
        for p in self._pipelines.values():
            p.update(
                market_store=market_store,
                feature_store=self
            )

    def view(self) -> FeatureSnapshot:
        return FeatureSnapshot(
            values=dict(self._values),
            history=self._history_view,
            pipeline_ready=dict(self._pipelines_ready),
            global_ready=self.global_ready(),
        )

    def _require_pipeline(self, name: str) -> None:
        if name not in self._pipelines:
            raise KeyError(
                f"pipeline '{name}' not found in FeatureStore, "
                f"known={sorted(self._pipelines)}"
            )

    def available_pipelines(self) -> FrozenSet[str]:
        return frozenset(self._pipelines.keys())