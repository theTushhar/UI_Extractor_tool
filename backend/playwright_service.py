import asyncio
import base64
from playwright.async_api import async_playwright
from extractor import extract_from_html
import logging

logger = logging.getLogger(__name__)

async def capture_page_data(url: str):
    """
    Navigates to a URL, captures HTML and a screenshot,
    then runs the extraction logic.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Navigating to {url}...")
            # Wait until network is idle or 30s timeout
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Optional: Scroll to bottom to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1) # Wait for any lazy content
            
            html_content = await page.content()
            screenshot = await page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Extract locators using our existing logic
            extraction_results = extract_from_html(html_content)
            
            # Add metadata
            extraction_results["url"] = url
            extraction_results["screenshot"] = screenshot_b64
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"Error capturing page {url}: {str(e)}")
            raise e
        finally:
            await browser.close()

async def validate_locator_live(url: str, selector_type: str, selector_value: str):
    """
    Validates a locator on a live page.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Handle different selector types
            # If it's a 'playwright:get_by_role' type, we'd need a parser
            # For now, let's support standard CSS/XPath
            count = 0
            if "xpath" in selector_type:
                count = await page.locator(f"xpath={selector_value}").count()
            elif "css" in selector_type:
                count = await page.locator(f"css={selector_value}").count()
            else:
                # Fallback to general locator
                count = await page.locator(selector_value).count()
                
            return {"status": "ok", "match_count": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            await browser.close()
