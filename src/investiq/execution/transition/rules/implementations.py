from investiq.execution.transition.enums import CurrentState, Event, TransitionType
from investiq.execution.transition.rules.api import TransitionKey, TransitionRule
from investiq.execution.transition.rules.registry import register_rule


@register_rule()
class NoOperationRule(TransitionRule):
    KEY = TransitionKey(CurrentState.FLAT, Event.GO_FLAT)
    NAME = "NoOperationRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.NO_OP

@register_rule()
class OpenLongFromFlatRule(TransitionRule):
    KEY = TransitionKey(CurrentState.FLAT, Event.GO_LONG)
    NAME = "OpenLongFromFlatRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.OPEN_LONG

@register_rule()
class OpenShortFromFlatRule(TransitionRule):
    KEY = TransitionKey(CurrentState.FLAT, Event.GO_SHORT)
    NAME = "OpenShortFromFlatRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.OPEN_SHORT

@register_rule()
class CloseLongFromLongRule(TransitionRule):
    KEY = TransitionKey(CurrentState.LONG, Event.GO_FLAT)
    NAME = "CloseLongFromLongRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.CLOSE_LONG

@register_rule()
class CloseShortFromShortRule(TransitionRule):
    KEY = TransitionKey(CurrentState.SHORT, Event.GO_FLAT)
    NAME = "CloseShortFromShortRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.CLOSE_SHORT

@register_rule()
class AdjustLongFromLongRule(TransitionRule):
    KEY = TransitionKey(CurrentState.LONG, Event.GO_LONG)
    NAME = "AdjustLongFromLongRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        if target_position == current_position:
            return TransitionType.NO_OP
        if target_position > current_position:
            return TransitionType.INCREASE_LONG
        return TransitionType.REDUCE_LONG

@register_rule()
class AdjustShortFromShortRule(TransitionRule):
    KEY = TransitionKey(CurrentState.SHORT, Event.GO_SHORT)
    NAME = "AdjustShortFromShortRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        if target_position == current_position:
            return TransitionType.NO_OP
        if abs(target_position) > abs(current_position):
            return TransitionType.INCREASE_SHORT
        return TransitionType.REDUCE_SHORT

@register_rule()
class ReversalToShortFromLongRule(TransitionRule):
    KEY = TransitionKey(CurrentState.LONG, Event.GO_SHORT)
    NAME = "ReversalToShortFromLongRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.REVERSAL_TO_SHORT

@register_rule()
class ReversalToLongFromShortRule(TransitionRule):
    KEY = TransitionKey(CurrentState.SHORT, Event.GO_LONG)
    NAME = "ReversalToLongFromShortRule"
    def classify(self, current_position: float, target_position: float) -> TransitionType:
        return TransitionType.REVERSAL_TO_LONG
