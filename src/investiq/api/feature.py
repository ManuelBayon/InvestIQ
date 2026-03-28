from dataclasses import dataclass
from typing import Mapping, Sequence, Protocol


class FeatureHistoryReader(Protocol):
    def latest(self, name: str) -> float: ...
    def window(self, name: str, n: int) -> tuple[float, ...]: ...
    def series(self, name: str) -> Sequence[float]: ...
    def names(self) -> tuple[str, ...]: ...

@dataclass(frozen=True)
class FeatureSnapshot:
    """
    Read-only feature snapshot for runtime consumers.

    - values: latest scalar values
    - history: read-only accessor over feature histories
    - pipeline_ready: per-pipeline readiness at current step
    - global_ready: all pipelines ready
    """
    values: Mapping[str, float]
    history: FeatureHistoryReader
    pipeline_ready: Mapping[str, bool]
    global_ready: bool

    def require(self, name: str) -> float:
        v = self.values.get(name)
        if v is None:
            raise KeyError(f"Missing feature: {name}")
        return v

    def __getitem__(self, name: str) -> float:
        return self.require(name)

    def pipeline_is_ready(self, pipeline: str) -> bool:
        v = self.pipeline_ready.get(pipeline)
        if v is None:
            raise KeyError(f"Unknown pipeline: {pipeline}")
        return bool(v)