from lxml.html import HtmlElement
from core.models import RawCandidate
from utils.html import xpath_literal, css_attr_literal
from utils.text import normalize_space_text
from strategies.base import LocatorStrategy

class AriaRoleStrategy(LocatorStrategy):
    """
    Generates locators based on ARIA roles and accessible names, 
    matching Playwright's getByRole patterns.
    """
    
    IMPLICIT_ROLES = {
        "button": "button",
        "a": "link",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
        "img": "img",
        "input": {
            "button": "button",
            "submit": "button",
            "reset": "button",
            "checkbox": "checkbox",
            "radio": "radio",
            "image": "button",
            "default": "textbox"
        },
        "textarea": "textbox",
        "select": "combobox",
    }

    def _get_role(self, el: HtmlElement) -> str:
        explicit_role = (el.get("role") or "").strip()
        if explicit_role:
            return explicit_role
            
        tag = el.tag.lower()
        role_map = self.IMPLICIT_ROLES.get(tag)
        
        if isinstance(role_map, dict):
            input_type = (el.get("type") or "default").lower()
            return role_map.get(input_type, role_map["default"])
            
        if tag == "a" and not el.get("href"):
            return None # <a> without href is not a link
            
        return role_map

    def _get_accessible_name(self, el: HtmlElement, root: HtmlElement) -> str:
        # 1) aria-label
        aria_label = (el.get("aria-label") or "").strip()
        if aria_label:
            return aria_label
            
        # 2) Label association
        element_id = el.get("id")
        if element_id:
            labels = root.xpath(f"//label[@for={xpath_literal(element_id)}]")
            if labels:
                name = normalize_space_text(" ".join(labels[0].itertext()))
                if name: return name
        
        # 3) Nested label
        parent_labels = el.xpath("ancestor::label[1]")
        if parent_labels:
            name = normalize_space_text(" ".join(parent_labels[0].itertext()))
            if name: return name

        # 4) alt text for images or buttons with images
        alt = (el.get("alt") or "").strip()
        if alt:
            return alt
            
        # 5) placeholder
        placeholder = (el.get("placeholder") or "").strip()
        if placeholder:
            return placeholder

        # 6) Inner text for semantic tags
        if el.tag.lower() in {"button", "a", "h1", "h2", "h3", "h4", "h5", "h6"}:
            name = normalize_space_text(" ".join(el.itertext()))
            if name: return name
            
        return ""

    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        role = self._get_role(el)
        if not role:
            return candidates

        name = self._get_accessible_name(el, root)
        tag = el.tag.lower()
        
        # Priority 1: Role + Name (Very stable)
        if name and len(name) < 100:
            # We construct a simple XPath for verification: //tag[@role='role' and contains(normalize-space(.), 'name')]
            # This is a simplification but enough for basic verification
            xpath_val = f"//{tag}[@role={xpath_literal(role)} and normalize-space(.)={xpath_literal(name)}]"
            if not el.get("role"): # If role is implicit
                xpath_val = f"//{tag}[normalize-space(.)={xpath_literal(name)}]"

            candidates.append(RawCandidate(
                strategy="playwright:get_by_role",
                value=f"page.get_by_role({xpath_literal(role)}, name={xpath_literal(name)})",
                internal_xpath=xpath_val,
                base_score=95,
                intended_stable=True,
                rationale=f"Semantic locator using role '{role}' and accessible name '{name}'."
            ))
            
        # Priority 2: Role only
        candidates.append(RawCandidate(
            strategy="playwright:get_by_role_generic",
            value=f"page.get_by_role({xpath_literal(role)})",
            internal_xpath=f"//{tag}[@role={xpath_literal(role)}]" if el.get("role") else f"//{tag}",
            base_score=70,
            intended_stable=False,
            rationale=f"Semantic locator using role '{role}'."
        ))

        return candidates
