import re
from lxml.html import HtmlElement
from core.models import RawCandidate
from core.constants import DYNAMIC_TOKEN_PATTERN, SAFE_CSS_TOKEN
from utils.html import xpath_literal, escape_css_id
from strategies.base import LocatorStrategy

class IdentityStrategy(LocatorStrategy):
    def _is_dynamic_token(self, value: str) -> bool:
        lower = (value or "").lower()
        if not lower: return False
        if any(token in lower for token in ["react", "ember", "ng-", "auto", "tmp", "hash", "uuid"]):
            return True
        return bool(DYNAMIC_TOKEN_PATTERN.search(lower))

    def _stable_prefix(self, value: str) -> str:
        token = (value or "").strip()
        prefix = re.sub(r"[-_:]?[0-9a-f]{3,}$", "", token, flags=re.I)
        if len(prefix) >= 3 and prefix != token:
            return prefix
        return ""

    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        tag = el.tag.lower()
        
        # ID
        element_id = (el.get("id") or "").strip()
        if element_id:
            if not self._is_dynamic_token(element_id):
                # CSS
                candidates.append(RawCandidate(
                    strategy="css:id",
                    value=f"#{escape_css_id(element_id)}",
                    base_score=96,
                    intended_stable=True,
                    rationale="Unique-looking ID attribute."
                ))
                # XPath
                candidates.append(RawCandidate(
                    strategy="xpath:id",
                    value=f"//{tag}[@id={xpath_literal(element_id)}]",
                    base_score=96,
                    intended_stable=True,
                    rationale="XPath match on ID."
                ))
            else:
                prefix = self._stable_prefix(element_id)
                if prefix:
                    candidates.append(RawCandidate(
                        strategy="css:id_prefix",
                        value=f'{tag}[id^="{prefix}"]',
                        base_score=66,
                        intended_stable=False,
                        rationale="ID appears dynamic; using stable prefix fallback."
                    ))
                    candidates.append(RawCandidate(
                        strategy="xpath:id_prefix",
                        value=f"//{tag}[starts-with(@id, {xpath_literal(prefix)})]",
                        base_score=68,
                        intended_stable=False,
                        rationale="XPath starts-with fallback for dynamic ID."
                    ))

        # Name
        element_name = (el.get("name") or "").strip()
        if element_name:
            if not self._is_dynamic_token(element_name):
                candidates.append(RawCandidate(
                    strategy="css:name",
                    value=f"{tag}[name={xpath_literal(element_name)}]",
                    base_score=88,
                    intended_stable=True,
                    rationale="Stable Name attribute."
                ))
                candidates.append(RawCandidate(
                    strategy="xpath:name",
                    value=f"//{tag}[@name={xpath_literal(element_name)}]",
                    base_score=88,
                    intended_stable=True,
                    rationale="XPath Name match."
                ))
            else:
                prefix = self._stable_prefix(element_name)
                if prefix:
                    candidates.append(RawCandidate(
                        strategy="css:name_prefix",
                        value=f'{tag}[name^="{prefix}"]',
                        base_score=64,
                        intended_stable=False,
                        rationale="Name appears dynamic; using stable prefix fallback."
                    ))

        return candidates
