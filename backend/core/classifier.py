from lxml.html import HtmlElement

def infer_type_mode(el: HtmlElement) -> tuple[str, str]:
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
