import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse
from lxml import etree, html
from lxml.cssselect import CSSSelector
from lxml.html import HtmlElement


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
}

SAFE_CSS_TOKEN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
DYNAMIC_TOKEN_PATTERN = re.compile(r"(\d{3,}|[a-f0-9]{8,})$", re.I)
TEXT_TAGS = {"button", "a", "label", "h1", "h2", "h3", "h4", "h5", "h6"}
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


def _normalize_space_text(text: str) -> str:
    return " ".join(text.split())


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
    element_id = el.get("id")
    if element_id:
        labels = root.xpath(f"//label[@for={_xpath_literal(element_id)}]")
        if labels:
            label_text = _normalize_space_text(" ".join(labels[0].itertext()))
            if label_text:
                return label_text

    parent_label = el.xpath("ancestor::label[1]")
    if parent_label:
        nested = _normalize_space_text(" ".join(parent_label[0].itertext()))
        if nested:
            return nested

    for attr in ["aria-label", "placeholder", "title", "alt", "name", "id", "value"]:
        value = (el.get(attr) or "").strip()
        if value:
            return value

    text = _normalize_space_text(" ".join(el.itertext()))
    if text:
        return text[:80]
    return f"Unnamed {fallback_type}"


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
    if SAFE_CSS_TOKEN.match(value) and attr in {"id"}:
        raw.append(
            RawCandidate(
                strategy=f"css:{label}",
                value=f"#{value}",
                base_score=base,
                intended_stable=stable,
                rationale=f"Uses unique-looking {attr} attribute.",
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
                rationale=f"Uses {attr} attribute match.",
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
                "attributes": attrs,
                "recommended_locator": {
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
