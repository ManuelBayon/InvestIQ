from investiq.execution.transition.rules.api import TransitionKey, TransitionRule
from investiq.execution.transition.rules.registry import TransitionRuleRegistry

class TransitionRuleFactory:
    @staticmethod
    def create(key: TransitionKey) -> TransitionRule:
        rule_cls = TransitionRuleRegistry.get(key)
        return rule_cls()