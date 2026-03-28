from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from investiq.execution.transition.enums import CurrentState, Event, TransitionType


@dataclass(frozen=True)
class TransitionKey:
    state: CurrentState
    event: Event

class TransitionRule(ABC):
    """
    A rule classifies a (current_position, target_position) into a TransitionType,
    for a given (state, event) key.
    """
    KEY: ClassVar[TransitionKey]
    NAME: ClassVar[str]

    @abstractmethod
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        ...