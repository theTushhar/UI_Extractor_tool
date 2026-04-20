from strategies.test_attr import TestAttributeStrategy
from strategies.identity import IdentityStrategy
from strategies.text_based import TextAndAttributeStrategy
from strategies.structural import StructuralStrategy

class StrategyRegistry:
    def __init__(self):
        self.strategies = [
            TestAttributeStrategy(),
            IdentityStrategy(),
            TextAndAttributeStrategy(),
            StructuralStrategy(),
        ]

    def run_all(self, el, root):
        candidates = []
        for strategy in self.strategies:
            candidates.extend(strategy.generate(el, root))
        return candidates
