import base64
import logging
import time
from playwright.sync_api import sync_playwright
from extractor import extract_from_html

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_session(self, url: str = "about:blank"):
        if self.browser:
            return {"status": "already_running"}
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False) 
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        self.page = self.context.new_page()
        if url != "about:blank":
            self.page.goto(url)
        return {"status": "started"}

    def capture_current_state(self):
        if not self.page:
            raise Exception("No active browser session. Start a session first.")

        self.page.bring_to_front()
        html_content = self.page.content()
        screenshot = self.page.screenshot(full_page=False)
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        extraction_results = extract_from_html(html_content)
        
        coordinates_script = """
        () => {
            const results = {};
            function getCanonicalXPath(element) {
                if (element.nodeType !== 1) return '';
                if (element.tagName.toLowerCase() === 'html') return '/html';
                let index = 1;
                let sibling = element.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === element.tagName) index++;
                    sibling = sibling.previousElementSibling;
                }
                return getCanonicalXPath(element.parentElement) + '/' + element.tagName.toLowerCase() + '[' + index + ']';
            }

            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            let node = walker.nextNode();
            while (node) {
                const rect = node.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    results[getCanonicalXPath(node)] = {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    };
                }
                node = walker.nextNode();
            }
            return results;
        }
        """
        coords_map = self.page.evaluate(coordinates_script)
        
        for element in extraction_results.get("elements", []):
            xpath = element.get("absolute_xpath")
            if xpath in coords_map:
                element["rect"] = coords_map[xpath]

        extraction_results["url"] = self.page.url
        extraction_results["screenshot"] = screenshot_b64
        extraction_results["html"] = html_content
        
        return extraction_results

    def highlight_element(self, selector_type: str, selector_value: str, internal_xpath: str = ""):
        if not self.page:
            raise Exception("No active browser session.")

        target = internal_xpath if internal_xpath else selector_value
        is_xpath = internal_xpath != "" or selector_type.startswith("xpath")

        highlight_script = """
        (args) => {
            const [target, isXpath] = args;
            let el;
            try {
                if (isXpath) {
                    el = document.evaluate(target, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                } else {
                    el = document.querySelector(target);
                }
            } catch(e) { return false; }

            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                let overlay = document.getElementById('ui-extractor-highlight');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'ui-extractor-highlight';
                    document.body.appendChild(overlay);
                }
                const rect = el.getBoundingClientRect();
                overlay.style.cssText = `
                    position: fixed; top: ${rect.top}px; left: ${rect.left}px;
                    width: ${rect.width}px; height: ${rect.height}px;
                    border: 4px solid #facc15; background: rgba(250, 204, 21, 0.2);
                    box-shadow: 0 0 20px 5px rgba(250, 204, 21, 0.5);
                    z-index: 9999999; pointer-events: none; border-radius: 4px;
                `;
                overlay.animate([{ opacity: 0.8 }, { opacity: 0.4 }, { opacity: 0.8 }], { duration: 1000, iterations: Infinity });
                setTimeout(() => { if (overlay.parentNode) overlay.remove(); }, 3000);
                return true;
            }
            return false;
        }
        """
        success = self.page.evaluate(highlight_script, [target, is_xpath])
        return {"status": "success" if success else "not_found"}

    def verify_session_locators(self, elements: list):
        if not self.page:
            raise Exception("No active browser session.")

        verify_script = """
        (elements) => {
            const results = [];
            for (const elData of elements) {
                const groundTruthXpath = elData.absolute_xpath;
                let targetElement = null;
                try {
                    targetElement = document.evaluate(groundTruthXpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                } catch (e) {}

                const updatedLocators = [];
                for (const loc of elData.locators) {
                    let matches = [];
                    let verifyValue = loc.internal_xpath || (loc.strategy.includes('xpath') ? loc.value : null);
                    let isCss = !verifyValue && loc.strategy.includes('css');
                    if (isCss) verifyValue = loc.value;

                    if (verifyValue) {
                        try {
                            if (isCss) {
                                matches = Array.from(document.querySelectorAll(verifyValue));
                            } else {
                                const iterator = document.evaluate(verifyValue, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                                for (let i = 0; i < iterator.snapshotLength; i++) matches.push(iterator.snapshotItem(i));
                            }
                        } catch (e) {}
                    }

                    const isCorrect = targetElement && matches.includes(targetElement);
                    const isUnique = matches.length === 1;
                    
                    updatedLocators.push({
                        ...loc,
                        unique: isUnique,
                        status: isCorrect ? 'correct' : (matches.length > 0 ? 'shifted' : 'broken'),
                        actual_matches: matches.length
                    });
                }

                // Always keep the element, but update its locators
                const validLocs = updatedLocators.filter(l => l.status === 'correct');
                const bestLoc = validLocs.length > 0 
                    ? validLocs.sort((a, b) => b.score - a.score)[0]
                    : updatedLocators.sort((a, b) => b.score - a.score)[0];

                results.push({
                    ...elData,
                    locators: updatedLocators,
                    recommended_locator: { 
                        ...bestLoc, 
                        rank: 1, 
                        reason: validLocs.length > 0 ? "Verified live" : "Verification failed - showing best guess" 
                    }
                });
            }
            return results;
        }
        """
        cleaned_elements = self.page.evaluate(verify_script, elements)
        return {
            "elements": cleaned_elements,
            "total_elements": len(cleaned_elements),
            "stable_elements": sum(1 for e in cleaned_elements if e['recommended_locator'].get('status') == 'correct' and e['recommended_locator'].get('score', 0) >= 80)
        }

    def stop_session(self):
        if self.page: self.page.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = self.browser = self.context = self.playwright = None
        return {"status": "stopped"}

browser_manager = BrowserManager()

def capture_page_data_sync(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            html_content = page.content()
            screenshot = page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            res = extract_from_html(html_content)
            res["url"] = url
            res["screenshot"] = screenshot_b64
            res["html"] = html_content
            return res
        finally:
            browser.close()
