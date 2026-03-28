from investiq.execution.transition.enums import CurrentState, Event
from investiq.execution.transition.rules.api import TransitionKey

def compute_key(current_position: float, target_position: float) -> TransitionKey:

    if current_position > 0:
        state = CurrentState.LONG
    elif current_position < 0:
        state = CurrentState.SHORT
    else:
        state = CurrentState.FLAT

    if target_position > 0:
        event = Event.GO_LONG
    elif target_position < 0:
        event = Event.GO_SHORT
    else:
        event = Event.GO_FLAT

    return TransitionKey(state=state, event=event)
