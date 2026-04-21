from lxml.html import HtmlElement
from lxml.cssselect import CSSSelector

def xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"

def css_attr_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'

def escape_css_id(element_id: str) -> str:
    # Escape colons and other special characters for CSS selectors
    return element_id.replace(":", "\\:")

def select_count(root: HtmlElement, strategy: str, value: str, internal_xpath: str = "") -> int:
    try:
        # If we have an internal XPath for verification, use it
        if internal_xpath:
            return len(root.xpath(internal_xpath))
            
        if strategy.startswith("xpath:"):
            return len(root.xpath(value))
        
        if strategy.startswith("playwright:"):
            return 0 # Cannot verify pure playwright locators in static HTML without translation
            
        selector = CSSSelector(value)
        return len(selector(root))
    except Exception:
        return 0
