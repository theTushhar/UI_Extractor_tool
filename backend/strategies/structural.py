from lxml.html import HtmlElement
from core.models import RawCandidate
from core.constants import TEST_ID_KEYS, DYNAMIC_TOKEN_PATTERN
from utils.html import xpath_literal
from strategies.base import LocatorStrategy

class StructuralStrategy(LocatorStrategy):
    def _is_dynamic_token(self, value: str) -> bool:
        lower = (value or "").lower()
        return bool(DYNAMIC_TOKEN_PATTERN.search(lower))

    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        tag = el.tag.lower()
        tree = el.getroottree()
        
        # 1) Relative Anchor
        for ancestor in el.iterancestors():
            anc_tag = ancestor.tag.lower() if isinstance(ancestor.tag, str) else ""
            if not anc_tag: continue
            
            anc_id = (ancestor.get("id") or "").strip()
            if anc_id and not self._is_dynamic_token(anc_id):
                candidates.append(RawCandidate(
                    strategy="xpath:relative_ancestor",
                    value=f"//{anc_tag}[@id={xpath_literal(anc_id)}]//{tag}",
                    base_score=54,
                    intended_stable=False,
                    rationale="Relative locator anchored by stable ancestor id."
                ))
                break
                
            for key in TEST_ID_KEYS:
                val = (ancestor.get(key) or "").strip()
                if val:
                    candidates.append(RawCandidate(
                        strategy="xpath:relative_ancestor",
                        value=f"//{anc_tag}[@{key}={xpath_literal(val)}]//{tag}",
                        base_score=56,
                        intended_stable=False,
                        rationale=f"Relative locator anchored by ancestor {key}."
                    ))
                    break
            else: continue
            break

        # 2) Absolute Path
        candidates.append(RawCandidate(
            strategy="xpath:absolute",
            value=tree.getpath(el),
            base_score=40,
            intended_stable=False,
            rationale="Absolute XPath (fragile fallback)."
        ))

        return candidates
