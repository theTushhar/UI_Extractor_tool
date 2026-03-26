import logging

from playwright.sync_api import Page


logger = logging.getLogger(__name__)


def validate_locators(page: Page, locators: list) -> list:
    """
    Validates a list of locators against the current page using Playwright.
    """
    logger.info("Validating %s locators", len(locators))
    for index, item in enumerate(locators, start=1):
        css_selector = item.get("cssSelector")
        element_name = item.get("elementName", f"locator_{index}")
        logger.debug(
            "Validating locator %s | element=%s | css=%s",
            index,
            element_name,
            css_selector,
        )
        if not css_selector:
            item["status"] = "MISSING_CSS_SELECTOR"
            logger.warning("Locator %s missing cssSelector", index)
            continue

        try:
            locator_instance = page.locator(css_selector)
            count = locator_instance.count()
            logger.debug("Locator %s matched %s elements", index, count)

            if count == 1:
                item["status"] = "VERIFIED"
            elif count > 1:
                item["status"] = "AMBIGUOUS"
            else:
                item["status"] = "BROKEN"

            logger.info(
                "Locator %s validation result | element=%s | status=%s",
                index,
                element_name,
                item["status"],
            )
        except Exception as exc:
            item["status"] = f"INVALID_SYNTAX: {exc}"
            logger.exception("Locator %s validation crashed", index)
    return locators
