from investiq.core.transition_engine.rules.api import TransitionKey, TransitionRule
from investiq.core.transition_engine.rules.registry import TransitionRuleRegistry

class TransitionRuleFactory:
    @staticmethod
    def create(key: TransitionKey) -> TransitionRule:
        rule_cls = TransitionRuleRegistry.get(key)
        return rule_cls()