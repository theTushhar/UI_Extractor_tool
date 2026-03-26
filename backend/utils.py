import logging

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def get_clean_dom(html_content: str) -> str:
    """
    Cleans the HTML content by removing script, style, svg, path, link, meta, noscript tags
    and whitelisting attributes.
    """
    logger.debug("Cleaning DOM with input length: %s", len(html_content))
    soup = BeautifulSoup(html_content, "html.parser")

    unwanted_tags = ["script", "style", "svg", "path", "link", "meta", "noscript"]
    removed_tag_count = 0
    for tag in unwanted_tags:
        found = soup.find_all(tag)
        removed_tag_count += len(found)
        for element in found:
            element.decompose()

    whitelisted_attrs = [
        "id",
        "class",
        "name",
        "type",
        "placeholder",
        "aria-label",
        "role",
        "data-testid",
        "data-test",
        "data-cy",
    ]
    removed_attr_count = 0
    for tag in soup.find_all(True):
        attrs_to_remove = [attr for attr in tag.attrs if attr not in whitelisted_attrs]
        removed_attr_count += len(attrs_to_remove)
        for attr in attrs_to_remove:
            del tag.attrs[attr]

    body_content = soup.body
    cleaned = str(body_content.prettify()) if body_content else ""
    logger.debug(
        "DOM cleaned | removed_tags=%s | removed_attrs=%s | output_length=%s",
        removed_tag_count,
        removed_attr_count,
        len(cleaned),
    )
    return cleaned
