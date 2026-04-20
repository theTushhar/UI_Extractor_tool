from lxml import html
from lxml.html import HtmlElement
from mhtml_parser import clean_mhtml_to_html

from core.models import Locator
from core.constants import INTERESTING_TAGS
from core.classifier import infer_type_mode
from core.naming import derive_name
from utils.html import select_count
from strategies.registry import StrategyRegistry

# Initialize registry once
registry = StrategyRegistry()

def _risk_level(strategy: str, unique: bool, stable: bool) -> str:
    if not unique: return "high"
    if "absolute" in strategy: return "high"
    if any(s in strategy for s in ["class", "text", "prefix"]): return "medium"
    return "low" if stable else "medium"

def _score(base: int, unique: bool, stable: bool, risk: str) -> int:
    score = int(base * 0.6) + (25 if unique else 0) + (15 if stable else 0)
    if risk == "medium": score -= 12
    elif risk == "high": score -= 24
    return max(1, min(100, score))

def _build_locators(el: HtmlElement, root: HtmlElement) -> list[Locator]:
    raw_candidates = registry.run_all(el, root)
    dedup: dict[tuple[str, str], Locator] = {}
    
    for candidate in raw_candidates:
        if not candidate.value: continue
        unique = select_count(root, candidate.strategy, candidate.value) == 1
        stable = candidate.intended_stable and unique
        risk = _risk_level(candidate.strategy, unique, stable)
        score = _score(candidate.base_score, unique, stable, risk)
        
        key = (candidate.strategy, candidate.value)
        if key not in dedup or score > dedup[key].score:
            dedup[key] = Locator(
                strategy=candidate.strategy,
                value=candidate.value,
                unique=unique,
                stable=stable,
                score=score,
                risk_level=risk,
                rationale=candidate.rationale,
            )

    return sorted(dedup.values(), key=lambda item: item.score, reverse=True)

def extract_from_html(html_content: str) -> dict:
    html_content = clean_mhtml_to_html(html_content)
    root = html.fromstring(html_content)
    tree = root.getroottree()

    title = root.xpath("//title/text()")
    page_name = title[0].strip() if title else "UI Locator Extraction"

    elements = []
    stable_count = 0

    for el in root.iter():
        if not isinstance(el.tag, str): continue
        tag = el.tag.lower()
        if tag in {"script", "style", "noscript", "meta", "link", "title"}: continue
        if el.get("hidden") is not None: continue
        
        if tag not in INTERESTING_TAGS and el.get("role") not in {"button", "link"}:
            continue

        element_type, mode = infer_type_mode(el)
        locators = _build_locators(el, root)
        if not locators: continue

        recommended = locators[0]
        if recommended.stable:
            stable_count += 1

        element_name = derive_name(el, root, element_type)
        absolute_xpath = tree.getpath(el)
        
        elements.append({
            "tag": tag,
            "element_name": element_name,
            "mode": mode,
            "element_type": element_type,
            "absolute_xpath": absolute_xpath,
            "attributes": dict(el.attrib),
            "recommended_locator": {
                "rank": 1,
                "strategy": recommended.strategy,
                "value": recommended.value,
                "score": recommended.score,
                "reason": recommended.rationale,
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
        })

    return {
        "page_name": page_name,
        "total_elements": len(elements),
        "stable_elements": stable_count,
        "elements": elements,
    }

def verify_locators_in_html(html_content: str, elements_data: list[dict]) -> dict:
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
                if strategy.startswith("xpath:"): matches = root.xpath(value)
                else: matches = html.CSSSelector(value)(root) # Simple fallback
            except: pass
            
            status = "broken"
            match_count = len(matches)
            is_correct = False
            if match_count == 1 and tree.getpath(matches[0]) == ground_truth_xpath:
                status = "correct"
                is_correct = True
            elif match_count > 1:
                status = "duplicate"
                for m in matches:
                    if tree.getpath(m) == ground_truth_xpath:
                        is_correct = True; break
            
            verified_locators.append({
                "rank": loc.get("rank"),
                "strategy": strategy,
                "value": value,
                "status": status,
                "match_count": match_count,
                "is_correct_element": is_correct
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
