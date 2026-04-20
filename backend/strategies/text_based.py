from lxml.html import HtmlElement
from core.models import RawCandidate
from core.constants import TEXT_TAGS
from utils.html import xpath_literal, css_attr_literal
from utils.text import normalize_space_text
from strategies.base import LocatorStrategy
from urllib.parse import urlparse

class TextAndAttributeStrategy(LocatorStrategy):
    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        tag = el.tag.lower()
        
        # 1) Role
        role = (el.get("role") or "").strip()
        if role:
            candidates.append(RawCandidate(
                strategy="css:role",
                value=f"{tag}[role={css_attr_literal(role)}]",
                base_score=74,
                intended_stable=True,
                rationale="Role-based locator is readable and semantic."
            ))

        # 2) Text
        text = normalize_space_text(" ".join(el.itertext()))
        if text and tag in TEXT_TAGS:
            exact = text[:50]
            candidates.append(RawCandidate(
                strategy="xpath:text",
                value=f"//{tag}[normalize-space(.)={xpath_literal(exact)}]",
                base_score=76,
                intended_stable=False,
                rationale="Text-based locator helps when attributes are weak."
            ))
            if len(text) > 20:
                partial = text[:20]
                candidates.append(RawCandidate(
                    strategy="xpath:text_contains",
                    value=f"//{tag}[contains(normalize-space(.), {xpath_literal(partial)})]",
                    base_score=70,
                    intended_stable=False,
                    rationale="Partial text match for long labels."
                ))

        # 3) Label association
        if tag in {"input", "textarea", "select"}:
            element_id = el.get("id")
            if element_id:
                labels = root.xpath(f"//label[@for={xpath_literal(element_id)}]")
                if labels:
                    label_text = normalize_space_text(" ".join(labels[0].itertext()))
                    if label_text and len(label_text) > 1:
                        candidates.append(RawCandidate(
                            strategy="xpath:label_for",
                            value=f"//{tag}[@id=//label[normalize-space(.)={xpath_literal(label_text)}]/@for]",
                            base_score=94,
                            intended_stable=True,
                            rationale="Locates input via its associated label."
                        ))

        # 4) Common attributes: type, href, placeholder
        input_type = (el.get("type") or "").strip()
        if input_type:
            candidates.append(RawCandidate(
                strategy="css:type",
                value=f"{tag}[type={css_attr_literal(input_type)}]",
                base_score=58,
                intended_stable=False,
                rationale="Type fallback."
            ))

        href = (el.get("href") or "").strip()
        if tag == "a" and href and href not in {"#", "javascript:void(0)", "javascript:;"}:
            candidates.append(RawCandidate(strategy="css:href", value=f"a[href={css_attr_literal(href)}]", base_score=74, intended_stable=True, rationale="Exact href."))
            path = urlparse(href).path
            if len(path) > 2:
                candidates.append(RawCandidate(strategy="xpath:href_contains", value=f"//a[contains(@href, {xpath_literal(path)})]", base_score=74, intended_stable=False, rationale="Href path contains."))

        placeholder = (el.get("placeholder") or "").strip()
        if placeholder:
            candidates.append(RawCandidate(strategy="css:placeholder", value=f"{tag}[placeholder={css_attr_literal(placeholder)}]", base_score=78, intended_stable=True, rationale="Placeholder match."))

        return candidates
