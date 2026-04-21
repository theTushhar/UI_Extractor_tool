import base64
from playwright.sync_api import sync_playwright
from extractor import extract_from_html
import logging
import time

logger = logging.getLogger(__name__)

def capture_page_data_sync(url: str):
    """
    Synchronous version of page capture.
    More stable on Windows when integrated with FastAPI.
    """
    with sync_playwright() as p:
        # Use chromium
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            logger.info(f"Navigating to {url} (Sync mode)...")
            # Navigate and wait
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            html_content = page.content()
            screenshot = page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Extract locators
            extraction_results = extract_from_html(html_content)
            
            # Add metadata
            extraction_results["url"] = url
            extraction_results["screenshot"] = screenshot_b64
            extraction_results["html"] = html_content
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"Error capturing page {url}: {str(e)}")
            raise e
        finally:
            browser.close()

def validate_locator_live_sync(url: str, selector_type: str, selector_value: str):
    """
    Synchronous locator validation.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            
            count = 0
            if "xpath" in selector_type:
                count = page.locator(f"xpath={selector_value}").count()
            elif "css" in selector_type:
                count = page.locator(f"css={selector_value}").count()
            else:
                count = page.locator(selector_value).count()
                
            return {"status": "ok", "match_count": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            browser.close()
