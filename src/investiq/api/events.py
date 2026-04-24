from dataclasses import dataclass

from investiq.api.features import FeaturePoint


@dataclass(frozen=True)
class FeatureStepEvent:
    computations: dict[
        str, tuple[FeaturePoint, ...]
    ]