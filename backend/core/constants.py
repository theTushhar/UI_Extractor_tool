import re

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
