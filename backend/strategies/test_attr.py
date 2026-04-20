from lxml.html import HtmlElement
from core.models import RawCandidate
from core.constants import TEST_ID_KEYS, SAFE_CSS_TOKEN
from utils.html import xpath_literal, css_attr_literal
from strategies.base import LocatorStrategy

class TestAttributeStrategy(LocatorStrategy):
    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        tag = el.tag.lower()
        for key in TEST_ID_KEYS:
            value = (el.get(key) or "").strip()
            if not value:
                continue
            
            # CSS
            if SAFE_CSS_TOKEN.match(value):
                candidates.append(RawCandidate(
                    strategy="css:test_attr",
                    value=f"{tag}[{key}={value}]",
                    base_score=100,
                    intended_stable=True,
                    rationale=f"High-priority test attribute {key}."
                ))
            else:
                candidates.append(RawCandidate(
                    strategy="css:test_attr",
                    value=f"{tag}[{key}={css_attr_literal(value)}]",
                    base_score=98,
                    intended_stable=True,
                    rationale=f"High-priority test attribute {key} (quoted)."
                ))
            
            # XPath
            candidates.append(RawCandidate(
                strategy="xpath:test_attr",
                value=f"//{tag}[@{key}={xpath_literal(value)}]",
                base_score=100,
                intended_stable=True,
                rationale=f"XPath match on test attribute {key}."
            ))
        return candidates
