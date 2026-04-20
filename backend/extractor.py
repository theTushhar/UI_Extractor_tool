import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse
from lxml import etree, html
from lxml.cssselect import CSSSelector
from lxml.html import HtmlElement
from mhtml_parser import clean_mhtml_to_html


INTERESTING_TAGS = {
    "input",
    "textarea",
    "select",
    "button",
    "a",
    "img",
    "label",
    "option",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "th",
    "fieldset",
}

SAFE_CSS_TOKEN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
DYNAMIC_TOKEN_PATTERN = re.compile(r"(\d{3,}|[a-f0-9]{8,})$", re.I)
TEXT_TAGS = {"button", "a", "label", "h1", "h2", "h3", "h4", "h5", "h6", "th", "legend"}
TEST_ID_KEYS = ["data-testid", "data-test", "data-cy", "data-qa"]


@dataclass
class RawCandidate:
    strategy: str
    value: str
    base_score: int
    intended_stable: bool
    rationale: str


@dataclass
class Locator:
    strategy: str
    value: str
    unique: bool
    stable: bool
    score: int
    risk_level: str
    rationale: str


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"


def _css_attr_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _escape_css_id(element_id: str) -> str:
    # Escape colons and other special characters for CSS selectors
    return element_id.replace(":", "\\:")


def _normalize_space_text(text: str) -> str:
    return " ".join(text.split())


def _clean_name(name: str) -> str:
    if not name:
        return ""
    # 1) Handle CamelCase and kebab-case
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    name = name.replace("-", " ").replace("_", " ").replace(":", " ")
    
    # 2) Remove common technical suffixes/prefixes if they are redundant
    name = re.sub(r"\b(btn|button|lnk|link|txt|text|id|input|select|form)\b", "", name, flags=re.I)
    
    # 3) Title Case and strip
    words = [w.capitalize() for w in name.split() if w]
    cleaned = " ".join(words)
    
    # 4) Limit length
    return cleaned[:80].strip()


def _is_dynamic_token(value: str) -> bool:
    lower = (value or "").lower()
    if not lower:
        return False
    if any(token in lower for token in ["react", "ember", "ng-", "auto", "tmp", "hash", "uuid"]):
        return True
    return bool(DYNAMIC_TOKEN_PATTERN.search(lower))


def _stable_prefix(value: str) -> str:
    token = (value or "").strip()
    prefix = re.sub(r"[-_:]?[0-9a-f]{3,}$", "", token, flags=re.I)
    if len(prefix) >= 3 and prefix != token:
        return prefix
    return ""


def _risk_level(strategy: str, unique: bool, stable: bool) -> str:
    if not unique:
        return "high"
    if strategy in {"xpath:absolute", "xpath:position"}:
        return "high"
    if strategy in {"css:class", "xpath:class", "xpath:text", "xpath:id_prefix", "css:id_prefix"}:
        return "medium"
    if stable:
        return "low"
    return "medium"


def _score(base: int, unique: bool, stable: bool, risk: str) -> int:
    score = int(base * 0.6) + (25 if unique else 0) + (15 if stable else 0)
    if risk == "medium":
        score -= 12
    elif risk == "high":
        score -= 24
    return max(1, min(100, score))


def _is_visible_candidate(el: HtmlElement) -> bool:
    if not isinstance(el.tag, str):
        return False
    if el.tag.lower() in {"script", "style", "noscript", "meta", "link", "title"}:
        return False
    if el.get("hidden") is not None:
        return False
    return True


def _infer_type_mode(el: HtmlElement) -> tuple[str, str]:
    tag = el.tag.lower()
    input_type = (el.get("type") or "").lower()
    role = (el.get("role") or "").lower()

    if role in {"button", "link"} and tag not in {"button", "a"}:
        return "Button" if role == "button" else "Link", "UserAction"
    if tag == "button":
        return "Button", "UserAction"
    if tag == "a":
        return "Link", "UserAction"
    if tag == "select":
        return "Dropdown", "Input"
    if tag == "textarea":
        return "Textarea", "Input"
    if tag == "img":
        return "Image", "Output"
    if tag == "label":
        return "Label", "Output"
    if tag == "table":
        return "Table", "Output"
    if tag == "th":
        return "Column Header", "Output"
    if tag == "fieldset":
        return "Section", "Output"
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return "Heading", "Output"
    if tag == "input":
        if input_type in {"submit", "button", "reset"}:
            return "Button", "UserAction"
        if input_type == "checkbox":
            return "Checkbox", "Input"
        if input_type == "radio":
            return "Radio", "Input"
        if input_type == "password":
            return "Password", "Input"
        if input_type == "email":
            return "Email", "Input"
        return "Text", "Input"
    return "Unknown", "Unknown"


def _derive_name(el: HtmlElement, root: HtmlElement, fallback_type: str) -> str:
    # 1) Try explicit labels (for attribute)
    element_id = el.get("id")
    name = ""
    if element_id:
        labels = root.xpath(f"//label[@for={_xpath_literal(element_id)}]")
        if labels:
            name = _normalize_space_text(" ".join(labels[0].itertext()))

    # 2) Try implicit labels (nested)
    if not name:
        parent_label = el.xpath("ancestor::label[1]")
        if parent_label:
            name = _normalize_space_text(" ".join(parent_label[0].itertext()))

    # 3) Proximity Search (Preceding sibling text)
    if not name and el.tag.lower() in {"input", "select", "textarea"}:
        # Look for text nodes in preceding siblings
        preceding = el.xpath("preceding-sibling::text()[1]")
        if preceding:
            text = _normalize_space_text(str(preceding[0]))
            if text and len(text) > 1:
                name = text

    # 4) Semantic attributes
    if not name:
        for attr in ["aria-label", "placeholder", "title", "alt", "name", "id", "value"]:
            val = (el.get(attr) or "").strip()
            if val:
                name = val
                break

    # 5) Icon/Tooltip Support (nested img alt)
    if not name:
        nested_imgs = el.xpath(".//img[@alt or @title]")
        if nested_imgs:
            name = nested_imgs[0].get("alt") or nested_imgs[0].get("title")

    # 6) Inner text (last resort)
    if not name:
        name = _normalize_space_text(" ".join(el.itertext()))

    # Clean the base name
    name = _clean_name(name) if name else f"Unnamed {fallback_type}"
    
    # 7) Table-Aware Context
    table_context = ""
    td_ancestors = el.xpath("ancestor::td[1]")
    if td_ancestors:
        td = td_ancestors[0]
        table = td.xpath("ancestor::table[1]")
        if table:
            # Try to find column index
            cell_index = len(td.xpath("preceding-sibling::td"))
            # Look for header (th) at that index
            headers = table[0].xpath(f".//th[{cell_index + 1}]")
            if headers:
                col_name = _clean_name(_normalize_space_text(" ".join(headers[0].itertext())))
                if col_name:
                    table_context = col_name

    # 8) Hierarchical Naming: Prepend section context
    section_title = ""
    for ancestor in el.iterancestors():
        if ancestor.tag == "fieldset":
            legends = ancestor.xpath("./legend")
            if legends:
                section_title = _clean_name(_normalize_space_text(" ".join(legends[0].itertext())))
                break
        
        cls = (ancestor.get("class") or "").lower()
        if any(token in cls for token in ["subtitle", "header", "heading", "title"]):
            text = _normalize_space_text(" ".join(ancestor.itertext()))
            if text and len(text) < 100:
                section_title = _clean_name(text)
                break

    # Final Assembly
    parts = []
    if section_title:
        parts.append(section_title)
    if table_context:
        parts.append(table_context)
    if name and name not in parts:
        parts.append(name)
    
    return " - ".join(parts) if parts else f"Unnamed {fallback_type}"


def _select_count(root: HtmlElement, strategy: str, value: str) -> int:
    try:
        if strategy.startswith("xpath:"):
            return len(root.xpath(value))
        selector = CSSSelector(value)
        return len(selector(root))
    except Exception:
        return 0


def _add_with_attribute(raw: list[RawCandidate], tag: str, attr: str, value: str, label: str, base: int, stable: bool) -> None:
    if not value:
        return
    quoted = _xpath_literal(value)
    if attr == "id":
        escaped_id = _escape_css_id(value)
        raw.append(
            RawCandidate(
                strategy=f"css:{label}",
                value=f"#{escaped_id}",
                base_score=base,
                intended_stable=stable,
                rationale=f"Uses unique-looking {attr} attribute (escaped).",
            )
        )
    elif SAFE_CSS_TOKEN.match(value):
        raw.append(
            RawCandidate(
                strategy=f"css:{label}",
                value=f"{tag}[{attr}={value}]",
                base_score=base - 2,
                intended_stable=stable,
                rationale=f"Uses {attr} attribute match.",
            )
        )
    else:
        css_value = _css_attr_literal(value)
        raw.append(
            RawCandidate(
                strategy=f"css:{label}",
                value=f"{tag}[{attr}={css_value}]",
                base_score=base - 2,
                intended_stable=stable,
                rationale=f"Uses {attr} attribute match (quoted).",
            )
        )

    raw.append(
        RawCandidate(
            strategy=f"xpath:{label}",
            value=f"//{tag}[@{attr}={quoted}]",
            base_score=base,
            intended_stable=stable,
            rationale=f"XPath attribute match on {attr}.",
        )
    )


def _build_locators(el: HtmlElement, root: HtmlElement, tree: etree._ElementTree) -> list[Locator]:
    tag = el.tag.lower()
    raw: list[RawCandidate] = []

    # 1) Test attributes are highest-priority by design.
    for key in TEST_ID_KEYS:
        value = (el.get(key) or "").strip()
        if value:
            _add_with_attribute(raw, tag, key, value, "test_attr", 100, True)

    # 2) Accessibility + semantic identifiers.
    aria_label = (el.get("aria-label") or "").strip()
    if aria_label:
        _add_with_attribute(raw, tag, "aria-label", aria_label, "aria_label", 92, True)

    role = (el.get("role") or "").strip()
    if role:
        role_css = _css_attr_literal(role)
        raw.append(
            RawCandidate(
                strategy="css:role",
                value=f"{tag}[role={role_css}]",
                base_score=74,
                intended_stable=True,
                rationale="Role-based locator is readable and semantic.",
            )
        )

    # 3) Stable ID and Name.
    element_id = (el.get("id") or "").strip()
    if element_id and not _is_dynamic_token(element_id):
        _add_with_attribute(raw, tag, "id", element_id, "id", 96, True)
    elif element_id:
        prefix = _stable_prefix(element_id)
        if prefix:
            raw.append(
                RawCandidate(
                    strategy="css:id_prefix",
                    value=f'{tag}[id^="{prefix}"]',
                    base_score=66,
                    intended_stable=False,
                    rationale="ID appears dynamic; using stable prefix fallback.",
                )
            )
            raw.append(
                RawCandidate(
                    strategy="xpath:id_prefix",
                    value=f"//{tag}[starts-with(@id, {_xpath_literal(prefix)})]",
                    base_score=68,
                    intended_stable=False,
                    rationale="ID appears dynamic; using XPath starts-with fallback.",
                )
            )

    element_name = (el.get("name") or "").strip()
    if element_name and not _is_dynamic_token(element_name):
        _add_with_attribute(raw, tag, "name", element_name, "name", 88, True)
    elif element_name:
        prefix = _stable_prefix(element_name)
        if prefix:
            raw.append(
                RawCandidate(
                    strategy="css:name_prefix",
                    value=f'{tag}[name^="{prefix}"]',
                    base_score=64,
                    intended_stable=False,
                    rationale="Name appears dynamic; using stable prefix fallback.",
                )
            )

    # 4) Useful attribute combos.
    input_type = (el.get("type") or "").strip()
    if input_type:
        input_type_css = _css_attr_literal(input_type)
        raw.append(
            RawCandidate(
                strategy="css:type",
                value=f"{tag}[type={input_type_css}]",
                base_score=58,
                intended_stable=False,
                rationale="Type alone is often broad, but useful as a fallback.",
            )
        )
        raw.append(
            RawCandidate(
                strategy="xpath:type",
                value=f"//{tag}[@type={_xpath_literal(input_type)}]",
                base_score=58,
                intended_stable=False,
                rationale="XPath type fallback when semantic attributes are absent.",
            )
        )

    href = (el.get("href") or "").strip()
    if tag == "a" and href and href not in {"#", "javascript:void(0)", "javascript:;"}:
        # Exact href can be brittle at runtime (trailing slash, query params, env domain rewrites).
        # Keep it, but score it lower than resilient contains strategies.
        _add_with_attribute(raw, tag, "href", href, "href", 74, True)
        parsed = urlparse(href)
        path_part = (parsed.path or "").strip()
        if len(path_part) > 2:
            path_css = _css_attr_literal(path_part)
            raw.append(
                RawCandidate(
                    strategy="css:href_contains",
                    value=f"a[href*={path_css}]",
                    base_score=74,
                    intended_stable=False,
                    rationale="Href path-contains fallback for environment-specific domains.",
                )
            )
            raw.append(
                RawCandidate(
                    strategy="xpath:href_contains",
                    value=f"//a[contains(@href, {_xpath_literal(path_part)})]",
                    base_score=74,
                    intended_stable=False,
                    rationale="XPath href contains fallback for environment-specific domains.",
                )
            )
            normalized_path = path_part.strip("/")
            if normalized_path:
                norm_css = _css_attr_literal(normalized_path)
                raw.append(
                    RawCandidate(
                        strategy="css:href_contains_path",
                        value=f"a[href*={norm_css}]",
                        base_score=79,
                        intended_stable=True,
                        rationale="Path-only contains ignores trailing slash and domain differences.",
                    )
                )
                raw.append(
                    RawCandidate(
                        strategy="xpath:href_contains_path",
                        value=f"//a[contains(@href, {_xpath_literal(normalized_path)})]",
                        base_score=79,
                        intended_stable=True,
                        rationale="Path-only XPath contains ignores trailing slash and domain differences.",
                    )
                )

                slug = normalized_path.split("/")[-1]
                if len(slug) >= 6:
                    slug_css = _css_attr_literal(slug)
                    raw.append(
                        RawCandidate(
                            strategy="css:href_slug",
                            value=f"a[href*={slug_css}]",
                            base_score=76,
                            intended_stable=False,
                            rationale="Slug-level href contains fallback for rewritten URL structures.",
                        )
                    )
                    raw.append(
                        RawCandidate(
                            strategy="xpath:href_slug",
                            value=f"//a[contains(@href, {_xpath_literal(slug)})]",
                            base_score=76,
                            intended_stable=False,
                            rationale="Slug-level XPath contains fallback for rewritten URL structures.",
                        )
                    )

    placeholder = (el.get("placeholder") or "").strip()
    if placeholder and tag in {"input", "textarea"}:
        _add_with_attribute(raw, tag, "placeholder", placeholder, "placeholder", 78, True)

    # 5) Text and class-based fallbacks.
    text = _normalize_space_text(" ".join(el.itertext()))
    if text and tag in TEXT_TAGS:
        exact = text[:50]
        raw.append(
            RawCandidate(
                strategy="xpath:text",
                value=f"//{tag}[normalize-space(.)={_xpath_literal(exact)}]",
                base_score=76,
                intended_stable=False,
                rationale="Text-based locator helps when attributes are weak.",
            )
        )
        if len(text) > 20:
            partial = text[:20]
            raw.append(
                RawCandidate(
                    strategy="xpath:text_contains",
                    value=f"//{tag}[contains(normalize-space(.), {_xpath_literal(partial)})]",
                    base_score=70,
                    intended_stable=False,
                    rationale="Partial text match for long or dynamic labels.",
                )
            )

    # 5.5) Label-to-Input association (for inputs, selects, textareas).
    if tag in {"input", "textarea", "select"}:
        element_id = el.get("id")
        if element_id:
            labels = root.xpath(f"//label[@for={_xpath_literal(element_id)}]")
            if labels:
                label_text = _normalize_space_text(" ".join(labels[0].itertext()))
                if label_text and len(label_text) > 1:
                    raw.append(
                        RawCandidate(
                            strategy="xpath:label_for",
                            value=f"//input[@id=//label[normalize-space(.)={_xpath_literal(label_text)}]/@for]",
                            base_score=94,
                            intended_stable=True,
                            rationale="Locates input via its associated label's 'for' attribute.",
                        )
                    )
        
        parent_label = el.xpath("ancestor::label[1]")
        if parent_label:
            label_text = _normalize_space_text(" ".join(parent_label[0].itertext()))
            if label_text and len(label_text) > 1:
                raw.append(
                    RawCandidate(
                        strategy="xpath:label_nested",
                        value=f"//label[contains(normalize-space(.), {_xpath_literal(label_text.split()[0])})]//{tag}",
                        base_score=90,
                        intended_stable=True,
                        rationale="Locates input nested inside a descriptive label.",
                    )
                )

    class_attr = (el.get("class") or "").strip()
    if class_attr:
        first_class = class_attr.split()[0]
        if SAFE_CSS_TOKEN.match(first_class):
            raw.append(
                RawCandidate(
                    strategy="css:class",
                    value=f"{tag}.{first_class}",
                    base_score=62,
                    intended_stable=False,
                    rationale="Class-based locator may break with style refactors.",
                )
            )
        raw.append(
            RawCandidate(
                strategy="xpath:class",
                value=f"//{tag}[contains(@class,{_xpath_literal(first_class)})]",
                base_score=62,
                intended_stable=False,
                rationale="Class contains is a fallback for partially stable class names.",
            )
        )

    # 6) Relative anchor fallback from nearest stable ancestor.
    for ancestor in el.iterancestors():
        anc_tag = ancestor.tag.lower() if isinstance(ancestor.tag, str) else ""
        if not anc_tag:
            continue
        anc_id = (ancestor.get("id") or "").strip()
        if anc_id and not _is_dynamic_token(anc_id):
            raw.append(
                RawCandidate(
                    strategy="xpath:relative_ancestor",
                    value=f"//{anc_tag}[@id={_xpath_literal(anc_id)}]//{tag}",
                    base_score=54,
                    intended_stable=False,
                    rationale="Relative locator anchored by stable ancestor id.",
                )
            )
            break
        for key in TEST_ID_KEYS:
            val = (ancestor.get(key) or "").strip()
            if val:
                raw.append(
                    RawCandidate(
                        strategy="xpath:relative_ancestor",
                        value=f"//{anc_tag}[@{key}={_xpath_literal(val)}]//{tag}",
                        base_score=56,
                        intended_stable=False,
                        rationale=f"Relative locator anchored by ancestor {key}.",
                    )
                )
                break
        else:
            continue
        break

    # 7) Last resort absolute path.
    raw.append(
        RawCandidate(
            strategy="xpath:absolute",
            value=tree.getpath(el),
            base_score=40,
            intended_stable=False,
            rationale="Absolute XPath is fragile and should be last fallback.",
        )
    )

    dedup: dict[tuple[str, str], Locator] = {}
    for candidate in raw:
        if not candidate.value:
            continue
        unique = _select_count(root, candidate.strategy, candidate.value) == 1
        stable = candidate.intended_stable and unique
        risk = _risk_level(candidate.strategy, unique, stable)
        score = _score(candidate.base_score, unique, stable, risk)
        dedup[(candidate.strategy, candidate.value)] = Locator(
            strategy=candidate.strategy,
            value=candidate.value,
            unique=unique,
            stable=stable,
            score=score,
            risk_level=risk,
            rationale=candidate.rationale,
        )

    return sorted(dedup.values(), key=lambda item: item.score, reverse=True)


def _recommended_reason(locator: Locator) -> str:
    parts = [f"Top-ranked locator ({locator.strategy})."]
    if locator.unique:
        parts.append("Unique in DOM.")
    if locator.stable:
        parts.append("Stable.")
    return " ".join(parts)


def extract_from_html(html_content: str) -> dict:
    html_content = clean_mhtml_to_html(html_content)
    root = html.fromstring(html_content)
    tree = root.getroottree()

    title = root.xpath("//title/text()")
    page_name = title[0].strip() if title else "UI Locator Extraction"

    elements = []
    stable_count = 0

    for el in root.iter():
        if not _is_visible_candidate(el):
            continue
        tag = el.tag.lower()
        if tag not in INTERESTING_TAGS and el.get("role") not in {"button", "link"}:
            continue

        element_type, mode = _infer_type_mode(el)
        locators = _build_locators(el, root, tree)
        if not locators:
            continue

        recommended = locators[0]
        if recommended.stable:
            stable_count += 1

        element_name = _derive_name(el, root, element_type)
        absolute_xpath = tree.getpath(el)
        attrs = {
            key: value
            for key, value in (el.attrib or {}).items()
            if key in {"id", "name", "type", "role", "aria-label", "placeholder", "href", "data-testid", "data-test", "data-cy", "data-qa"}
        }

        elements.append(
            {
                "tag": tag,
                "element_name": element_name,
                "mode": mode,
                "element_type": element_type,
                "absolute_xpath": absolute_xpath,
                "attributes": attrs,
                "recommended_locator": {
                    "rank": 1,
                    "strategy": recommended.strategy,
                    "value": recommended.value,
                    "score": recommended.score,
                    "reason": _recommended_reason(recommended),
                },
                "locators": [
                    {
                        "rank": idx + 1,
                        "strategy": loc.strategy,
                        "value": loc.value,
                        "unique": loc.unique,
                        "score": loc.score,
                    }
                    for idx, loc in enumerate(locators)
                ],
            }
        )

    return {
        "page_name": page_name,
        "total_elements": len(elements),
        "stable_elements": stable_count,
        "elements": elements,
    }


def verify_locators_in_html(html_content: str, elements_data: list[dict]) -> dict:
    """
    Verifies a list of locators against HTML content using absolute XPath as ground truth.
    """
    html_content = clean_mhtml_to_html(html_content)
    root = html.fromstring(html_content)
    tree = root.getroottree()
    
    results = []
    
    for element in elements_data:
        ground_truth_xpath = element.get("absolute_xpath")
        verified_locators = []
        
        for loc in element.get("locators", []):
            strategy = loc.get("strategy", "")
            value = loc.get("value", "")
            
            matches = []
            try:
                if strategy.startswith("xpath:"):
                    matches = root.xpath(value)
                else:
                    selector = CSSSelector(value)
                    matches = selector(root)
            except Exception:
                pass
            
            status = "broken"
            match_count = len(matches)
            is_correct_element = False
            
            if match_count == 0:
                status = "broken"
            elif match_count > 1:
                status = "duplicate"
                # Check if the intended element is among the duplicates
                for match in matches:
                    if tree.getpath(match) == ground_truth_xpath:
                        is_correct_element = True
                        break
            else:
                # Exactly one match. Is it the right one?
                if tree.getpath(matches[0]) == ground_truth_xpath:
                    status = "correct"
                    is_correct_element = True
                else:
                    status = "misidentified"
            
            verified_locators.append({
                "rank": loc.get("rank"),
                "strategy": strategy,
                "value": value,
                "status": status,
                "match_count": match_count,
                "is_correct_element": is_correct_element
            })
            
        results.append({
            "element_name": element.get("element_name"),
            "absolute_xpath": ground_truth_xpath,
            "verification": verified_locators
        })
        
    return {
        "verified_elements": results,
        "summary": {
            "total_elements": len(elements_data),
            "correct_locators": sum(1 for el in results for v in el["verification"] if v["status"] == "correct"),
            "broken_locators": sum(1 for el in results for v in el["verification"] if v["status"] == "broken"),
            "duplicate_locators": sum(1 for el in results for v in el["verification"] if v["status"] == "duplicate"),
        }
    }
