from lxml.html import HtmlElement
from utils.text import normalize_space_text, clean_name
from utils.html import xpath_literal

def derive_name(el: HtmlElement, root: HtmlElement, fallback_type: str) -> str:
    # 1) Try explicit labels (for attribute)
    element_id = el.get("id")
    name = ""
    if element_id:
        labels = root.xpath(f"//label[@for={xpath_literal(element_id)}]")
        if labels:
            name = normalize_space_text(" ".join(labels[0].itertext()))

    # 2) Try implicit labels (nested)
    if not name:
        parent_label = el.xpath("ancestor::label[1]")
        if parent_label:
            name = normalize_space_text(" ".join(parent_label[0].itertext()))

    # 3) Proximity Search (Preceding sibling text)
    if not name and el.tag.lower() in {"input", "select", "textarea"}:
        # Look for text nodes in preceding siblings
        preceding = el.xpath("preceding-sibling::text()[1]")
        if preceding:
            text = normalize_space_text(str(preceding[0]))
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
        name = normalize_space_text(" ".join(el.itertext()))

    # Clean the base name
    name = clean_name(name) if name else f"Unnamed {fallback_type}"
    
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
                col_name = clean_name(normalize_space_text(" ".join(headers[0].itertext())))
                if col_name:
                    table_context = col_name

    # 8) Hierarchical Naming: Prepend section context
    section_title = ""
    for ancestor in el.iterancestors():
        if ancestor.tag == "fieldset":
            legends = ancestor.xpath("./legend")
            if legends:
                section_title = clean_name(normalize_space_text(" ".join(legends[0].itertext())))
                break
        
        cls = (ancestor.get("class") or "").lower()
        if any(token in cls for token in ["subtitle", "header", "heading", "title"]):
            text = normalize_space_text(" ".join(ancestor.itertext()))
            if text and len(text) < 100:
                section_title = clean_name(text)
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
