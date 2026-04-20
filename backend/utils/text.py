import re

def normalize_space_text(text: str) -> str:
    return " ".join(text.split())

def clean_name(name: str) -> str:
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
