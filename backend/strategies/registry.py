from strategies.test_attr import TestAttributeStrategy
from strategies.identity import IdentityStrategy
from strategies.text_based import TextAndAttributeStrategy
from strategies.structural import StructuralStrategy
from strategies.aria_role import AriaRoleStrategy
from strategies.table import TableStrategy

class StrategyRegistry:
    def __init__(self):
        self.strategies = [
            TestAttributeStrategy(),
            IdentityStrategy(),
            TextAndAttributeStrategy(),
            AriaRoleStrategy(),
            TableStrategy(),
            StructuralStrategy(),
        ]

    def run_all(self, el, root):
        candidates = []
        for strategy in self.strategies:
            candidates.extend(strategy.generate(el, root))
        return candidates
